from pathlib import Path

import streamlit as st
from movie_master import MovieMaster, MOODS, LANG_NAMES
import ui

st.set_page_config(page_title="Movie Master", page_icon="🎬", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)


@st.cache_resource(show_spinner="Warming up the projector...")
def load_model():
    # Works whether the data sits in data/ or at the top level of the repo
    path = next(p for p in ["data/movies_master.csv.gz", "movies_master.csv.gz"] if Path(p).exists())
    return MovieMaster(path)


model = load_model()


# Cached results: switching toggles or revisiting a movie is instant
@st.cache_data(max_entries=500, show_spinner=False)
def get_similar(label, lang, family, mix):
    return model.similar(label, lang=lang, family_only=family, mix=mix)


@st.cache_data(max_entries=500, show_spinner=False)
def get_twins(i, family):
    return model.twins(i, family_only=family)


@st.cache_data(max_entries=500, show_spinner=False)
def get_mood(text, pill, lang, family, mix):
    return model.by_mood(text, moods=[pill] if pill else None, lang=lang, family_only=family, mix=mix)


st.markdown(ui.hero_html(len(model.df), model.df["original_language"].nunique()), unsafe_allow_html=True)

# ---------------- Global controls ----------------
lang_codes = model.language_options()
counts = model.df["original_language"].value_counts()
lang_opts = [None] + lang_codes
c1, c2, c3 = st.columns([2, 1, 1], vertical_alignment="bottom")
with c1:
    lang = st.selectbox(
        "Language", lang_opts, key="lang",
        format_func=lambda c: "🌍 All languages" if c is None
        else f"{ui.lang_label(c, LANG_NAMES[c])} · {counts[c]:,} films")
with c2:
    mix = st.toggle("🌏 Mix languages", value=True, key="mix", disabled=lang is not None,
                    help="Max 2 films from any one language, so you see world cinema.")
with c3:
    family = st.toggle("👨‍👩‍👧 Family-friendly", key="family",
                       help="G / PG where MPAA ratings exist, plus Family and Animation films.")

tab_similar, tab_mood, tab_how = st.tabs(["🎞️  Similar movies", "🎭  By mood", "⚙️  How it works"])

# ---------------- Similar movies ----------------
with tab_similar:
    default = next((i for i, l in enumerate(model.labels) if l.startswith("The Dark Knight (2008")), 0)
    q = st.text_input("Search a movie", key="movie_q", label_visibility="collapsed",
                      placeholder=f"Search {len(model.df):,} movies, then press Enter: Parasite, 3 Idiots, Baahubali, दंगल...")
    idx = default
    if q.strip():
        matches = model.search(q)
        if matches:
            picked = st.pills("Matches", matches, format_func=lambda i: model.labels[i], default=matches[0],
                              key=f"pick_{q}", label_visibility="collapsed")
            idx = matches[0] if picked is None else picked
        else:
            st.caption("No movie found with that name. Check the spelling or try fewer letters.")
            idx = None
    else:
        st.caption("Showing The Dark Knight. Type any title, in English or its original script, and press Enter.")
    i, results = get_similar(model.labels[idx], lang, family, mix) if idx is not None else (None, None)
    if results is not None:
        st.markdown(ui.seed_html(model.df.loc[i]), unsafe_allow_html=True)
        where = f" in {LANG_NAMES[lang]}" if lang else ""
        st.markdown(f'<div class="section">Because you liked this, try <span>these{where}</span></div>'
                    '<p class="subsection">Each pick shows why it matched.</p>', unsafe_allow_html=True)
        if len(results):
            st.markdown(ui.cards_html(results), unsafe_allow_html=True)
        else:
            st.caption("No matches with these filters. Try another language or turn off Family-friendly.")

        twins = get_twins(i, family)
        if len(twins):
            st.markdown('<div class="section">Same vibe, <span>another language</span></div>'
                        '<p class="subsection">The closest match to your movie in other film industries. '
                        'Languages without a convincing match are skipped.</p>', unsafe_allow_html=True)
            st.markdown(ui.twins_html(twins), unsafe_allow_html=True)


# ---------------- By mood ----------------
def _typed():          # typing clears the chip, so the latest input wins
    st.session_state["mood_pill"] = None


def _picked():         # picking a chip clears the text box
    st.session_state["mood_text"] = ""


with tab_mood:
    st.text_input("What are you in the mood for?", key="mood_text", on_change=_typed,
                  placeholder="Try: I need motivation · had a bad day · something scary",
                  label_visibility="collapsed")
    pill = st.pills("Or pick a vibe", list(MOODS), key="mood_pill", on_change=_picked,
                    format_func=lambda k: f"{MOODS[k]['emoji']} {MOODS[k]['label']}", selection_mode="single")
    text = st.session_state.get("mood_text", "").strip()

    if pill or text:
        moods, results = get_mood(text, pill, lang, family, mix)
        where = f" in {LANG_NAMES[lang]}" if lang else ""
        if moods:
            label = " + ".join(f"{MOODS[m]['emoji']} {MOODS[m]['label']}" for m in moods)
            st.markdown(f'<div class="section">Your vibe: <span>{label}</span>{where}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="section">No mood matched, so these fit <span>your words</span>{where}</div>',
                        unsafe_allow_html=True)
        if not moods and not len(results):
            st.info("Couldn't match those words to any movie. Try words like 'motivation', 'funny', 'scary' or 'romantic'.")
        elif len(results):
            st.markdown(ui.cards_html(results), unsafe_allow_html=True)
        if 0 < len(results) < 5:
            st.caption("Only a few films fit this mood with your filters. Try another language or turn off Family-friendly.")
    else:
        st.caption("Type how you feel and press Enter, or tap a vibe. Pick a language above for Hindi, Tamil, Korean and more.")


# ---------------- How it works ----------------
with tab_how:
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown(f"""
#### 🎞️ Similar movies
Content-based filtering on **{len(model.df):,} movies in {model.df['original_language'].nunique()} languages** (TMDB).

1. Each movie becomes a profile: genres, theme keywords, plot, tagline, director, writers, composer, cast.
2. **TF-IDF** turns profiles into vectors. Tone tags ("intense") and places ("Paris") count less than real themes.
3. **Cosine similarity** ranks every movie against your pick, nudged by rating.
4. **Same vibe, another language:** the closest match in each film industry, shown only when it shares a genre and clears a similarity bar.
5. **Why this pick:** shared director, writer, cast or the rarest shared themes.
""")
    with b:
        st.markdown("""
#### 🎭 Mood search
1. Your words map to **10 mood profiles**: trigger words, genres, genres to avoid, TMDB theme and tone tags.
2. Score = 25% genre fit + 50% keyword similarity + 25% rating, with penalties for clashing genres.

#### ⚖️ Fair across languages
A Malayalam film rated 8.0 from 300 votes and an English film rated 8.0 from 30,000 votes are both strong. Ratings are weighted against each language's own vote levels, and popularity thresholds are set per language.

**Stack:** Python · pandas · scikit-learn · Streamlit
""")

st.markdown(ui.FOOTER, unsafe_allow_html=True)
