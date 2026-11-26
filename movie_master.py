"""Movie Master core: data cleaning, TF-IDF model, similar-movie and mood recommendations."""
import re
import difflib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

GENRES = ["Science Fiction", "TV Movie", "Action", "Adventure", "Animation", "Comedy", "Crime",
          "Documentary", "Drama", "Family", "Fantasy", "Foreign", "History", "Horror", "Music",
          "Mystery", "Romance", "Thriller", "War", "Western"]
GENRE_RE = re.compile("|".join(GENRES))

# Triggers are matched as substrings, so use word stems: "motivat" matches motivate/motivation/motivated
MOODS = {
    "motivated": {
        "label": "Motivated", "emoji": "💪",
        "triggers": ["motivat", "inspir", "push", "hustle", "grind", "discipline", "productive",
                     "give up", "lazy", "ambition", "succeed", "success", "goal"],
        "genres": ["Drama"],
        "avoid": ["Horror", "Animation", "War"],
        "keywords": "sport sports underdog boxing boxer coach football basketball training team "
                    "competition champion comeback perseverance dream success ambition inspiration",
    },
    "happy": {
        "label": "Cheer me up", "emoji": "😊",
        "triggers": ["happy", "cheer", "feel good", "feel-good", "uplift", "smile", "bad day",
                     "down", "low", "wholesome", "light"],
        "genres": ["Comedy", "Family", "Animation"],
        "avoid": ["Horror", "Crime", "War", "Thriller"],
        "keywords": "friendship family heartwarming fun kindness joy feel good",
    },
    "laugh": {
        "label": "Make me laugh", "emoji": "😂",
        "triggers": ["laugh", "funny", "comedy", "hilarious", "silly"],
        "genres": ["Comedy"],
        "avoid": ["Horror", "War"],
        "keywords": "friends party chaos parody slapstick buddy",
    },
    "romantic": {
        "label": "Romantic", "emoji": "❤️",
        "triggers": ["romant", "love", "date night", "crush", "relationship"],
        "genres": ["Romance"],
        "avoid": ["Horror", "War"],
        "keywords": "love romance relationship couple falling in love wedding",
    },
    "thrilled": {
        "label": "Edge of my seat", "emoji": "🔍",
        "triggers": ["thrill", "suspense", "edge of", "tense", "mystery", "twist", "mind"],
        "genres": ["Thriller", "Mystery", "Crime"],
        "avoid": ["Family", "Animation"],
        "keywords": "twist suspense detective investigation serial killer conspiracy",
    },
    "scared": {
        "label": "Scare me", "emoji": "👻",
        "triggers": ["scare", "scary", "horror", "spooky", "creepy", "fright"],
        "genres": ["Horror"],
        "avoid": ["Family", "Comedy", "Animation"],
        "keywords": "haunted house ghost demon possession supernatural monster",
    },
    "adrenaline": {
        "label": "Adrenaline", "emoji": "💥",
        "triggers": ["action", "adrenaline", "pumped", "hype", "energy", "explosive", "fight"],
        "genres": ["Action", "Adventure"],
        "avoid": ["Romance", "Documentary"],
        "keywords": "fight chase revenge mission explosion hero battle",
    },
    "thoughtful": {
        "label": "Make me think", "emoji": "🧠",
        "triggers": ["think", "deep", "philosoph", "smart", "reflect", "existential", "curious"],
        "genres": ["Science Fiction", "Drama", "Mystery"],
        "avoid": ["Comedy", "Family"],
        "keywords": "reality identity memory time travel artificial intelligence dystopia existence",
    },
    "emotional": {
        "label": "Good cry", "emoji": "😢",
        "triggers": ["cry", "emotional", "tearjerker", "sad movie", "grief", "heartbreak"],
        "genres": ["Drama", "Romance"],
        "avoid": ["Horror", "Action", "Comedy"],
        "keywords": "grief loss death love family sacrifice terminal illness",
    },
    "adventurous": {
        "label": "Adventure", "emoji": "🗺️",
        "triggers": ["adventure", "travel", "explore", "escape", "wanderlust", "journey", "fantasy"],
        "genres": ["Adventure", "Fantasy"],
        "avoid": ["Horror"],
        "keywords": "journey quest travel exploration magic treasure self discovery",
    },
}


def _squash(name):
    return name.replace(" ", "").lower()


class MovieMaster:
    def __init__(self, csv_path):
        df = pd.read_csv(csv_path, low_memory=False)
        for col in ["genres", "keywords", "overview", "tagline", "cast", "director"]:
            df[col] = df[col].fillna("")
        df["genre_list"] = df["genres"].apply(lambda s: GENRE_RE.findall(str(s)))
        df["year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year.astype("Int64")
        df = df.drop_duplicates("title").reset_index(drop=True)

        # IMDb weighted rating, scaled 0-1
        C, m = df["vote_average"].mean(), df["vote_count"].quantile(0.60)
        v, R = df["vote_count"], df["vote_average"]
        wr = (v / (v + m)) * R + (m / (v + m)) * C
        df["quality"] = (wr - wr.min()) / (wr.max() - wr.min())

        soup = (
            df["genre_list"].apply(lambda g: " ".join(_squash(x) for x in g) + " ") * 3
            + df["keywords"].str.lower() + " "
            + df["overview"].str.lower() + " "
            + (df["director"].apply(_squash) + " ") * 2
            + df["cast"].str.lower()
        )
        self.tfidf = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), min_df=2, max_features=50000)
        self.matrix = self.tfidf.fit_transform(soup)
        self.genre_sets = df["genre_list"].apply(set)
        self.df = df
        self.titles_lower = df["title"].str.lower().tolist()

    def find_title(self, name):
        name = name.lower().strip()
        if name in self.titles_lower:
            return self.titles_lower.index(name)
        match = difflib.get_close_matches(name, self.titles_lower, n=1, cutoff=0.6)
        return self.titles_lower.index(match[0]) if match else None

    def _result(self, idx, score):
        out = self.df.loc[idx, ["title", "year", "genres", "vote_average", "vote_count", "overview", "director"]].copy()
        out["score"] = score[idx].round(3)
        return out.reset_index(drop=True)

    def similar(self, name, n=5, min_votes=50):
        i = self.find_title(name)
        if i is None:
            return None, None
        sims = cosine_similarity(self.matrix[i], self.matrix).ravel()
        score = 0.85 * sims + 0.15 * self.df["quality"].values
        score[self.df["vote_count"].values < min_votes] = -1
        score[i] = -1
        top = np.argsort(score)[::-1][:n]
        return self.df.loc[i, "title"], self._result(top, score)

    def detect_moods(self, text):
        text = text.lower()
        hits = {m: sum(t in text for t in p["triggers"]) for m, p in MOODS.items()}
        hits = {m: h for m, h in hits.items() if h}
        return sorted(hits, key=hits.get, reverse=True)[:2]

    def by_mood(self, text, n=5, min_votes=300, moods=None):
        moods = moods if moods is not None else self.detect_moods(text)
        query = " ".join(MOODS[m]["keywords"] for m in moods) if moods else text
        want = set().union(*[MOODS[m]["genres"] for m in moods]) if moods else set()
        avoid = set().union(*[MOODS[m]["avoid"] for m in moods]) if moods else set()

        kw = cosine_similarity(self.tfidf.transform([query.lower()]), self.matrix).ravel()
        kw = kw / kw.max() if kw.max() > 0 else kw
        genre = self.genre_sets.apply(lambda g: len(g & want) / len(want) if want else 0).values
        penalty = self.genre_sets.apply(lambda g: 0.5 if g & avoid else 0).values

        score = 0.25 * genre + 0.50 * kw + 0.25 * self.df["quality"].values - penalty
        score[self.df["vote_count"].values < min_votes] = -1
        top = np.argsort(score)[::-1][:n]
        return moods, self._result(top, score)
