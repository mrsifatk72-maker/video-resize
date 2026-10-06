# Dr. Tanim Ahmed — Portfolio Website

A static, single-page personal website for **Dr. Tanim Ahmed, BDS (DU)**: Dental Surgeon, Clinical Practitioner and Dental Educator.

It is plain HTML, CSS and JavaScript, with no build step and no dependencies.

```
tanim-portfolio/
├── index.html          # all page content and SEO metadata
├── assets/css/styles.css
├── assets/js/main.js   # nav, reveals, count-up, timeline, expertise tabs, gallery lightbox
└── assets/img/         # optimized WebP photos + og-image.jpg
```

## Preview locally

```bash
cd tanim-portfolio
python3 -m http.server 8000   # then open http://localhost:8000
```

## Publish

Upload the `tanim-portfolio` folder to any static host, such as Netlify (drag and drop), Vercel, GitHub Pages or cPanel hosting.

**Before going live:** in `index.html`, replace `https://www.example.com/` (the canonical and `og:url` tags) with the real domain.

## Editing content

- **Text:** every section is labelled with a `<!-- ===== SECTION ===== -->` comment in `index.html`.
- **Gallery:** each photo is one `<li class="g" data-cat="…">` block. `data-cat` is one of `endo`, `resto`, `surgery` or `practice`. `data-full` is the large image the lightbox opens.
- **Contact:** search for `8801785078724` and `ahmedtanim009@gmail.com`.
