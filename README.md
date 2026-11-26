# 🎬 Movie Master

A movie recommender with two modes:
- **Similar movies:** pick a movie, get 5 similar ones.
- **By mood:** type how you feel ("I need motivation", "cheer me up"), get 5 movies that match.

**Live demo:** _add your Streamlit link here_

## How it works
- **Data:** TMDB 5000 (4,800 movies: genres, keywords, overview, cast, director, ratings).
- **Similar movies:** content-based filtering. TF-IDF on a combined text profile per movie, ranked by cosine similarity, blended with an IMDb-style weighted rating.
- **Mood search:** 10 mood profiles map trigger words to genres and vibe keywords. Score = 25% genre match + 50% keyword similarity + 25% rating, with a penalty for clashing genres.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```

## Files
- `app.py`: Streamlit web app
- `movie_master.py`: model and recommendation logic
- `Movie_Master.ipynb`: original exploration notebook
- `data/movies.csv`: TMDB 5000 dataset

## Next steps
- Sentence embeddings for free-text moods ("I feel stuck in life")
- Movie posters from the TMDB API
- Offline evaluation against MovieLens user ratings
