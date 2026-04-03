#!/usr/bin/env python3
"""
VIDEO PROCESSOR — Dr. M R Sifat | mediversebd.com
Compress · Convert · Extract Audio
Run: python3 video_processor_app.py
"""

import http.server
import socketserver
import json
import os
import re
import subprocess
import threading
import webbrowser
import tempfile
import shutil
import urllib.parse
import sys
import platform
import time
from pathlib import Path

PORT = 8765

def get_output_dir():
    home = Path.home()
    out = home / "Desktop" / "VideoProcessor_Output"
    out.mkdir(parents=True, exist_ok=True)
    return str(out)

UPLOAD_DIR = tempfile.mkdtemp(prefix="vidproc_upload_")

# Global job state for progress streaming
job_state = {
    'running': False,
    'log': [],
    'percent': 0,
    'status': 'idle',
    'files': [],
    'output_dir': ''
}

def get_video_duration(path):
    """Get video duration in seconds using ffprobe."""
    try:
        r = subprocess.run(
            ['ffprobe','-v','error','-show_entries','format=duration',
             '-of','default=noprint_wrappers=1:nokey=1', path],
            capture_output=True, text=True, timeout=30
        )
        return float(r.stdout.strip())
    except:
        return 0

def run_ffmpeg_with_progress(cmd, label, duration_secs, job_state, step_start, step_end):
    """Run FFmpeg and parse progress from stderr."""
    job_state['log'].append(f"▶ {label}")
    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        time_pattern = re.compile(r'time=(\d+):(\d+):([\d.]+)')
        for line in proc.stdout:
            line = line.strip()
            m = time_pattern.search(line)
            if m and duration_secs > 0:
                h, mn, s = int(m.group(1)), int(m.group(2)), float(m.group(3))
                elapsed = h * 3600 + mn * 60 + s
                pct = min(elapsed / duration_secs, 1.0)
                job_state['percent'] = int(step_start + pct * (step_end - step_start))
        proc.wait()
        ok = proc.returncode == 0
        job_state['log'].append("  ✓ Done" if ok else f"  ✗ Failed (code {proc.returncode})")
        return ok
    except Exception as e:
        job_state['log'].append(f"  ✗ Exception: {e}")
        return False

def process_video_job(inp, qual, vfmts, afmts):
    """Run the full processing job in a background thread."""
    global job_state
    job_state.update({'running': True, 'log': [], 'percent': 0, 'status': 'running', 'files': []})

    outdir = get_output_dir()
    job_state['output_dir'] = outdir
    base = os.path.splitext(os.path.basename(inp))[0]
    crf  = {'high': 18, 'medium': 23, 'low': 28}.get(qual, 23)
    files = []

    duration = get_video_duration(inp)
    job_state['log'].append(f"📹 Duration: {int(duration//60)}m {int(duration%60)}s")

    # Count total tasks for step allocation
    total_tasks = 1 + len(vfmts) + len(afmts)
    step = 90 / total_tasks
    current_step = 0

    def add(p):
        if os.path.isfile(p):
            sz = os.path.getsize(p)
            files.append({'name': os.path.basename(p), 'path': p,
                          'size': f"{sz/1048576:.1f} MB" if sz >= 1048576 else f"{sz/1024:.0f} KB"})

    # 1. Compress
    out = os.path.join(outdir, f"{base}_compressed.mp4")
    cmd = ['ffmpeg','-y','-i',inp,'-c:v','libx264','-preset','medium',
           '-crf',str(crf),'-c:a','aac','-b:a','128k','-movflags','+faststart',
           '-progress','pipe:1','-nostats', out]
    if run_ffmpeg_with_progress(cmd, f"Compressing ({qual})", duration, job_state, current_step, current_step + step):
        add(out)
    current_step += step

    # 2. Video conversions
    vmap = {
        'mp4' :['-c:v','libx264','-crf','18','-c:a','aac','-movflags','+faststart'],
        'mkv' :['-c:v','libx264','-crf','18','-c:a','aac'],
        'avi' :['-c:v','libx264','-crf','18','-c:a','mp3'],
        'mov' :['-c:v','libx264','-crf','18','-c:a','aac','-movflags','+faststart'],
        'webm':['-c:v','libvpx-vp9','-crf','18','-b:v','0','-c:a','libopus'],
        'flv' :['-c:v','libx264','-crf','18','-c:a','aac'],
        'wmv' :['-c:v','wmv2','-b:v','5M','-c:a','wmav2'],
    }
    for fmt in vfmts:
        out = os.path.join(outdir, f"{base}.{fmt}")
        cfg = vmap.get(fmt, ['-c:v','libx264','-crf','18','-c:a','aac'])
        cmd = ['ffmpeg','-y','-i',inp] + cfg + ['-progress','pipe:1','-nostats', out]
        if run_ffmpeg_with_progress(cmd, f"Converting → {fmt.upper()}", duration, job_state, current_step, current_step + step):
            add(out)
        current_step += step

    # 3. Audio
    amap = {
        'mp3' :['-c:a','libmp3lame','-b:a','192k'],
        'aac' :['-c:a','aac','-b:a','192k'],
        'wav' :['-c:a','pcm_s16le'],
        'ogg' :['-c:a','libvorbis','-b:a','192k'],
        'flac':['-c:a','flac'],
        'm4a' :['-c:a','aac','-b:a','192k'],
    }
    for fmt in afmts:
        out = os.path.join(outdir, f"{base}_audio.{fmt}")
        cfg = amap.get(fmt, ['-c:a','libmp3lame','-b:a','192k'])
        cmd = ['ffmpeg','-y','-i',inp,'-vn'] + cfg + ['-progress','pipe:1','-nostats', out]
        if run_ffmpeg_with_progress(cmd, f"Extracting audio → {fmt.upper()}", duration, job_state, current_step, current_step + step):
            add(out)
        current_step += step

    job_state.update({'running': False, 'percent': 100, 'status': 'done', 'files': files})

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Video Processor</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',system-ui,sans-serif;background:#0f172a;color:#e2e8f0;min-height:100vh}
.header{background:linear-gradient(135deg,#1e3a5f 0%,#0f172a 100%);border-bottom:2px solid #38bdf8;padding:20px 36px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px}
.header h1{font-size:22px;font-weight:800;color:#f8fafc}.header h1 span{color:#38bdf8}
.header p{color:#64748b;font-size:13px;margin-top:3px}
.badge{background:#064e3b;color:#34d399;padding:5px 14px;border-radius:20px;font-size:12px;font-weight:700;border:1px solid #065f46}
.container{max-width:860px;margin:0 auto;padding:28px 20px}
.drop-zone{border:2px dashed #334155;border-radius:14px;padding:52px 32px;text-align:center;cursor:pointer;transition:all 0.2s;background:#1e293b}
.drop-zone:hover,.drop-zone.over{border-color:#38bdf8;background:#162032}
.drop-icon{font-size:52px;margin-bottom:14px;display:block}
.drop-zone h2{font-size:19px;font-weight:700;color:#f1f5f9;margin-bottom:6px}
.drop-zone p{color:#64748b;font-size:14px}
.drop-hint{color:#38bdf8;font-size:13px;font-weight:600;margin-top:10px}
#fileInput{display:none}
.card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:24px;margin-top:20px}
.card-title{font-size:13px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:14px}
.file-row{display:flex;align-items:center;gap:14px;background:#0f172a;border-radius:10px;padding:14px 18px}
.file-icon{font-size:34px;flex-shrink:0}
.file-name{font-weight:700;color:#38bdf8;font-size:15px;word-break:break-all}
.file-meta{color:#64748b;font-size:13px;margin-top:3px}
.file-status{margin-left:auto;font-size:12px;font-weight:600;flex-shrink:0}
.status-ready{color:#34d399}.status-uploading{color:#fbbf24}.status-error{color:#f87171}
.upload-prog-wrap{margin-top:10px;background:#0f172a;border-radius:4px;height:6px;overflow:hidden;display:none}
.upload-prog-bar{height:100%;background:#38bdf8;border-radius:4px;width:0%;transition:width 0.2s}
.btn-group{display:flex;gap:10px;flex-wrap:wrap}
.q-btn{flex:1;min-width:120px;padding:12px 10px;border-radius:9px;border:1.5px solid #334155;background:#0f172a;color:#94a3b8;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s;text-align:center;line-height:1.4}
.q-btn:hover{border-color:#64748b;color:#e2e8f0}.q-btn.active{border-color:#38bdf8;background:#0c2233;color:#38bdf8}
.q-btn .q-label{font-size:15px;display:block;margin-bottom:2px}
.q-btn .q-desc{font-size:11px;color:#64748b;font-weight:400}.q-btn.active .q-desc{color:#7dd3fc}
.chip-grid{display:flex;flex-wrap:wrap;gap:8px}
.chip{padding:8px 16px;border-radius:20px;border:1.5px solid #334155;background:#0f172a;color:#94a3b8;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.15s}
.chip:hover{border-color:#64748b;color:#e2e8f0}.chip.active{border-color:#38bdf8;background:#0c2233;color:#38bdf8}
.chip.audio.active{border-color:#a78bfa;background:#1e1040;color:#a78bfa}
.process-btn{width:100%;padding:15px;border-radius:10px;background:linear-gradient(135deg,#0ea5e9,#6366f1);color:#fff;border:none;font-size:16px;font-weight:700;cursor:pointer;transition:all 0.2s;margin-top:20px}
.process-btn:hover{opacity:0.9;transform:translateY(-1px)}.process-btn:disabled{opacity:0.4;cursor:not-allowed;transform:none}
.progress-card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:22px;margin-top:20px;display:none}
.prog-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
.prog-label{font-size:14px;color:#94a3b8}
.prog-pct{font-size:20px;font-weight:700;color:#38bdf8}
.prog-track{background:#0f172a;border-radius:6px;height:14px;overflow:hidden}
.prog-fill{height:100%;background:linear-gradient(90deg,#38bdf8,#818cf8);border-radius:6px;width:0%;transition:width 0.6s ease}
.prog-task{font-size:13px;color:#64748b;margin-top:8px}
.prog-log{font-family:monospace;font-size:11px;color:#475569;max-height:120px;overflow-y:auto;margin-top:12px;background:#0a0f1a;border-radius:6px;padding:10px 12px;white-space:pre-wrap;line-height:1.6}
.results-card{background:#1e293b;border:1px solid #334155;border-radius:12px;padding:22px;margin-top:20px;display:none}
.results-card h3{font-size:16px;font-weight:700;color:#34d399;margin-bottom:14px}
.result-item{display:flex;align-items:center;justify-content:space-between;gap:12px;background:#0f172a;border-radius:9px;padding:13px 16px;margin-bottom:8px;border:1px solid #1e3a2a}
.ri-name{font-weight:600;font-size:14px;color:#f1f5f9}.ri-size{font-size:12px;color:#64748b;margin-top:2px}
.dl-btn{padding:7px 16px;border-radius:7px;background:#065f46;color:#6ee7b7;border:none;font-size:13px;font-weight:700;cursor:pointer;text-decoration:none;flex-shrink:0}
.dl-btn:hover{background:#047857}
.open-folder-btn{display:block;width:100%;padding:11px;border-radius:8px;background:#334155;color:#e2e8f0;border:none;font-size:14px;font-weight:600;cursor:pointer;margin-top:12px}
.open-folder-btn:hover{background:#475569}
.reset-btn{display:block;width:100%;padding:11px;border-radius:8px;background:transparent;color:#64748b;border:1px solid #334155;font-size:14px;font-weight:600;cursor:pointer;margin-top:8px}
.tip{font-size:12px;color:#475569;margin-top:8px;font-style:italic}
</style>
</head>
<body>
<div class="header">
  <div><h1>🎬 Video <span>Processor</span></h1><p>mediversebd.com &nbsp;·&nbsp; Compress · Convert · Extract Audio</p></div>
  <span class="badge">✅ 100% Local · No Internet Needed</span>
</div>
<div class="container">
  <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
    <span class="drop-icon">📁</span>
    <h2>Drop your video here</h2>
    <p>or click anywhere to browse files from your computer</p>
    <p class="drop-hint">MP4 · MKV · AVI · MOV · WebM · FLV · WMV · TS · 3GP</p>
  </div>
  <input type="file" id="fileInput" accept="video/*,.mkv,.avi,.mov,.webm,.flv,.wmv,.ts,.3gp,.mp4">

  <div id="controls" style="display:none">
    <div class="card">
      <div class="card-title">📄 Selected File</div>
      <div class="file-row">
        <span class="file-icon">🎬</span>
        <div style="flex:1;min-width:0">
          <div class="file-name" id="fileName">—</div>
          <div class="file-meta" id="fileMeta">—</div>
        </div>
        <span class="file-status" id="fileStatus"></span>
      </div>
      <div class="upload-prog-wrap" id="uploadProgWrap">
        <div class="upload-prog-bar" id="uploadProgBar"></div>
      </div>
    </div>
    <div class="card">
      <div class="card-title">🗜️ Compression Quality</div>
      <div class="btn-group">
        <button class="q-btn" data-q="high" onclick="selectQuality(this)"><span class="q-label">⭐ High</span><span class="q-desc">Best quality · ~35% smaller</span></button>
        <button class="q-btn active" data-q="medium" onclick="selectQuality(this)"><span class="q-label">✅ Medium</span><span class="q-desc">Recommended · ~55% smaller</span></button>
        <button class="q-btn" data-q="low" onclick="selectQuality(this)"><span class="q-label">🗜️ Low</span><span class="q-desc">Max compression · ~70% smaller</span></button>
      </div>
      <p class="tip">💡 "Medium" is ideal for online course videos — great quality at much smaller file size.</p>
    </div>
    <div class="card">
      <div class="card-title">🎥 Convert to Video Formats <span style="color:#475569;font-weight:400;font-size:11px">(optional)</span></div>
      <div class="chip-grid">
        <span class="chip" data-fmt="mp4" onclick="toggleChip(this,'video')">MP4</span>
        <span class="chip" data-fmt="mkv" onclick="toggleChip(this,'video')">MKV</span>
        <span class="chip" data-fmt="avi" onclick="toggleChip(this,'video')">AVI</span>
        <span class="chip" data-fmt="mov" onclick="toggleChip(this,'video')">MOV</span>
        <span class="chip" data-fmt="webm" onclick="toggleChip(this,'video')">WebM</span>
        <span class="chip" data-fmt="flv" onclick="toggleChip(this,'video')">FLV</span>
        <span class="chip" data-fmt="wmv" onclick="toggleChip(this,'video')">WMV</span>
      </div>
    </div>
    <div class="card">
      <div class="card-title">🎵 Extract Audio <span style="color:#475569;font-weight:400;font-size:11px">(optional)</span></div>
      <div class="chip-grid">
        <span class="chip audio" data-fmt="mp3" onclick="toggleChip(this,'audio')">MP3</span>
        <span class="chip audio" data-fmt="aac" onclick="toggleChip(this,'audio')">AAC</span>
        <span class="chip audio" data-fmt="wav" onclick="toggleChip(this,'audio')">WAV</span>
        <span class="chip audio" data-fmt="ogg" onclick="toggleChip(this,'audio')">OGG</span>
        <span class="chip audio" data-fmt="flac" onclick="toggleChip(this,'audio')">FLAC</span>
        <span class="chip audio" data-fmt="m4a" onclick="toggleChip(this,'audio')">M4A</span>
      </div>
    </div>
    <button class="process-btn" id="processBtn" onclick="processVideo()" disabled>🚀 Process Video</button>
  </div>

  <div class="progress-card" id="progressCard">
    <div class="prog-header">
      <div class="prog-label" id="progLabel">Processing...</div>
      <div class="prog-pct" id="progPct">0%</div>
    </div>
    <div class="prog-track"><div class="prog-fill" id="progFill"></div></div>
    <div class="prog-task" id="progTask"></div>
    <div class="prog-log" id="progLog"></div>
  </div>

  <div class="results-card" id="resultsCard">
    <h3>✅ Done! Your files are ready</h3>
    <div id="resultList"></div>
    <button class="open-folder-btn" onclick="openFolder()">📂 Open Output Folder on Desktop</button>
    <button class="reset-btn" onclick="resetAll()">🔄 Process Another Video</button>
  </div>
</div>

<script>
let uploadedPath = null, selectedQuality = 'medium', selectedVideo = [], selectedAudio = [];
let pollInterval = null;

const dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('over'));
dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('over'); handleFile(e.dataTransfer.files[0]); });
document.getElementById('fileInput').addEventListener('change', e => { if (e.target.files[0]) handleFile(e.target.files[0]); });

function handleFile(file) {
  if (!file) return;
  document.getElementById('controls').style.display = 'block';
  document.getElementById('resultsCard').style.display = 'none';
  document.getElementById('progressCard').style.display = 'none';
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileMeta').textContent = 'Size: ' + fmtSize(file.size) + ' — Uploading...';
  document.getElementById('fileStatus').className = 'file-status status-uploading';
  document.getElementById('fileStatus').textContent = '⏳ Uploading...';
  document.getElementById('processBtn').disabled = true;
  document.getElementById('uploadProgWrap').style.display = 'block';
  uploadedPath = null;

  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/upload');
  xhr.setRequestHeader('X-Filename', encodeURIComponent(file.name));
  xhr.upload.addEventListener('progress', e => {
    if (e.lengthComputable) {
      const pct = Math.round((e.loaded / e.total) * 100);
      document.getElementById('uploadProgBar').style.width = pct + '%';
      document.getElementById('fileMeta').textContent = 'Uploading ' + pct + '% of ' + fmtSize(file.size) + '...';
    }
  });
  xhr.addEventListener('load', () => {
    if (xhr.status === 200) {
      const d = JSON.parse(xhr.responseText);
      if (d.path) {
        uploadedPath = d.path;
        document.getElementById('fileStatus').className = 'file-status status-ready';
        document.getElementById('fileStatus').textContent = '✅ Ready';
        document.getElementById('fileMeta').textContent = fmtSize(file.size) + ' · Upload complete ✅';
        document.getElementById('uploadProgBar').style.width = '100%';
        document.getElementById('processBtn').disabled = false;
      }
    } else {
      document.getElementById('fileStatus').className = 'file-status status-error';
      document.getElementById('fileStatus').textContent = '❌ Upload failed';
    }
  });
  xhr.send(file);
}

function fmtSize(b) {
  if (b >= 1073741824) return (b/1073741824).toFixed(2) + ' GB';
  if (b >= 1048576) return (b/1048576).toFixed(1) + ' MB';
  return (b/1024).toFixed(0) + ' KB';
}

function selectQuality(btn) {
  document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active'); selectedQuality = btn.dataset.q;
}

function toggleChip(chip, type) {
  chip.classList.toggle('active');
  const f = chip.dataset.fmt;
  if (type === 'video') selectedVideo = selectedVideo.includes(f) ? selectedVideo.filter(x=>x!==f) : [...selectedVideo, f];
  else selectedAudio = selectedAudio.includes(f) ? selectedAudio.filter(x=>x!==f) : [...selectedAudio, f];
}

function processVideo() {
  if (!uploadedPath) { alert('Please wait for upload to complete.'); return; }
  document.getElementById('processBtn').disabled = true;
  document.getElementById('progressCard').style.display = 'block';
  document.getElementById('resultsCard').style.display = 'none';
  document.getElementById('progFill').style.width = '2%';
  document.getElementById('progPct').textContent = '0%';
  document.getElementById('progLabel').textContent = '⏳ Starting FFmpeg...';
  document.getElementById('progLog').textContent = '';

  fetch('/process', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ path: uploadedPath, quality: selectedQuality, video_formats: selectedVideo, audio_formats: selectedAudio })
  }).then(() => {});

  // Poll real progress every 2 seconds
  pollInterval = setInterval(pollProgress, 2000);
}

function pollProgress() {
  fetch('/progress')
    .then(r => r.json())
    .then(d => {
      const pct = d.percent || 0;
      document.getElementById('progFill').style.width = pct + '%';
      document.getElementById('progPct').textContent = pct + '%';

      const logs = d.log || [];
      const lastLog = logs[logs.length - 1] || '';
      document.getElementById('progLabel').textContent = d.status === 'done' ? '✅ All done!' : '⏳ Processing...';
      document.getElementById('progTask').textContent = lastLog;
      document.getElementById('progLog').textContent = logs.join('\\n');
      document.getElementById('progLog').scrollTop = 9999;

      if (d.status === 'done') {
        clearInterval(pollInterval);
        showResults(d.files, d.output_dir);
      }
    });
}

function showResults(files, outputDir) {
  const list = document.getElementById('resultList');
  list.innerHTML = '';
  if (!files || !files.length) {
    list.innerHTML = '<p style="color:#f87171;font-size:14px">No files generated. Check that FFmpeg is installed.</p>';
  } else {
    files.forEach(f => {
      list.innerHTML += '<div class="result-item"><div><div class="ri-name">' + f.name + '</div><div class="ri-size">' + f.size + '</div></div><a class="dl-btn" href="/download?path=' + encodeURIComponent(f.path) + '" download="' + f.name + '">⬇ Download</a></div>';
    });
  }
  document.getElementById('resultsCard').dataset.outdir = outputDir || '';
  document.getElementById('resultsCard').style.display = 'block';
}

function openFolder() {
  fetch('/open_folder', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({dir: document.getElementById('resultsCard').dataset.outdir}) });
}

function resetAll() {
  if (pollInterval) clearInterval(pollInterval);
  uploadedPath = null; selectedVideo = []; selectedAudio = [];
  document.getElementById('controls').style.display = 'none';
  document.getElementById('progressCard').style.display = 'none';
  document.getElementById('resultsCard').style.display = 'none';
  document.getElementById('fileInput').value = '';
  document.querySelectorAll('.chip.active').forEach(c => c.classList.remove('active'));
  document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('active'));
  document.querySelector('[data-q="medium"]').classList.add('active');
  selectedQuality = 'medium';
  document.getElementById('processBtn').disabled = false;
  document.getElementById('uploadProgBar').style.width = '0%';
  document.getElementById('uploadProgWrap').style.display = 'none';
}
</script>
</body>
</html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args): pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == '/':
            self._send(200, 'text/html', HTML.encode())
        elif parsed.path == '/progress':
            resp = {
                'running' : job_state['running'],
                'percent' : job_state['percent'],
                'status'  : job_state['status'],
                'log'     : job_state['log'][-20:],
                'files'   : job_state['files'],
                'output_dir': job_state['output_dir']
            }
            self._send(200, 'application/json', json.dumps(resp).encode())
        elif parsed.path == '/download':
            params = urllib.parse.parse_qs(parsed.query)
            fp = params.get('path', [None])[0]
            if fp and os.path.isfile(fp):
                with open(fp, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/octet-stream')
                self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(fp)}"')
                self.send_header('Content-Length', str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == '/upload':
            result = self._upload()
            self._send(200, 'application/json', json.dumps(result).encode())
        elif self.path == '/process':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            # Run in background thread so browser doesn't wait
            t = threading.Thread(target=process_video_job, args=(
                body.get('path'), body.get('quality','medium'),
                body.get('video_formats',[]), body.get('audio_formats',[])
            ), daemon=True)
            t.start()
            self._send(200, 'application/json', json.dumps({'status':'started'}).encode())
        elif self.path == '/open_folder':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            folder = body.get('dir','')
            if folder and os.path.isdir(folder):
                s = platform.system()
                if s == 'Windows': os.startfile(folder)
                elif s == 'Darwin': subprocess.Popen(['open', folder])
                else: subprocess.Popen(['xdg-open', folder])
            self._send(200, 'application/json', json.dumps({'status':'ok'}).encode())
        else:
            self.send_error(404)

    def _send(self, code, ctype, data):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _upload(self):
        length = int(self.headers.get('Content-Length', 0))
        raw_name = self.headers.get('X-Filename', 'video.mp4')
        filename = urllib.parse.unquote(raw_name)
        safe = "".join(c for c in filename if c.isalnum() or c in '._- ')
        if not safe: safe = 'video.mp4'
        path = os.path.join(UPLOAD_DIR, safe)
        written = 0
        with open(path, 'wb') as f:
            while written < length:
                chunk = self.rfile.read(min(1024*1024, length - written))
                if not chunk: break
                f.write(chunk)
                written += len(chunk)
        return {'status': 'ok', 'path': path}


def check_ffmpeg():
    try:
        return subprocess.run(['ffmpeg','-version'], capture_output=True).returncode == 0
    except FileNotFoundError:
        return False


def main():
    outdir = get_output_dir()
    print()
    print("=" * 56)
    print("  🎬 VIDEO PROCESSOR — Dr. Sifat | mediversebd.com")
    print("=" * 56)
    if not check_ffmpeg():
        print("\n  ❌ FFmpeg NOT found!\n")
        if platform.system() == "Darwin": print("  Run: brew install ffmpeg")
        input("  Press Enter to exit..."); sys.exit(1)
    print(f"  ✅ FFmpeg        : OK")
    print(f"  ✅ Python        : {sys.version.split()[0]}")
    print(f"  ✅ Output folder : {outdir}")
    print(f"  🌐 App URL       : http://localhost:{PORT}")
    print()
    print("  ► Browser opening automatically...")
    print("  ► Keep this window open. Press Ctrl+C to stop.")
    print("=" * 56 + "\n")
    threading.Thread(target=lambda: (__import__('time').sleep(1.2), webbrowser.open(f"http://localhost:{PORT}")), daemon=True).start()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n✅ Stopped.")
            shutil.rmtree(UPLOAD_DIR, ignore_errors=True)

if __name__ == '__main__':
    main()
