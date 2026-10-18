"""Build a portable static notebook from Markdown, Word, and PDF documents."""
from pathlib import Path
from html import escape, unescape
from html.parser import HTMLParser
from urllib.parse import quote, unquote, urlsplit
import hashlib
import json
import re
import shutil
import sys
import bleach
import mammoth
import markdown

ROOT = Path(__file__).resolve().parent
RESERVED = {'assets', 'tests', 'images', 'dist', 'work', 'outputs', '__pycache__', 'node_modules', 'rough'}
TYPES = {'.md', '.docx', '.pdf'}

def natural_key(value):
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r'(\d+)', str(value))]

def discover_folders():
    return sorted((p.name for p in ROOT.iterdir() if p.is_dir() and not p.is_symlink()
                   and not p.name.startswith('.') and p.name not in RESERVED), key=natural_key)

def visible_file(path):
    return path.is_file() and not any(part.startswith('.') for part in path.relative_to(ROOT).parts) and not any(p.is_symlink() for p in [path, *path.parents])

def page_id(relative):
    return hashlib.sha256(relative.as_posix().encode()).hexdigest()[:20]

def clean(body):
    return bleach.clean(body, tags=set(bleach.sanitizer.ALLOWED_TAGS) | {
        'p','h1','h2','h3','h4','h5','h6','pre','hr','br','img','table','thead',
        'tbody','tr','th','td','del','sup','sub','div','span','details','summary'},
        attributes={'a':['href','title','id'], 'img':['src','alt','title','width','height'],
                    'code':['class'], 'th':['align'], 'td':['align'],
                    'h1':['id'], 'h2':['id'], 'h3':['id'], 'h4':['id'], 'h5':['id'], 'h6':['id']},
        protocols=['http','https','mailto','data'], strip=True)

class LocalLinks(HTMLParser):
    def __init__(self, source, known):
        super().__init__(convert_charrefs=False)
        self.source, self.known, self.parts = source, known, []
    def handle_starttag(self, tag, attrs):
        result = []
        for key, value in attrs:
            if key in ('href','src') and value:
                parsed = urlsplit(value)
                if not parsed.scheme and not parsed.netloc and parsed.path:
                    # Resolve against the original file's folder, then enforce containment.
                    target = ((ROOT / unquote(parsed.path).lstrip('/')) if parsed.path.startswith('/') else (self.source.parent / unquote(parsed.path))).resolve()
                    content = ROOT.resolve()
                    try:
                        rel = target.relative_to(content)
                        value = (self.known.get(rel.as_posix()) if key == 'href' else None) or '../files/' + quote(rel.as_posix())
                        if parsed.query: value += '?' + parsed.query
                        if parsed.fragment: value += '#' + parsed.fragment
                    except ValueError:
                        value = '#'
            result.append(' ' + key + '="' + escape(value or '', quote=True) + '"')
        self.parts.append('<' + tag + ''.join(result) + '>')
    def handle_startendtag(self, tag, attrs): self.handle_starttag(tag, attrs)
    def handle_endtag(self, tag): self.parts.append('</' + tag + '>')
    def handle_data(self, data): self.parts.append(data)
    def handle_entityref(self, name): self.parts.append('&' + name + ';')
    def handle_charref(self, name): self.parts.append('&#' + name + ';')

def shell(title, body, prefix=''):
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)} · Peeyush's notebook</title>
<link rel="stylesheet" href="{prefix}assets/style.css"><link rel="stylesheet" href="{prefix}assets/diagrams.css"></head><body>
<header><a class="brand" href="{prefix}index.html"><span class="mark">PR</span><span class="brand-copy">Peeyush Rao<span class="brand-caption">SECURITY NOTEBOOK</span></span></a>
<a class="repo" href="https://github.com/peeyushrao/peeyushrao.github.io">GitHub ↗</a></header>
{body}<footer>Peeyush Rao · Security notes <span>Learn. Practise. Revisit.</span></footer>
<script src="{prefix}assets/mermaid.min.js"></script><script src="{prefix}assets/diagrams.js"></script>
</body></html>'''

def build(destination=None):
    output = Path(destination) if destination else ROOT / 'dist'
    if output.exists():
        # Only the dedicated build folder may be cleared.
        if output.resolve() != (ROOT / 'dist').resolve():
            raise ValueError('Refusing to clear a directory other than dist')
        shutil.rmtree(output)
    (output / 'posts').mkdir(parents=True)
    shutil.copytree(ROOT / 'assets', output / 'assets')
    content = ROOT
    folders = discover_folders()
    paths = sorted((p for folder in folders for p in (content / folder).rglob('*')
                    if visible_file(p) and p.suffix.lower() in TYPES), key=natural_key)
    known = {p.relative_to(content).as_posix(): page_id(p.relative_to(content)) + '.html' for p in paths}
    # Keep linked images and original documents available, excluding hidden files.
    for folder in folders + (['images'] if (content / 'images').is_dir() else []):
      for p in (content / folder).rglob('*'):
        if visible_file(p):
            dest = output / 'files' / p.relative_to(content)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)
            # Preserve the standalone breathing tool and other public HTML tools.
            if folder == 'tools' and p.suffix.lower() == '.html':
                tool = output / p.relative_to(content)
                tool.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, tool)
    entries = []
    for p in paths:
        rel = p.relative_to(content)
        title = re.sub(r'[-_]+', ' ', p.stem)
        kind = p.suffix[1:].upper()
        original = '../files/' + quote(rel.as_posix())
        if kind == 'MD':
            text = p.read_text(encoding='utf-8-sig')
            # Optional front matter can be present; filename/first H1 supplies title.
            text = re.sub(r'\A---\s*\n.*?\n---\s*\n', '', text, flags=re.S)
            heading = re.search(r'^#{1,2}\s+(.+)$', text, re.M)
            if heading: title = unescape(re.sub('<[^>]+>', '', markdown.markdown(heading.group(1)))).strip()
            text = re.sub(r'<details\s*>', '<details markdown="1">', text)
            body = clean(markdown.markdown(text, extensions=['tables','fenced_code','toc','sane_lists','md_in_html']))
        elif kind == 'DOCX':
            with p.open('rb') as f:
                result = mammoth.convert_to_html(f)
            for message in result.messages: print(f'{rel}: {message.message}', file=sys.stderr)
            body = clean(result.value)
        else:
            body = f'<object class="pdf" data="{original}" type="application/pdf"><p>Your browser cannot preview this PDF. <a href="{original}">Open or download the PDF</a>.</p></object>'
        if kind != 'PDF':
            links = LocalLinks(p.resolve(), known)
            links.feed(body)
            body = ''.join(links.parts)
        plain = unescape(re.sub('<[^>]+>', ' ', body))
        plain = re.sub(r'\s+', ' ', plain).strip()
        excerpt = plain[:180] if kind != 'PDF' else 'PDF reference · Open to read or download.'
        entries.append({'title':title, 'folder':rel.parts[0], 'directory':rel.parent.as_posix(), 'type':kind,
                        'url':'posts/' + known[rel.as_posix()], 'excerpt':excerpt,
                        'text':plain, 'source':rel.as_posix()})
        article = f'''<main class="reading"><a class="back" href="../index.html">← All notes</a>
<div class="eyebrow">{escape(' / '.join(rel.parts[:-1]))} / {kind}</div><h1>{escape(title)}</h1>
<a class="download" href="{original}" download>Download original ↗</a><article>{body}</article></main>'''
        (output / 'posts' / known[rel.as_posix()]).write_text(shell(title, article, '../'), encoding='utf-8')
    buttons = '<button class="folder active" data-folder="">All notes <span>' + str(len(entries)) + '</span></button>'
    for folder in folders:
        directories = [content / folder] + sorted((p for p in (content / folder).rglob('*')
            if p.is_dir() and not any(part.startswith('.') for part in p.relative_to(content).parts)
            and not any(parent.is_symlink() for parent in [p, *p.parents])), key=natural_key)
        for directory in directories:
            key = directory.relative_to(content).as_posix()
            depth = len(directory.relative_to(content).parts) - 1
            count = sum(e['directory'] == key or e['directory'].startswith(key + '/') for e in entries)
            label = ('↳ ' if depth else '') + directory.name
            buttons += f'<button class="folder{ " child-folder" if depth else ""}" data-folder="{escape(key)}" style="--depth:{depth}" title="{escape(key)}">{escape(label)} <span>{count}</span></button>'
    cards = ''.join(f'''<a class="card" href="{escape(e['url'])}" data-folder="{escape(e['directory'])}" data-search="{escape((e['title']+' '+e['text']+' '+e['directory']).lower())}">
<div class="card-top"><span title="{escape(e['directory'])}">{escape(e['directory'].replace('/', ' / '))}</span><b>{e['type']}</b></div><h3>{escape(e['title'])}</h3><p>{escape(e['excerpt'])}</p><span class="read">Read note ↗</span></a>''' for e in entries)
    routes = json.dumps({e['source']:e['url'] for e in entries}, ensure_ascii=True).replace('<', '\\u003c')
    home = f'''<main><section class="hero"><div class="hero-copy"><div class="eyebrow">LEARNING IN THE OPEN</div>
<h1>Understand the systems.<br><em>Connect the signals.</em></h1><p>Practical notes on SOC, EDR, cloud security, and detection engineering.<br class="desktop"> A growing library for investigation and interview preparation.</p>
<div class="stats"><strong>{len(entries)}</strong> notes <i></i><strong>{len(folders)}</strong> folders <i></i><a href="tools/breathe-478.html">Take a breathing break ↗</a></div></div>
<div class="field-index"><div class="field-heading"><span>THE FIELD INDEX</span><b>VOL. 01</b></div>
<div class="field-row"><span>01</span><div><strong>Detection &amp; response</strong><small>Signals, investigations, and the endpoint</small></div></div>
<div class="field-row"><span>02</span><div><strong>Cloud &amp; infrastructure</strong><small>Workloads, identity, and what connects them</small></div></div>
<div class="field-row"><span>03</span><div><strong>Core concepts</strong><small>Questions worth understanding deeply</small></div></div>
<div class="field-footer"><span>SOC</span><span>EDR</span><span>CLOUD</span><span>RESEARCH</span></div></div></section>
<section class="library"><aside><div class="eyebrow">YOUR FOLDERS</div><nav aria-label="Filter notes by folder">{buttons}</nav>
<div class="aside-note">A place for the questions<br>worth coming back to.</div></aside>
<div class="notes"><div class="toolbar"><h2 id="folder-title">All notes</h2><label><span class="sr-only">Search notes</span><input id="search" type="search" placeholder="Search your notes…"></label></div>
<p id="result-count" aria-live="polite">{len(entries)} notes in your library</p><div class="cards">{cards}</div>
<div id="empty" hidden><h3>No notes here yet.</h3><p>Try another search, or add a document to this folder and push it to GitHub.</p></div></div></section></main>
<script id="legacy-routes" type="application/json">{routes}</script>
<script src="assets/app.js"></script>'''
    (output / 'index.html').write_text(shell('Security notes', home), encoding='utf-8')
    (output / '.nojekyll').touch()
    print(f'Built {len(entries)} notes in {output}')
    return entries

if __name__ == '__main__': build()
