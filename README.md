# 🎬 Movie Master

A multilingual movie recommender: **23,241 movies in 86 languages**, with mood search and a reason behind every pick.

**Live demo:** https://movie-master.streamlit.app/

## What it does
- **Similar movies:** pick a movie, get 5 similar ones, each with a "why this pick" (same director, shared themes...).
- **Same vibe, another language:** the closest match to your movie in English, Hindi, Tamil, Korean, Japanese, French and Spanish cinema.
- **Mood search:** type how you feel ("I need motivation", "cheer me up") or tap one of 10 moods.
- **Language filter:** Hindi, Tamil, Malayalam, Telugu, Korean, Japanese, Arabic and 20+ more, with original titles shown.
- **Family-friendly filter:** G/PG titles plus Family and Animation films.

Example: *Motivated + Hindi* returns Mary Kom, Dangal, Chak De! India and M.S. Dhoni: The Untold Story.

## How it works
- **Content-based filtering:** each movie becomes a profile of genres, TMDB theme keywords, plot, tagline, director, writers, composer and cast. TF-IDF vectors are ranked by cosine similarity, with rating as a multiplier.
- **Signal weighting:** theme keywords count double. TMDB tone tags ("intense") and place names ("Paris") count once, because they are weak evidence that two films are alike.
- **Fair across languages:** weighted ratings use each language's own vote levels, and popularity thresholds are set per language, so a strong Malayalam film isn't buried under English films with 100x the votes.
- **Explanations:** shared director, writer or cast, then the rarest shared themes (highest IDF).
- **Cross-language twins:** shown only when the match shares a genre and clears a similarity threshold.
- **Mood search:** 10 profiles of trigger words, genres, genres to avoid and TMDB keywords. Score = 25% genre fit + 50% keyword similarity + 25% rating, with penalties for clashing genres.

## Data
| File | Source | Used for |
|---|---|---|
| `data/raw/movies_global.csv` | Kaggle: Full TMDB Movies Dataset 2024 (asaniczka), filtered | Base: 23,241 movies, plot, keywords, posters |
| `data/raw/tmdb_movies.csv` | Kaggle: TMDB 5000 | Director, writers, composer |
| `data/raw/movies2024.csv` | Kaggle | Directors and cast |
| `data/raw/movies_updated.csv` | Kaggle: IMDb-based, 1980-2001 | MPAA ratings, IMDb scores |

Filter used on the 1.5M-row TMDB dataset: released, non-adult, has overview and genres; English films with 200+ votes, other languages with 30+ votes.

`build_data.py` merges everything into `data/movies_master.csv` (joined on TMDB id; the IMDb file on normalised title + year).

## Run locally
```
pip install -r requirements.txt
python build_data.py      # only if you change files in data/raw/
streamlit run app.py
```

## Files
- `app.py`: Streamlit app
- `ui.py`: styling and card layout
- `movie_master.py`: recommender, mood search, explanations
- `build_data.py`: data merge and cleaning
- `Movie_Master.ipynb`: original exploration notebook

## Limitations
- Director and cast data covers 31% of films (mostly popular English titles), so many international films are matched on genres, keywords and plot only.
- MPAA ratings exist for about 2,000 films, so the family filter leans on genres for the rest.
- Release dates run to September 2023.

## Next steps
- Where to watch in the UAE (TMDB watch providers)
- Multilingual sentence embeddings so moods can be typed in Hindi or Arabic
- Offline evaluation with MovieLens ratings

Movie data and posters from TMDB. This product uses the TMDB API but is not endorsed or certified by TMDB.
