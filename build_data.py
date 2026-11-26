"""
Builds data/movies_master.csv from the raw datasets in data/raw/. Run after changing raw data:
    python build_data.py

Base:
  movies_global.csv   23,241 movies in 100+ languages, filtered from Kaggle's Full TMDB Movies
                      Dataset 2024 (asaniczka). Plot, keywords, genres, votes, posters.
Enrichment (joined on TMDB id, or title + year for the IMDb file):
  tmdb_movies.csv     TMDB 5000: director, writers, composer from the crew column
  movies2024.csv      directors and top cast for ~7,600 popular movies
  movies_updated.csv  IMDb-based, 1980-2001: MPAA rating, IMDb score and votes
"""
import ast
import re
import unicodedata
from pathlib import Path

import pandas as pd

RAW = Path(__file__).parent / "data" / "raw"
OUT = Path(__file__).parent / "data" / "movies_master.csv"


def norm_title(t):
    t = unicodedata.normalize("NFKD", str(t)).encode("ascii", "ignore").decode().lower()
    t = re.sub(r"^(the|a|an) ", "", t).replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", t)


def unescape(s):
    s = str(s)
    return re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s) if "\\u" in s else s


def crew_people(crew, jobs, limit=3):
    try:
        items = ast.literal_eval(crew)
    except (ValueError, SyntaxError):
        return ""
    names = []
    for i in items:
        if i.get("job") in jobs and i["name"] not in names:
            names.append(unescape(i["name"]))
    return "|".join(names[:limit])


def comma_to_pipe(s, limit=None):
    if pd.isna(s) or not str(s).strip():
        return ""
    parts = list(dict.fromkeys(p.strip() for p in str(s).split(",") if p.strip()))
    return "|".join(parts[:limit] if limit else parts)


def main():
    g = pd.read_csv(RAW / "movies_global.csv")
    g = g.drop_duplicates("id")
    g["year"] = pd.to_datetime(g["release_date"], errors="coerce").dt.year
    g["genres"] = g["genres"].map(comma_to_pipe)
    g["keywords"] = g["keywords"].map(comma_to_pipe)
    for col in ["tagline", "poster_path"]:
        g[col] = g[col].fillna("")

    # People from TMDB 5000 crew (most reliable), then movies2024 for gaps
    t = pd.read_csv(RAW / "tmdb_movies.csv", low_memory=False)
    t = t[t["id"].isin(g["id"])]
    crew = pd.DataFrame({
        "id": t["id"],
        "director_a": t["crew"].map(lambda c: crew_people(c, {"Director"}, limit=2)),
        "writers": t["crew"].map(lambda c: crew_people(c, {"Screenplay", "Writer", "Novel", "Story"})),
        "composer": t["crew"].map(lambda c: crew_people(c, {"Original Music Composer", "Music"}, limit=1)),
    })
    m24 = pd.read_csv(RAW / "movies2024.csv").drop_duplicates("MovieID")
    m24 = pd.DataFrame({"id": m24["MovieID"],
                        "director_b": m24["Directors"].map(lambda s: comma_to_pipe(s, 2)),
                        "cast": m24["Actors"].map(lambda s: comma_to_pipe(s, 5))})
    g = g.merge(crew, on="id", how="left").merge(m24, on="id", how="left")
    g["director"] = g["director_a"].where(g["director_a"].fillna("") != "", g["director_b"]).fillna("")
    for col in ["writers", "composer", "cast"]:
        g[col] = g[col].fillna("")

    # MPAA + IMDb score from the IMDb-based file, matched on title + year within 1
    imdb = pd.read_csv(RAW / "movies_updated.csv")
    imdb["key"] = imdb["name"].map(norm_title)
    g["key"] = g["title"].map(norm_title)
    imdb = imdb.rename(columns={"year": "imdb_year", "rating": "mpaa", "score": "imdb_score", "votes": "imdb_votes"})
    mm = g[["id", "key", "year"]].merge(imdb[["key", "imdb_year", "mpaa", "imdb_score", "imdb_votes"]], on="key")
    mm = mm[(mm["year"] - mm["imdb_year"]).abs() <= 1].drop_duplicates("id")
    g = g.merge(mm[["id", "mpaa", "imdb_score", "imdb_votes"]], on="id", how="left")
    g["mpaa"] = g["mpaa"].fillna("")

    keep = ["id", "imdb_id", "title", "original_title", "original_language", "year", "genres", "keywords",
            "overview", "tagline", "director", "writers", "composer", "cast", "runtime", "vote_average",
            "vote_count", "popularity", "poster_path", "mpaa", "imdb_score", "imdb_votes"]
    g = g[keep].sort_values("vote_count", ascending=False)
    g.to_csv(OUT, index=False)

    print(f"Saved {len(g):,} movies to {OUT.name} ({OUT.stat().st_size / 1e6:.1f} MB)")
    print(f"  languages: {g['original_language'].nunique()}, non-English films: {(g['original_language'] != 'en').sum():,}")
    print(f"  with director: {(g['director'] != '').sum():,} | with cast: {(g['cast'] != '').sum():,}")
    print(f"  with keywords: {(g['keywords'] != '').sum():,} | with MPAA: {(g['mpaa'] != '').sum():,}")


if __name__ == "__main__":
    main()
