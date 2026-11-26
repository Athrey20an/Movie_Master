"""Visual layer: CSS and HTML card rendering. Posters come from the dataset's poster_path (TMDB image CDN)."""
import html

from movie_master import FLAGS

POSTER_BASE = "https://image.tmdb.org/t/p/w342"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;800&display=swap');
html, body, [class*="css"], .stMarkdown, .stTextInput, .stSelectbox { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 1160px; }
*, *::before, *::after { box-sizing: border-box; }

/* Hero */
.hero { text-align: center; padding: 2.2rem 1rem 1.4rem; margin-bottom: .8rem; border-radius: 20px;
  background: radial-gradient(circle at 50% 0%, rgba(229,9,20,.28), rgba(11,11,15,0) 70%); }
.hero h1 { font-size: clamp(2.2rem, 6vw, 3.6rem); font-weight: 800; letter-spacing: -1.5px; margin: 0;
  background: linear-gradient(90deg, #fff 0%, #ffb3b8 55%, #E50914 100%);
  -webkit-background-clip: text; background-clip: text; color: transparent; }
.hero p { color: #A8A8B3; font-size: 1.05rem; margin: .6rem auto 0; max-width: 600px; }
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
.section span { color: #E50914; }
.subsection { color: #8E8E99; font-size: .88rem; margin: 0 0 .9rem; }

/* Poster grid */
.grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 1.1rem; }
.grid.six { grid-template-columns: repeat(var(--n, 6), 1fr); gap: .9rem; }
@media (max-width: 900px) { .grid, .grid.six { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 560px) { .grid, .grid.six { grid-template-columns: repeat(2, 1fr); gap: .8rem; }
  .seed { flex-direction: column; text-align: center; } .hero { padding: 1.4rem .5rem 1rem; } }

.card { background: #17171F; border-radius: 14px; overflow: hidden; position: relative;
  opacity: 0; animation: fadeUp .5s ease forwards; transition: transform .25s ease, box-shadow .25s ease; }
.card:hover { transform: translateY(-6px); box-shadow: 0 14px 30px rgba(229,9,20,.25); }
.card:nth-child(1){animation-delay:.00s} .card:nth-child(2){animation-delay:.07s}
.card:nth-child(3){animation-delay:.14s} .card:nth-child(4){animation-delay:.21s}
.card:nth-child(5){animation-delay:.28s} .card:nth-child(6){animation-delay:.35s}
@keyframes fadeUp { from { opacity: 0; transform: translateY(14px); } to { opacity: 1; transform: none; } }

.pwrap { overflow: hidden; position: relative; }
.poster { width: 100%; aspect-ratio: 2/3; object-fit: cover; display: block; transition: transform .4s ease;
  background: #24242E; }
.card:hover .poster { transform: scale(1.04); }
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
  background: rgba(229,9,20,.08); border-left: 2px solid #E50914; padding: .35rem .5rem; border-radius: 0 6px 6px 0; }
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


def hero_html(n_movies, n_langs):
    return ('<div class="hero"><h1>Movie Master</h1>'
            '<p>Pick a movie you love, or tell it how you feel. Get picks from around the world, '
            'with the reason behind every one.</p>'
            f'<div class="stats"><div><b>{n_movies:,}</b>movies</div><div><b>{n_langs}</b>languages</div>'
            '<div><b>10</b>moods</div></div></div>')


FOOTER = ('<div class="foot">Built by Athreyan Babu with Python, scikit-learn and Streamlit<br>'
          'Movie data and posters from <a href="https://www.themoviedb.org" target="_blank">TMDB</a> '
          '(via Kaggle datasets), with MPAA ratings from an IMDb-based Kaggle dataset. '
          'This product uses the TMDB API but is not endorsed or certified by TMDB.</div>')
