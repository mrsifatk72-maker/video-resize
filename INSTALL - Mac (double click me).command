#!/bin/bash
# ============================================================
#  VIDEO PROCESSOR — Auto Installer & Launcher
#  Dr. M R Sifat | mediversebd.com
#  Just double-click this file — it does everything for you.
# ============================================================

cd "$(dirname "$0")"
clear

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   🎬 Video Processor — Auto Setup               ║"
echo "  ║   mediversebd.com                               ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "  This will install everything needed and launch the app."
echo "  You only need to do this once."
echo ""

# ── Step 1: Xcode Command Line Tools ────────────────────────
if ! xcode-select -p &>/dev/null; then
  echo "  [1/3] Installing Xcode tools (required by Mac)..."
  xcode-select --install
  echo ""
  echo "  ⚠️  A popup appeared asking to install Xcode tools."
  echo "  Click 'Install' in that popup, wait for it to finish,"
  echo "  then double-click this file again."
  echo ""
  read -p "  Press Enter to close..."
  exit 0
fi
echo "  [1/3] ✅ Xcode tools: OK"

# ── Step 2: Homebrew ─────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "  [2/3] Installing Homebrew (Mac package manager)..."
  echo "        This may ask for your Mac password."
  echo ""
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # Add brew to PATH for Apple Silicon and Intel Macs
  if [ -f /opt/homebrew/bin/brew ]; then
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [ -f /usr/local/bin/brew ]; then
    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
    eval "$(/usr/local/bin/brew shellenv)"
  fi
else
  eval "$(/opt/homebrew/bin/brew shellenv 2>/dev/null || /usr/local/bin/brew shellenv 2>/dev/null)"
fi
echo "  [2/3] ✅ Homebrew: OK"

# ── Step 3: Python ───────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "  [3/4] Installing Python..."
  brew install python
fi
echo "  [3/4] ✅ Python: $(python3 --version)"

# ── Step 4: FFmpeg ───────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
  echo "  [4/4] Installing FFmpeg (video engine)..."
  echo "        This may take 5-10 minutes. Please wait..."
  brew install ffmpeg
fi
echo "  [4/4] ✅ FFmpeg: OK"

# ── Launch ───────────────────────────────────────────────────
echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║   ✅ All set! Launching the app...              ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""
echo "  Your browser will open in a moment."
echo "  Keep this window open while using the app."
echo "  Press Ctrl+C here to stop the app."
echo ""

python3 "$(dirname "$0")/video_processor_app.py"
