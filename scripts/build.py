#!/usr/bin/env python3
"""모든지 정적 사이트 생성기: vault/ (Obsidian markdown) -> dist/ (static HTML).

사용: python scripts/build.py
의존성: pip install markdown
"""
import html as html_mod
import re
import shutil
import urllib.parse
from datetime import date
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
VAULT = ROOT / "vault"
DIST = ROOT / "dist"
SITE_NAME = "모든지"
TAGLINE = "모든 지식의 편찬과 집합소"
GITHUB = "https://github.com/say828/modernji"

MD_EXT = ["extra", "sane_lists", "toc"]


QUIZ_BLOCK_RE = re.compile(r"```quiz\n(.*?)```", re.S)


def parse_quiz(text: str):
    """quiz 블록 파싱. Q: 문제 / '- ' 오답 / '-* ' 정답 / E: 해설."""
    questions, cur = [], None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("Q:"):
            cur = {"q": s[2:].strip(), "opts": [], "exp": ""}
            questions.append(cur)
        elif s.startswith("-*") and cur:
            cur["opts"].append((s[2:].strip(), True))
        elif s.startswith("-") and cur:
            cur["opts"].append((s[1:].strip(), False))
        elif s.startswith("E:") and cur:
            cur["exp"] = s[2:].strip()
        elif s and cur:  # 접힌 줄은 직전 필드에 이어붙인다
            if cur["exp"]:
                cur["exp"] += " " + s
            elif not cur["opts"]:
                cur["q"] += " " + s
    return [q for q in questions if q["opts"]]


class Page:
    def __init__(self, src: Path):
        self.src = src
        self.rel = src.relative_to(VAULT)          # philosophy/foo.md
        self.key = str(self.rel.with_suffix(""))    # philosophy/foo
        self.raw = src.read_text()
        self.quizzes = []
        def _extract(m):
            self.quizzes.append(parse_quiz(m.group(1)))
            return f"%%QUIZ{len(self.quizzes) - 1}%%"
        self.raw = QUIZ_BLOCK_RE.sub(_extract, self.raw)
        m = re.search(r"^# (.+)$", self.raw, re.M)
        self.title = m.group(1).strip() if m else self.rel.stem
        self.is_index = self.rel.name == "index.md"
        self.section = self.rel.parts[0] if len(self.rel.parts) > 1 else ""
        # URL: index.md -> dir/, other.md -> dir/other/
        if self.is_index:
            self.url = "/" + "/".join(self.rel.parts[:-1])
        else:
            self.url = "/" + self.key
        if not self.url.endswith("/"):
            self.url += "/"
        self.backlinks: list["Page"] = []

    @property
    def href(self):
        return urllib.parse.quote(self.url)

    @property
    def out(self):
        return DIST / self.url.lstrip("/") / "index.html"


def load_pages():
    return {p.key: p for p in (Page(f) for f in sorted(VAULT.rglob("*.md")))}


def resolve_wikilinks(page: Page, pages: dict):
    def sub(m):
        # 마크다운 표 안에서는 파이프가 \| 로 이스케이프되므로 백슬래시를 걷어낸다
        inner = m.group(1).replace("\\|", "|").replace("\\", "")
        target, _, label = inner.partition("|")
        target = target.strip()
        label = label.strip() or target.split("/")[-1]
        hit = pages.get(target) or next(
            (p for k, p in pages.items() if k.split("/")[-1] == target or p.title == target), None)
        if hit is None:
            return label
        if hit is not page:
            hit.backlinks.append(page)
        return f'<a href="{hit.href}" class="wikilink">{label}</a>'
    return re.sub(r"\[\[([^\]]+)\]\]", sub, page.raw)


CSS = """
:root{
  --bg:#0e0e12;--bg2:#131318;--panel:#17171e;--border:#26262f;--border2:#32323e;
  --ink:#d7d7e0;--muted:#8b8b9a;--faint:#5c5c6a;
  --vio:#a78bfa;--vio2:#c4b5fd;--vio-deep:#7c5cff;--vio-bg:rgba(139,92,246,.10);
  --code-bg:#1a1a24;--sidebar-w:280px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{background:var(--bg);color:var(--ink);
  font-family:-apple-system,BlinkMacSystemFont,"Pretendard","Apple SD Gothic Neo","Malgun Gothic",sans-serif;
  font-size:16px;line-height:1.75;letter-spacing:-.01em}
a{color:var(--vio);text-decoration:none}
a:hover{color:var(--vio2)}
/* ---- layout ---- */
.wrap{display:flex;min-height:100vh}
.sidebar{width:var(--sidebar-w);flex-shrink:0;background:var(--bg2);border-right:1px solid var(--border);
  position:sticky;top:0;height:100vh;overflow-y:auto;padding:1.4rem 1.1rem 2rem}
.main{flex:1;min-width:0}
.content{max-width:47rem;margin:0 auto;padding:3.2rem 2rem 5rem}
/* ---- sidebar ---- */
.brand{display:flex;align-items:center;gap:.6rem;margin-bottom:1.6rem}
.brand .dot{width:26px;height:26px;border-radius:8px;flex-shrink:0;
  background:linear-gradient(135deg,#7c5cff,#c084fc);box-shadow:0 0 18px rgba(139,92,246,.45)}
.brand a{font-weight:800;font-size:1.15rem;color:var(--ink);letter-spacing:-.02em}
.brand a:hover{color:var(--vio2)}
.nav-sec{margin:1.2rem 0 .3rem;font-size:.72rem;font-weight:700;color:var(--faint);
  text-transform:uppercase;letter-spacing:.12em}
.nav a{display:block;padding:.32rem .6rem;margin:.1rem 0;border-radius:7px;color:var(--muted);
  font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.nav a:hover{background:var(--panel);color:var(--ink)}
.nav a.active{background:var(--vio-bg);color:var(--vio2);font-weight:600}
.nav details{margin:.1rem 0}
.nav summary{padding:.3rem .6rem;border-radius:7px;color:var(--muted);font-size:.88rem;
  font-weight:600;cursor:pointer;list-style:none;user-select:none}
.nav summary::-webkit-details-marker{display:none}
.nav summary::before{content:"▸ ";color:var(--faint)}
.nav details[open] summary::before{content:"▾ "}
.nav summary:hover{background:var(--panel);color:var(--ink)}
.nav details a{margin-left:.85rem;font-size:.86rem}
/* ---- typography ---- */
.content h1{font-size:2.05rem;font-weight:800;letter-spacing:-.03em;line-height:1.3;
  padding-bottom:.7rem;border-bottom:1px solid var(--border);margin-bottom:1.4rem}
.content h2{font-size:1.35rem;font-weight:700;letter-spacing:-.02em;margin:2.4rem 0 .8rem}
.content h3{font-size:1.08rem;font-weight:700;margin:1.8rem 0 .6rem;color:var(--vio2)}
.content p{margin:.85rem 0}
.content ul,.content ol{margin:.85rem 0 .85rem 1.5rem}
.content li{margin:.35rem 0}
.content strong{color:#fff}
.content blockquote{margin:1.3rem 0;padding:.75rem 1.2rem;border-left:3px solid var(--vio-deep);
  background:var(--vio-bg);border-radius:0 10px 10px 0;color:var(--vio2)}
.content blockquote p{margin:.3rem 0}
.content code{font-family:"D2Coding","SF Mono",Menlo,monospace;font-size:.88em;
  background:var(--code-bg);border:1px solid var(--border);border-radius:5px;padding:.12em .4em}
.content pre{background:var(--code-bg);border:1px solid var(--border);border-radius:10px;
  padding:1rem 1.2rem;overflow-x:auto;margin:1.2rem 0}
.content pre code{background:none;border:none;padding:0}
.content hr{border:none;border-top:1px solid var(--border);margin:2.2rem 0}
.content table{border-collapse:collapse;width:100%;margin:1.2rem 0;font-size:.92rem;display:block;overflow-x:auto}
.content th{text-align:left;color:var(--muted);font-weight:600;font-size:.8rem;
  text-transform:uppercase;letter-spacing:.06em}
.content th,.content td{padding:.55rem .8rem;border-bottom:1px solid var(--border)}
.content tr:hover td{background:rgba(139,92,246,.04)}
a.wikilink{border-bottom:1px dashed rgba(167,139,250,.5)}
/* ---- interactive quiz ---- */
.quiz{background:var(--bg2);border:1px solid var(--border);border-radius:14px;
  padding:1.2rem 1.3rem;margin:1.5rem 0}
.qz-q{margin:0 0 1.3rem}
.qz-text{font-weight:600;margin-bottom:.55rem}
.qz-opt{display:block;width:100%;text-align:left;background:var(--panel);
  border:1px solid var(--border);color:var(--ink);border-radius:9px;
  padding:.55rem .9rem;margin:.4rem 0;cursor:pointer;font:inherit;font-size:.93rem;
  transition:border-color .12s}
.qz-opt:hover{border-color:var(--vio-deep)}
.qz-q.done .qz-opt{cursor:default;opacity:.7}
.qz-opt.right{border-color:#34d399;background:rgba(52,211,153,.12);color:#a7f3d0;opacity:1!important}
.qz-opt.wrong{border-color:#f87171;background:rgba(248,113,113,.12);color:#fecaca;opacity:1!important}
.qz-exp{display:none;margin:.6rem 0 0;padding:.7rem 1rem;background:var(--vio-bg);
  border-left:3px solid var(--vio-deep);border-radius:0 8px 8px 0;font-size:.92rem;color:var(--vio2)}
.qz-exp.show{display:block}
.qz-foot{display:flex;justify-content:space-between;align-items:center;
  border-top:1px solid var(--border);padding-top:.8rem;font-size:.88rem;color:var(--muted)}
.qz-score{color:var(--vio2);font-weight:600}
.qz-prev{font-size:.78rem;color:var(--faint);margin-left:.5rem}
.qz-reset{background:none;border:1px solid var(--border2);color:var(--muted);
  border-radius:8px;padding:.3rem .8rem;cursor:pointer;font:inherit;font-size:.82rem}
.qz-reset:hover{color:var(--ink);border-color:var(--vio-deep)}
/* ---- quiz (details fallback) ---- */
.content details{margin:.7rem 0 1.3rem;background:var(--panel);border:1px solid var(--border);
  border-radius:10px;padding:.6rem 1rem}
.content details[open]{border-color:var(--vio-deep)}
.content summary{cursor:pointer;font-weight:600;color:var(--vio);font-size:.9rem;
  list-style:none;user-select:none}
.content summary::before{content:"▸ ";transition:transform .15s}
.content details[open] summary::before{content:"▾ "}
.content summary::-webkit-details-marker{display:none}
.content details p{margin:.6rem 0 .2rem;font-size:.95rem}
/* ---- chrome ---- */
.crumbs{font-size:.82rem;color:var(--faint);margin-bottom:1.1rem}
.crumbs a{color:var(--faint)} .crumbs a:hover{color:var(--vio)}
.backlinks{margin-top:3.5rem;padding:1rem 1.2rem;background:var(--panel);
  border:1px solid var(--border);border-radius:12px}
.backlinks h4{font-size:.75rem;color:var(--faint);text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem}
.backlinks a{display:inline-block;margin-right:1rem;font-size:.9rem}
.foot{margin-top:4rem;padding-top:1.2rem;border-top:1px solid var(--border);
  font-size:.8rem;color:var(--faint);display:flex;justify-content:space-between;flex-wrap:wrap;gap:.5rem}
.foot a{color:var(--faint)} .foot a:hover{color:var(--vio)}
/* ---- hero (home) ---- */
.hero{position:relative;text-align:center;padding:4.5rem 0 3rem;overflow:hidden}
.hero .mark{font-size:4.2rem;font-weight:900;letter-spacing:-.04em;line-height:1.1;
  background:linear-gradient(120deg,#e9e4ff 10%,#a78bfa 45%,#7c5cff 80%);
  -webkit-background-clip:text;background-clip:text;color:transparent;
  filter:drop-shadow(0 0 32px rgba(139,92,246,.35))}
.hero .tag{margin-top:.9rem;font-size:1.15rem;color:var(--muted);letter-spacing:.02em}
.hero .sub{margin-top:.4rem;font-size:.85rem;color:var(--faint)}
.constellation{position:absolute;inset:0;z-index:-1;opacity:.5}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:.9rem;margin:2rem 0}
.card{display:block;background:var(--panel);border:1px solid var(--border);border-radius:14px;
  padding:1.1rem 1.2rem;transition:border-color .15s,transform .15s}
.card:hover{border-color:var(--vio-deep);transform:translateY(-2px)}
.card .t{font-weight:700;color:var(--ink);margin-bottom:.25rem}
.card .d{font-size:.84rem;color:var(--muted);line-height:1.55}
.card.ghost{opacity:.45;pointer-events:none}
/* ---- mobile ---- */
.menu-btn{display:none}
@media(max-width:860px){
  .sidebar{position:fixed;z-index:50;left:0;transform:translateX(-100%);transition:transform .2s;width:min(80vw,300px)}
  .sidebar.open{transform:none;box-shadow:0 0 0 100vmax rgba(0,0,0,.55)}
  .menu-btn{display:flex;align-items:center;gap:.5rem;position:sticky;top:0;z-index:40;width:100%;
    background:rgba(14,14,18,.85);backdrop-filter:blur(10px);border:none;border-bottom:1px solid var(--border);
    color:var(--ink);font-size:.95rem;font-weight:700;padding:.8rem 1.2rem;cursor:pointer}
  .content{padding:2rem 1.2rem 4rem}
  .hero .mark{font-size:3rem}
}
::-webkit-scrollbar{width:10px;height:10px}
::-webkit-scrollbar-thumb{background:var(--border2);border-radius:5px}
::-webkit-scrollbar-track{background:transparent}
"""

CONSTELLATION = """
<svg class="constellation" viewBox="0 0 800 360" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
 <g stroke="#8b5cf6" stroke-opacity=".25" stroke-width="1">
  <line x1="120" y1="80" x2="260" y2="150"/><line x1="260" y1="150" x2="410" y2="70"/>
  <line x1="410" y1="70" x2="560" y2="160"/><line x1="560" y1="160" x2="700" y2="90"/>
  <line x1="260" y1="150" x2="330" y2="280"/><line x1="560" y1="160" x2="480" y2="290"/>
  <line x1="330" y1="280" x2="480" y2="290"/><line x1="120" y1="80" x2="90" y2="250"/>
  <line x1="90" y1="250" x2="330" y2="280"/><line x1="700" y1="90" x2="730" y2="260"/>
  <line x1="480" y1="290" x2="730" y2="260"/>
 </g>
 <g fill="#a78bfa">
  <circle cx="120" cy="80" r="4" fill-opacity=".9"/><circle cx="260" cy="150" r="6" fill-opacity=".7"/>
  <circle cx="410" cy="70" r="3.5" fill-opacity=".9"/><circle cx="560" cy="160" r="5" fill-opacity=".7"/>
  <circle cx="700" cy="90" r="4" fill-opacity=".8"/><circle cx="330" cy="280" r="4.5" fill-opacity=".6"/>
  <circle cx="480" cy="290" r="3.5" fill-opacity=".7"/><circle cx="90" cy="250" r="3" fill-opacity=".6"/>
  <circle cx="730" cy="260" r="3.5" fill-opacity=".6"/>
 </g>
</svg>
"""

TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='24' fill='%237c5cff'/><text x='50' y='68' font-size='52' text-anchor='middle' fill='white' font-family='sans-serif' font-weight='bold'>知</text></svg>">
<style>{css}</style>
</head>
<body>
<button class="menu-btn" onclick="document.querySelector('.sidebar').classList.toggle('open')">☰ {site}</button>
<div class="wrap">
<aside class="sidebar">
  <div class="brand"><div class="dot"></div><a href="/">{site}</a></div>
  <nav class="nav">{nav}</nav>
</aside>
<div class="main"><div class="content">
{crumbs}
{body}
{backlinks}
<div class="foot">
  <span>{site} · {tagline}</span>
  <span><a href="{github}">GitHub</a> · {today}</span>
</div>
</div></div>
</div>
{quizjs}
</body>
</html>
"""

QUIZ_JS = """<script>
(function(){
  document.querySelectorAll('.quiz').forEach(function(quiz){
    var key='mj-wrong-'+quiz.dataset.key+'-'+quiz.dataset.block;
    var qs=quiz.querySelectorAll('.qz-q');
    var score=quiz.querySelector('.qz-score');
    var prevEl=quiz.querySelector('.qz-prev');
    var answered=0, correct=0;
    try{
      var prev=JSON.parse(localStorage.getItem(key)||'[]');
      if(prev.length) prevEl.textContent='지난 시도: '+prev.length+'문제 틀림. 그 문제들이 오늘 새겨질 차례.';
    }catch(e){}
    function upd(){score.textContent=answered? correct+' / '+qs.length+' 정답':'';}
    qs.forEach(function(q,qi){
      q.querySelectorAll('.qz-opt').forEach(function(opt){
        opt.addEventListener('click',function(){
          if(q.classList.contains('done'))return;
          q.classList.add('done');answered++;
          if(opt.dataset.c==='1'){opt.classList.add('right');correct++;}
          else{
            opt.classList.add('wrong');
            q.querySelector('.qz-opt[data-c="1"]').classList.add('right');
            try{
              var w=JSON.parse(localStorage.getItem(key)||'[]');
              if(w.indexOf(qi)<0){w.push(qi);localStorage.setItem(key,JSON.stringify(w));}
            }catch(e){}
          }
          q.querySelector('.qz-exp').classList.add('show');
          upd();
        });
      });
    });
    quiz.querySelector('.qz-reset').addEventListener('click',function(){
      qs.forEach(function(q){
        q.classList.remove('done');
        q.querySelectorAll('.qz-opt').forEach(function(o){o.classList.remove('right','wrong');});
        q.querySelector('.qz-exp').classList.remove('show');
      });
      answered=0;correct=0;upd();
      try{localStorage.removeItem(key);}catch(e){}
      prevEl.textContent='';
    });
  });
})();
</script>"""


def render_quiz(page: Page, block_idx: int, questions: list) -> str:
    esc = html_mod.escape
    parts = [f'<div class="quiz" data-key="{esc(page.key)}" data-block="{block_idx}">']
    for n, q in enumerate(questions, 1):
        opts = "".join(
            f'<button class="qz-opt" data-c="{int(correct)}">{esc(text)}</button>'
            for text, correct in q["opts"])
        exp = f'<div class="qz-exp">💡 {esc(q["exp"])}</div>' if q["exp"] else ""
        parts.append(
            f'<div class="qz-q"><div class="qz-text">문제 {n}. {esc(q["q"])}</div>'
            f'<div>{opts}</div>{exp}</div>')
    parts.append('<div class="qz-foot"><span><span class="qz-score"></span>'
                 '<span class="qz-prev"></span></span>'
                 '<button class="qz-reset">다시 풀기</button></div></div>')
    return "".join(parts)

SECTION_LABELS = {"about": "소개", "philosophy": "철학"}


def build_nav(pages: dict, current: Page):
    home = pages.get("index")
    items = []
    if home:
        cls = ' class="active"' if current is home else ""
        items.append(f'<a href="/"{cls}>🏠 홈</a>')
    by_sec: dict[str, list[Page]] = {}
    for p in pages.values():
        if p.section:
            by_sec.setdefault(p.section, []).append(p)
    for sec in sorted(by_sec):
        label = SECTION_LABELS.get(sec, sec)
        items.append(f'<div class="nav-sec">{label}</div>')
        sec_pages = sorted(by_sec[sec], key=lambda p: (not p.is_index, str(p.rel)))
        # "01-철학입문-1강-..." 형태는 과목별 접이식 그룹으로 묶는다
        courses: dict[tuple, list] = {}
        flat = []
        for p in sec_pages:
            m = re.match(r"^(\d+)-([^-]+)-", p.rel.stem)
            if p.is_index or not m:
                flat.append(p)
            else:
                courses.setdefault((m.group(1), m.group(2)), []).append(p)
        for p in flat:
            name = "개요" if p.is_index else p.title
            cls = ' class="active"' if p is current else ""
            items.append(f'<a href="{p.href}"{cls}>{name}</a>')
        for (num, cname), plist in sorted(courses.items()):
            opened = " open" if any(p is current for p in plist) else ""
            items.append(f'<details class="nav-course"{opened}>'
                         f'<summary>{int(num):02d} {cname}</summary>')
            for p in plist:
                name = re.sub(r"^\S+\s+", "", p.title)  # "철학입문 1강. X" -> "1강. X"
                cls = ' class="active"' if p is current else ""
                items.append(f'<a href="{p.href}"{cls}>{name}</a>')
            items.append("</details>")
    return "\n".join(items)


def build_crumbs(page: Page):
    if page.key == "index":
        return ""
    parts = [f'<a href="/">{SITE_NAME}</a>']
    if page.section:
        label = SECTION_LABELS.get(page.section, page.section)
        parts.append(f'<a href="/{page.section}/">{label}</a>')
    if not page.is_index:
        parts.append(page.title)
    return '<div class="crumbs">' + " / ".join(parts) + "</div>"


def first_sentence(page: Page):
    for line in page.raw.splitlines():
        line = line.strip()
        if line and not line.startswith(("#", ">", "|", "-", "!", "%%", "`", "<")):
            return re.sub(r"[*\[\]]|\{[^}]*\}", "", line)[:150]
    return TAGLINE


def render_home(body_html: str, pages: dict):
    n_docs = len(pages)
    hero = f"""
<div class="hero">{CONSTELLATION}
  <div class="mark">모든지</div>
  <div class="tag">{TAGLINE} · 모든 지식은 문제로 먼저 만난다</div>
  <div class="sub">modernji.com · 문서 {n_docs}편 · 틀린 만큼 새겨진다</div>
</div>
<div class="cards">
  <a class="card" href="/philosophy/"><div class="t">🏛 철학</div>
    <div class="d">철학과 4년 커리큘럼 18과목 88강을 순서대로. 매 강 문제로 열고 문제로 닫는다.</div></a>
  <a class="card" href="/about/"><div class="t">🧠 모던지란</div>
    <div class="d">문제풀이 기반 지식 편찬이라는 개발 철학과 그 선행연구 근거. 문제 2개로 바로 체험.</div></a>
  <div class="card ghost"><div class="t">🔬 과학</div><div class="d">준비 중</div></div>
  <div class="card ghost"><div class="t">📜 역사</div><div class="d">준비 중</div></div>
</div>
"""
    # 홈은 히어로가 제목을 대신하므로 본문에서 h1과 첫 문단(태그라인 중복)을 제거
    body_html = re.sub(r"<h1[^>]*>.*?</h1>", "", body_html, count=1, flags=re.S)
    body_html = re.sub(r"<p>모든 지식의 편찬과 집합소\.?</p>", "", body_html, count=1)
    return hero + body_html


def main():
    if DIST.exists():
        shutil.rmtree(DIST)
    pages = load_pages()
    for page in pages.values():
        text = resolve_wikilinks(page, pages)
        page.html = markdown.markdown(text, extensions=MD_EXT)
        for bi, qz in enumerate(page.quizzes):
            widget = render_quiz(page, bi, qz)
            ph = f"%%QUIZ{bi}%%"
            page.html = page.html.replace(f"<p>{ph}</p>", widget).replace(ph, widget)
    today = date.today().isoformat()
    for page in pages.values():
        body = render_home(page.html, pages) if page.key == "index" else page.html
        bl = ""
        uniq = {b.key: b for b in page.backlinks if b is not page}
        if uniq:
            links = "".join(f'<a href="{b.href}">← {b.title}</a>' for b in uniq.values())
            bl = f'<div class="backlinks"><h4>이 문서를 언급함</h4>{links}</div>'
        title = SITE_NAME if page.key == "index" else f"{page.title} · {SITE_NAME}"
        html = TEMPLATE.format(
            title=title, desc=first_sentence(page), css=CSS, site=SITE_NAME,
            nav=build_nav(pages, page), crumbs=build_crumbs(page), body=body,
            backlinks=bl, tagline=TAGLINE, github=GITHUB, today=today,
            quizjs=QUIZ_JS if page.quizzes else "")
        page.out.parent.mkdir(parents=True, exist_ok=True)
        page.out.write_text(html)
        print(f"  {page.rel} -> {page.out.relative_to(ROOT)}")
    # 404
    (DIST / "404.html").write_text(TEMPLATE.format(
        title=f"404 · {SITE_NAME}", desc=TAGLINE, css=CSS, site=SITE_NAME,
        nav=build_nav(pages, pages["index"]), crumbs="",
        body='<div class="hero"><div class="mark">404</div>'
             '<div class="tag">아직 모르는 페이지입니다</div>'
             '<div class="sub"><a href="/">홈으로</a></div></div>',
        backlinks="", tagline=TAGLINE, github=GITHUB, today=today, quizjs=""))
    print(f"OK: {len(pages)} pages -> {DIST}")


if __name__ == "__main__":
    main()
