#!/usr/bin/env python3
"""
Static blog builder for hossamzaki.com — no dependencies, pure standard library.

Reads:   posts/posts.json  (metadata)  +  posts/<slug>.md  (content)
Writes:  writing.html      (the blog index)
         posts/<slug>.html (one static page per post)

Run it after adding or editing a post:

    python3 build.py

Then commit and push. That's it.
"""

import json, re, html, pathlib, datetime

ROOT = pathlib.Path(__file__).parent
POSTS = ROOT / "posts"

# ---------- tiny markdown -> HTML converter ----------
def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)',
                  lambda m: f'<a href="{html.escape(m.group(2), quote=True)}">{m.group(1)}</a>', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text

def md_to_html(md):
    blocks = re.split(r'\n\s*\n', md.strip())
    out = []
    for block in blocks:
        lines = block.split('\n')
        stripped = block.strip()
        if stripped == '---':
            out.append('<hr>')
        elif stripped.startswith('### '):
            out.append(f'<h3>{inline(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            out.append(f'<h2>{inline(stripped[3:])}</h2>')
        elif all(l.lstrip().startswith('>') for l in lines):
            inner = ' '.join(l.lstrip()[1:].strip() for l in lines)
            out.append(f'<blockquote><p>{inline(inner)}</p></blockquote>')
        elif all(re.match(r'^\s*[-*]\s+', l) for l in lines):
            bullet = re.compile(r'^\s*[-*]\s+')
            items = ''.join('<li>' + inline(bullet.sub('', l)) + '</li>' for l in lines)
            out.append(f'<ul>{items}</ul>')
        else:
            out.append(f'<p>{inline(" ".join(lines))}</p>')
    return '\n'.join(out)

def fmt_date(s):
    try:
        return datetime.date.fromisoformat(s).strftime('%B %-d, %Y')
    except Exception:
        return s

# ---------- shared chrome ----------
def header(active, prefix=''):
    def cls(name): return ' class="active"' if name == active else ''
    return f'''<header class="site">
  <div class="wrap">
    <a class="brand" href="{prefix}index.html">Hossam Zaki</a>
    <nav class="site-nav">
      <a href="{prefix}index.html"{cls('about')}>Home</a>
      <a href="{prefix}publications.html"{cls('publications')}>Publications</a>
      <a href="{prefix}projects.html"{cls('projects')}>Projects</a>
      <a href="{prefix}writing.html"{cls('writing')}>Writing</a>
      <a href="{prefix}now.html"{cls('now')}>Now</a>
    </nav>
  </div>
</header>'''

FOOTER = '''<footer class="site">
  <div class="wrap">
    <div class="row">
      <span>&copy; <span id="year"></span> Hossam Zaki</span>
      <span>
        <a href="mailto:hzaki23@gmail.com">Email</a> &middot;
        <a href="https://x.com/hossamzki">X</a> &middot;
        <a href="https://github.com/hossam-zaki">GitHub</a> &middot;
        <a href="https://www.linkedin.com/in/hossamzaki23">LinkedIn</a> &middot;
        <a href="https://scholar.google.com/citations?user=AaVVYHsAAAAJ&hl=en">Scholar</a>
      </span>
    </div>
  </div>
</footer>
<script>document.getElementById('year').textContent = new Date().getFullYear();</script>'''

SITE = 'https://hossamzaki.com'

def page(title, body, active, prefix='', description='', canon=''):
    desc = html.escape(description or 'Writing on AI, interventional radiology, and building in medicine, by Hossam Zaki.', quote=True)
    url = f'{SITE}/{canon}' if canon else SITE + '/'
    og_image = f'{SITE}/assets/og-image.png'
    t = html.escape(title, quote=True)
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml">
<meta property="og:site_name" content="Hossam Zaki">
<meta property="og:type" content="article">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{og_image}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@hossamzki">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_image}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
{header(active, prefix)}
<main>
  <div class="wrap">
{body}
  </div>
</main>
{FOOTER}
</body>
</html>
'''

# ---------- build ----------
def main():
    posts = json.loads((POSTS / 'posts.json').read_text())
    posts.sort(key=lambda p: p['date'], reverse=True)  # newest first

    # individual post pages
    for p in posts:
        md = (POSTS / f"{p['slug']}.md").read_text()
        body = f'''    <p><a href="../writing.html">&larr; All writing</a></p>
    <article class="post">
      <h1>{html.escape(p['title'])}</h1>
      <div class="post-meta">{fmt_date(p['date'])}</div>
{md_to_html(md)}
    </article>'''
        out = page(f"{p['title']} — Hossam Zaki", body, 'writing', prefix='../',
                   description=p.get('excerpt', ''), canon=f"posts/{p['slug']}.html")
        (POSTS / f"{p['slug']}.html").write_text(out)

    # blog index
    items = '\n'.join(f'''      <li>
        <div class="date">{fmt_date(p['date'])}</div>
        <a class="post-title" href="posts/{p['slug']}.html">{html.escape(p['title'])}</a>
        {f'<div class="excerpt">{html.escape(p.get("excerpt",""))}</div>' if p.get('excerpt') else ''}
      </li>''' for p in posts)
    body = f'''    <section>
      <h1>Writing</h1>
      <p class="subtle">Notes on AI, interventional radiology, and building in medicine.
      Longer essays go out through <em>The Interventionist</em>.</p>
    </section>
    <section>
      <ul class="post-list">
{items}
      </ul>
    </section>'''
    (ROOT / 'writing.html').write_text(page(
        'Writing — Hossam Zaki', body, 'writing',
        description='Notes on AI, interventional radiology, and building in medicine.',
        canon='writing.html'))

    print(f"Built {len(posts)} posts + writing.html")

if __name__ == '__main__':
    main()
