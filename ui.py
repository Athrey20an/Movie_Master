"""Visual layer: CSS and HTML card rendering. Posters come from the dataset's poster_path (TMDB image CDN)."""
import html

from movie_master import FLAGS

POSTER_BASE = "https://image.tmdb.org/t/p/w342"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Inter:wght@400;500;600;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox { font-family: 'Inter', sans-serif; }
.stApp { background: #0B0B0F; color: #F2F2F5; }   /* backup if .streamlit/config.toml is missing */
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1160px; }
*, *::before, *::after { box-sizing: border-box; }

/* Hero */
.hero { text-align: center; padding: 2.2rem 1rem 1.2rem; margin-bottom: .8rem; border-radius: 20px;
  position: relative; overflow: hidden; isolation: isolate; }
.hero::before { content: ""; position: absolute; inset: -30%; z-index: -1;
  background: radial-gradient(circle at 50% 30%, rgba(229,9,20,.30), rgba(11,11,15,0) 55%);
  animation: drift 14s ease-in-out infinite; }
/* MOVIE / MASTER logo: stacked Anton lettering, warm cream fill, film grain, slow light sweep */
.hero h1.logo { margin: 0 auto; display: inline-flex; flex-direction: column; align-items: center;
  font-family: 'Anton', Impact, 'Arial Narrow', sans-serif; font-weight: 400; line-height: .9;
  font-size: clamp(3.3rem, 10vw, 6.4rem);   /* MASTER size; MOVIE and the divider scale from it */
  text-transform: uppercase; filter: drop-shadow(0 10px 30px rgba(229,9,20,.35)); }
.logo .l1, .logo .l2 { display: block;
  background:
    linear-gradient(105deg, transparent 42%, rgba(255,255,255,.9) 50%, transparent 58%),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0.25 0 0 0 0 0.16 0 0 0 0 0.08 0 0 0 .6 0'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E"),
    linear-gradient(180deg, #FFF6E6 0%, #F1DDBC 55%, #CFA877 100%);
  background-size: 260% 100%, 140px 140px, 100% 100%;
  background-position: 160% 0, 0 0, 0 0;
  -webkit-background-clip: text; background-clip: text; color: transparent;
  animation: logoSweep 7s ease-in-out 1.2s infinite, logoIn .8s cubic-bezier(.2,.8,.2,1) both; }
.logo .l1 { font-size: .5em; letter-spacing: .93em; margin-right: -.93em; }   /* tracked out to MASTER's width */
.logo .l2 { font-size: 1em; letter-spacing: .02em; animation-delay: 1.35s, .12s; }
.logo .rule { width: 100%; height: 3px; margin: .1em 0 .17em; border-radius: 2px;
  background: linear-gradient(90deg, transparent, #E50914 18%, #FF4D57 50%, #E50914 82%, transparent);
  transform-origin: center; animation: ruleIn .9s cubic-bezier(.2,.8,.2,1) .25s both; }
@keyframes logoSweep { 0% { background-position: 160% 0, 0 0, 0 0; } 45%, 100% { background-position: -60% 0, 0 0, 0 0; } }
@keyframes logoIn { from { opacity: 0; translate: 0 18px; } }
@keyframes ruleIn { from { transform: scaleX(0); opacity: 0; } to { transform: scaleX(1); opacity: 1; } }
.hero p, .stats { animation: fadeUp .7s ease .15s both; }
.marquee { overflow: hidden; margin: 1.4rem -1rem 0; animation: fadeUp .9s ease .3s both;
  -webkit-mask-image: linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent);
  mask-image: linear-gradient(90deg, transparent, #000 12%, #000 88%, transparent); }
.track { display: flex; gap: .7rem; width: max-content; animation: scroll 70s linear infinite; }
.marquee:hover .track { animation-play-state: paused; }
.track img { height: 132px; aspect-ratio: 2/3; object-fit: cover; border-radius: 9px; opacity: .55;
  background: #1c1c25; transition: opacity .3s ease, transform .3s ease; }
.track img:hover { opacity: 1; transform: translateY(-4px) scale(1.05); }
@media (max-width: 560px) { .track img { height: 96px; } }
.hero p { color: #A8A8B3; font-size: 1.05rem; margin: 1.1rem auto 0; max-width: 600px; }
.stats { display: flex; justify-content: center; gap: 1.6rem; margin-top: 1rem; flex-wrap: wrap; }
.stats div { color: #8E8E99; font-size: .82rem; }
.stats b { color: #fff; font-size: 1.05rem; display: block; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { gap: .4rem; justify-content: center; border-bottom: none; }
.stTabs [data-baseweb="tab"] { background: #17171F; border-radius: 999px; padding: .5rem 1.2rem;
  height: auto; transition: background .2s ease; }
.stTabs [aria-selected="true"] { background: #E50914 !important; color: #fff !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none; }

/* Section heading */
.section { font-size: 1.25rem; font-weight: 600; margin: 1.8rem 0 .3rem; }
.section { animation: fadeUp .5s ease both; }
.section span { color: #E50914; background: linear-gradient(#E50914, #E50914) left bottom / 0 2px no-repeat;
  padding-bottom: 2px; animation: underline .7s ease .25s forwards; }
.subsection { color: #8E8E99; font-size: .88rem; margin: 0 0 .9rem; }

/* Poster grid */
.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1.1rem; }
.grid.six { grid-template-columns: repeat(var(--n, 6), 1fr); gap: .9rem; }
@media (max-width: 900px) { .grid, .grid.six { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 560px) { .grid, .grid.six { grid-template-columns: repeat(2, 1fr); gap: .8rem; }
  .seed { flex-direction: column; text-align: center; } .hero { padding: 1.4rem .5rem 1rem; } }

.grid { perspective: 1200px; }
.card { background: #17171F; border-radius: 14px; overflow: hidden; position: relative;
  animation: rise .55s cubic-bezier(.2,.8,.2,1) both;
  transition: transform .3s cubic-bezier(.2,.8,.2,1), box-shadow .3s ease; }
.card:hover { transform: translateY(-8px) rotateX(4deg); box-shadow: 0 18px 36px rgba(229,9,20,.28); }
.grid.six .card { animation: flipIn .7s cubic-bezier(.2,.8,.2,1) both; transform-origin: left center; }
.card:nth-child(1){animation-delay:.00s} .card:nth-child(2){animation-delay:.08s}
.card:nth-child(3){animation-delay:.16s} .card:nth-child(4){animation-delay:.24s}
.card:nth-child(5){animation-delay:.32s} .card:nth-child(6){animation-delay:.40s}
@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }
@keyframes rise { from { opacity: 0; translate: 0 22px; scale: .96; } to { opacity: 1; translate: 0 0; scale: 1; } }
@keyframes flipIn { from { opacity: 0; rotate: y -75deg; } to { opacity: 1; rotate: y 0deg; } }
@keyframes shimmer { from { background-position: 200% 0; } to { background-position: -200% 0; } }
@keyframes titleShine { to { background-position: 200% center; } }
@keyframes drift { 0%, 100% { transform: translate(-12%, -8%); } 50% { transform: translate(12%, 6%); } }
@keyframes scroll { to { transform: translateX(-50%); } }
@keyframes underline { to { background-size: 100% 2px; } }
@keyframes slideIn { from { opacity: 0; translate: -8px 0; } to { opacity: 1; translate: 0 0; } }
@keyframes glow { 0%, 100% { box-shadow: 0 0 0 0 rgba(229,9,20,.45); } 50% { box-shadow: 0 0 0 8px rgba(229,9,20,0); } }

.pwrap { overflow: hidden; position: relative; }
.pwrap::after { content: ""; position: absolute; inset: 0; pointer-events: none;
  background: linear-gradient(115deg, transparent 35%, rgba(255,255,255,.22) 50%, transparent 65%);
  transform: translateX(-130%); transition: transform .8s ease; }
.card:hover .pwrap::after { transform: translateX(130%); }
.poster { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block; transition: transform .5s ease;
  background: linear-gradient(90deg, #1c1c25 25%, #2b2b37 50%, #1c1c25 75%); background-size: 200% 100%;
  animation: shimmer 1.6s linear infinite; }
.card:hover .poster { transform: scale(1.06); }
.noposter { width: 100%; aspect-ratio: 2/3; display: flex; flex-direction: column; gap: .5rem; align-items: center;
  justify-content: center; text-align: center; padding: 1rem; font-weight: 700; font-size: 1rem; color: #fff;
  overflow-wrap: anywhere; background: linear-gradient(160deg, #3a0a0e, #17171F 60%); }
.badge { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,.75); backdrop-filter: blur(4px);
  color: #FFD54A; font-weight: 600; font-size: .8rem; padding: .25rem .55rem; border-radius: 999px; }
.langtag { position: absolute; top: 10px; left: 10px; background: rgba(229,9,20,.92); color: #fff;
  font-weight: 600; font-size: .75rem; padding: .25rem .6rem; border-radius: 999px; }
.info { padding: .75rem .8rem .9rem; }
.title { font-weight: 600; font-size: .95rem; line-height: 1.25; margin: 0; color: #fff; }
.orig { color: #8E8E99; font-size: .75rem; font-style: italic; margin: .1rem 0 0; }
.meta { color: #8E8E99; font-size: .76rem; margin: .3rem 0 .5rem; line-height: 1.5; }
.mpaa { font-size: .64rem; font-weight: 600; padding: .02rem .35rem; border: 1px solid #5A5A66;
  border-radius: 4px; color: #C9C9D1; margin-left: .3rem; }
.chips { display: flex; flex-wrap: wrap; gap: .3rem; }
.chip { font-size: .66rem; padding: .15rem .5rem; border-radius: 999px; background: #24242E; color: #C9C9D1; }
.why { margin-top: .6rem; font-size: .74rem; line-height: 1.4; color: #E8C7C9;
  background: rgba(229,9,20,.08); border-left: 2px solid #E50914; padding: .35rem .5rem; border-radius: 0 6px 6px 0;
  animation: slideIn .5s ease .45s both; }
.card details { margin-top: .5rem; font-size: .76rem; color: #A8A8B3; }
.card summary { cursor: pointer; color: #E50914; font-weight: 500; list-style: none; }
.card summary::-webkit-details-marker { display: none; }
.card details p { margin: .4rem 0 0; line-height: 1.45; }

/* Selected movie banner */
.seed { display: flex; gap: 1.2rem; align-items: center; background: #17171F; border-radius: 16px;
  padding: 1rem; animation: fadeUp .4s ease forwards; margin-top: .6rem; }
.seed img, .seed .noposter { width: 96px; min-width: 96px; border-radius: 10px; aspect-ratio: 2/3; object-fit: cover; }
.seed h3 { margin: 0 0 .2rem; font-size: 1.25rem; }
.seed p { margin: .3rem 0 0; color: #A8A8B3; font-size: .88rem; line-height: 1.45; }

[data-testid="stPills"] button { border-radius: 999px !important; transition: all .2s ease; }
[data-testid="stPills"] button:hover { transform: translateY(-2px); }
[data-testid="stPills"] button[aria-checked="true"], [data-testid="stPills"] button[kind*="Active"] {
  box-shadow: 0 0 14px rgba(229,9,20,.45); }
[data-testid="stButton"] button { border-radius: 999px; border: 1px solid #E50914; background: #17171F;
  font-weight: 600; transition: transform .2s ease, background .2s ease; animation: glow 2.4s ease-in-out infinite; }
[data-testid="stButton"] button:hover { background: #E50914; color: #fff; transform: translateY(-2px) scale(1.03); }
[data-testid="stButton"] button:active { transform: scale(.96); }
.stTabs [data-baseweb="tab"]:hover { background: #24242E; }

/* Respect "reduce motion" settings */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation: none !important; transition: none !important; }
  .section span { background-size: 100% 2px; }
}

.foot { text-align: center; color: #6B6B76; font-size: .75rem; margin-top: 3rem; line-height: 1.6; }
.foot a { color: #8E8E99; }
</style>
"""
CSS = "\n".join(line for line in CSS.splitlines() if line.strip())  # blank lines break st.markdown HTML

e = html.escape


def lang_label(code, name):
    return f"{FLAGS.get(code, '🌐')} {name}"


def _poster(path, title):
    if path:
        return f'<img class="poster" src="{POSTER_BASE}{path}" alt="{e(title)} poster" loading="lazy">'
    return f'<div class="noposter"><span style="font-size:2rem">🎬</span>{e(title)}</div>'


def _year(y):
    return "" if str(y) == "<NA>" else str(y)


def _card(r, tag=None):
    title = str(r["title"])
    orig = str(r["original_title"])
    orig_html = f'<p class="orig">{e(orig)}</p>' if orig and orig.lower() != title.lower() else ""
    runtime = f" · {int(r['runtime'])} min" if r["runtime"] == r["runtime"] and r["runtime"] else ""
    imdb = f" · IMDb {r['imdb_score']:.1f}" if r["imdb_score"] == r["imdb_score"] else ""
    mpaa = f'<span class="mpaa">{e(r["mpaa"])}</span>' if r["mpaa"] else ""
    lang = "" if tag else f" · {lang_label(r['original_language'], r['lang'])}"
    chips = "".join(f'<span class="chip">{e(g)}</span>' for g in r["genre_list"][:3])
    why = f'<div class="why">💡 {e(r["why"])}</div>' if r.get("why") else ""
    plot = f'<details><summary>Plot ▾</summary><p>{e(str(r["overview"]))}</p></details>' if r["overview"] else ""
    tag_html = f'<div class="langtag">{e(tag)}</div>' if tag else ""
    return (f'<div class="card"><div class="pwrap">{_poster(r["poster_path"], title)}</div>{tag_html}'
            f'<div class="badge">★ {r["vote_average"]:.1f}</div>'
            f'<div class="info"><p class="title">{e(title)}</p>{orig_html}'
            f'<p class="meta">{_year(r["year"])}{runtime}{lang}{imdb}{mpaa}</p>'
            f'<div class="chips">{chips}</div>{why}{plot}</div></div>')


def cards_html(results):
    return '<div class="grid">' + "".join(_card(r) for _, r in results.iterrows()) + "</div>"


def twins_html(results):
    cards = "".join(_card(r, tag=lang_label(r["original_language"], r["lang"])) for _, r in results.iterrows())
    n = max(4, len(results))   # 4+ columns so 2-3 twins don't stretch into giant cards
    return f'<div class="grid six" style="--n:{n}">{cards}</div>'


def seed_html(row):
    img = (f'<img src="{POSTER_BASE}{row["poster_path"]}" alt="">' if row["poster_path"]
           else '<div class="noposter"><span style="font-size:1.8rem">🎬</span></div>')
    genres = " · ".join(row["genre_list"][:3])
    mpaa = f'<span class="mpaa">{e(row["mpaa"])}</span>' if row["mpaa"] else ""
    orig = row["original_title"]
    orig_html = (f' <span style="color:#8E8E99;font-weight:400;font-style:italic;font-size:.95rem">{e(orig)}</span>'
                 if orig and orig.lower() != row["title"].lower() else "")
    people = []
    if row["director"]:
        people.append("Dir. " + e(row["director"].replace("|", ", ")))
    if row["writers"]:
        people.append("Written by " + e(row["writers"].replace("|", ", ")))
    people_html = f'<div class="meta">{" · ".join(people)}</div>' if people else ""
    overview = row["overview"]
    short = e(overview[:230]) + ("…" if len(overview) > 230 else "")
    return (f'<div class="seed">{img}<div><h3>{e(row["title"])}{orig_html} '
            f'<span style="color:#8E8E99;font-weight:400">{_year(row["year"])}</span></h3>'
            f'<div class="meta">★ {row["vote_average"]:.1f} · {lang_label(row["original_language"], row["lang"])}'
            f' · {e(genres)}{mpaa}</div>{people_html}<p>{short}</p></div></div>')


def hero_html(n_movies, n_langs, posters=()):
    strip = ""
    if posters:
        imgs = "".join(f'<img src="https://image.tmdb.org/t/p/w185{p}" alt="" loading="lazy">' for p in posters)
        strip = f'<div class="marquee"><div class="track">{imgs}{imgs}</div></div>'   # doubled for a seamless loop
    return ('<div class="hero"><h1 class="logo" aria-label="Movie Master">'
            '<span class="l1">Movie</span><span class="rule"></span><span class="l2">Master</span></h1>'
            '<p>Pick a movie you love, or tell it how you feel. Get picks from around the world, '
            'with the reason behind every one.</p>'
            f'<div class="stats"><div><b>{n_movies:,}</b>movies</div><div><b>{n_langs}</b>languages</div>'
            f'<div><b>10</b>moods</div></div>{strip}</div>')


def background_css(b64, ratio, mime="webp"):
    """Clapperboard watermark: fixed in the bottom-right corner, faint, slowly floating."""
    return f"""<style>
.stApp {{ background-color: #0B0B0F !important; }}   /* never change .stApp's position: it collapses the page */
/* Streamlit's inner containers can carry the theme colour and hide the watermark: make them see-through */
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stMainBlockContainer"],
section.main, .main, [data-testid="stHeader"], [data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stAppViewBlockContainer"] {{ background: transparent !important; }}
.stApp::before {{ content: ""; position: fixed; right: -70px; bottom: -50px; z-index: 0; pointer-events: none;
  width: min(560px, 62vw); aspect-ratio: {ratio:.4f};
  background: url(data:image/{mime};base64,{b64}) no-repeat center / contain;
  opacity: .11; animation: floaty 14s ease-in-out infinite; }}
.block-container {{ position: relative; z-index: 1; }}
@keyframes floaty {{ 0%, 100% {{ transform: rotate(-12deg) translateY(0); }}
  50% {{ transform: rotate(-9deg) translateY(-14px); }} }}
@media (max-width: 560px) {{ .stApp::before {{ opacity: .07; right: -40px; bottom: -30px; }} }}
@media (prefers-reduced-motion: reduce) {{ .stApp::before {{ transform: rotate(-12deg); }} }}
</style>"""


FOOTER = ('<div class="foot">Built by Athreyan Babu with Python, scikit-learn and Streamlit<br>'
          'Movie data and posters from <a href="https://www.themoviedb.org" target="_blank">TMDB</a> '
          '(via Kaggle datasets), with MPAA ratings from an IMDb-based Kaggle dataset. '
          'This product uses the TMDB API but is not endorsed or certified by TMDB.</div>')
