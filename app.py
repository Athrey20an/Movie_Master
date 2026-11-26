import streamlit as st
from movie_master import MovieMaster, MOODS

st.set_page_config(page_title="Movie Master", page_icon="🎬", layout="centered")


@st.cache_resource(show_spinner="Loading 4,800 movies...")
def load_model():
    return MovieMaster("data/movies.csv")


model = load_model()


def show_results(results):
    for _, r in results.iterrows():
        with st.container(border=True):
            year = f" ({r['year']})" if str(r["year"]) != "<NA>" else ""
            st.markdown(f"### {r['title']}{year}")
            st.caption(f"⭐ {r['vote_average']}/10 · {int(r['vote_count']):,} votes · {r['genres']} · Dir. {r['director']}")
            if r["overview"]:
                st.write(r["overview"])


st.title("🎬 Movie Master")
st.write("Find 5 movies like one you love, or tell it how you feel and get 5 picks that match the mood.")

tab1, tab2, tab3 = st.tabs(["Similar movies", "By mood", "How it works"])

with tab1:
    titles = sorted(model.df["title"].tolist())
    default = titles.index("The Dark Knight") if "The Dark Knight" in titles else 0
    movie = st.selectbox("Pick a movie you like", titles, index=default)
    if st.button("Find similar movies", type="primary"):
        found, results = model.similar(movie)
        st.subheader(f"Because you liked {found}")
        show_results(results)

with tab2:
    text = st.text_input("How are you feeling, or what do you need?", placeholder="e.g. I need motivation")
    go = st.button("Get recommendations", type="primary")
    st.write("Or pick one:")
    cols = st.columns(5)
    clicked = None
    for i, (key, p) in enumerate(MOODS.items()):
        if cols[i % 5].button(f"{p['emoji']} {p['label']}", key=f"mood_{key}", use_container_width=True):
            clicked = key

    if clicked or (go and text.strip()):
        if clicked:
            moods, results = model.by_mood("", moods=[clicked])
        else:
            moods, results = model.by_mood(text)
        if moods:
            st.success("Detected mood: " + ", ".join(f"{MOODS[m]['emoji']} {MOODS[m]['label']}" for m in moods))
        else:
            st.info("No mood detected, so these match your words directly. Try words like 'motivation', 'funny' or 'scary'.")
        show_results(results)

with tab3:
    st.markdown("""
**Data:** TMDB 5000 dataset, 4,800 movies with genres, keywords, plot overview, cast and director.

**Similar movies (content-based filtering):**
1. Each movie becomes one text profile: genres (weighted 3x), keywords, overview, director (2x), cast.
2. TF-IDF turns profiles into vectors (4,800 x 30,680).
3. Cosine similarity ranks every movie against the one you picked.
4. Final score = 85% similarity + 15% IMDb-style weighted rating. Movies under 50 votes are skipped.

**Mood search:**
1. Your text is matched against 10 mood profiles (trigger words, target genres, genres to avoid, vibe keywords).
2. Score = 25% genre match + 50% keyword similarity + 25% rating, minus a penalty for clashing genres.
3. Only movies with 300+ votes are shown, so picks are well known.

Built with Python, pandas, scikit-learn and Streamlit.
""")
