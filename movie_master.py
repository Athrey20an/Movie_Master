"""Movie Master core: multilingual content-based recommender with mood search and explanations."""
import difflib
import re
import unicodedata

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

LANG_NAMES = {
    "en": "English", "hi": "Hindi", "ta": "Tamil", "ml": "Malayalam", "te": "Telugu", "kn": "Kannada",
    "bn": "Bengali", "ko": "Korean", "ja": "Japanese", "zh": "Mandarin", "cn": "Cantonese", "fr": "French",
    "es": "Spanish", "it": "Italian", "de": "German", "pt": "Portuguese", "ru": "Russian", "tr": "Turkish",
    "ar": "Arabic", "fa": "Persian", "he": "Hebrew", "th": "Thai", "id": "Indonesian", "pl": "Polish",
    "sv": "Swedish", "da": "Danish", "no": "Norwegian", "nl": "Dutch", "fi": "Finnish", "cs": "Czech",
    "hu": "Hungarian", "ro": "Romanian", "el": "Greek", "xx": "No dialogue",
}
FLAGS = {"en": "🇺🇸", "hi": "🇮🇳", "ta": "🇮🇳", "ml": "🇮🇳", "te": "🇮🇳", "ko": "🇰🇷", "ja": "🇯🇵",
         "zh": "🇨🇳", "cn": "🇭🇰", "fr": "🇫🇷", "es": "🇪🇸", "it": "🇮🇹", "de": "🇩🇪", "pt": "🇧🇷",
         "ru": "🇷🇺", "tr": "🇹🇷", "ar": "🇸🇦", "fa": "🇮🇷", "th": "🇹🇭"}
TWIN_LANGS = ["en", "hi", "ta", "ko", "ja", "fr", "es"]   # "same vibe, another language" picks 6 of these

# Mood keywords are TMDB keyword phrases (comma-separated); triggers are word stems
MOODS = {
    "motivated": {
        "label": "Motivated", "emoji": "💪",
        "triggers": ["motivat", "inspir", "push", "hustle", "grind", "discipline", "productive",
                     "give up", "lazy", "ambition", "succeed", "success", "goal"],
        "genres": ["Drama"],
        "avoid": ["Horror", "Animation", "War"],
        "keywords": "sports, underdog, boxing, coach, football, basketball, training, competition, "
                    "champion, comeback, perseverance, dream, ambition, inspirational, based on true story, "
                    "biography, overcoming adversity, determination",
    },
    "happy": {
        "label": "Cheer me up", "emoji": "😊",
        "triggers": ["happy", "cheer", "feel good", "feel-good", "uplift", "smile", "bad day",
                     "down", "low", "wholesome", "light"],
        "genres": ["Comedy", "Family", "Animation"],
        "avoid": ["Horror", "Crime", "War", "Thriller"],
        "avoid_mpaa": ["R", "NC-17", "X"],
        "keywords": "friendship, family, heartwarming, feel-good, joyful, cheerful, kindness, wholesome, "
                    "lighthearted, playful, hopeful",
    },
    "laugh": {
        "label": "Make me laugh", "emoji": "😂",
        "triggers": ["laugh", "funny", "comedy", "hilarious", "silly"],
        "genres": ["Comedy"],
        "avoid": ["Horror", "War"],
        "keywords": "hilarious, slapstick, parody, buddy comedy, absurd, satire, spoof, comedic, witty, "
                    "amused, mischief",
    },
    "romantic": {
        "label": "Romantic", "emoji": "❤️",
        "triggers": ["romant", "love", "date night", "crush", "relationship"],
        "genres": ["Romance"],
        "avoid": ["Horror", "War"],
        "keywords": "love, romance, falling in love, romantic, wedding, couple, love triangle, first love, "
                    "romantic comedy",
    },
    "thrilled": {
        "label": "Edge of my seat", "emoji": "🔍",
        "triggers": ["thrill", "suspense", "edge of", "tense", "mystery", "twist", "mind"],
        "genres": ["Thriller", "Mystery", "Crime"],
        "avoid": ["Family", "Animation"],
        "keywords": "twist ending, suspense, detective, investigation, serial killer, conspiracy, "
                    "psychological thriller, murder, whodunit, suspenseful, tense",
    },
    "scared": {
        "label": "Scare me", "emoji": "👻",
        "triggers": ["scare", "scary", "horror", "spooky", "creepy", "fright"],
        "genres": ["Horror"],
        "avoid": ["Family", "Comedy", "Animation"],
        "keywords": "haunted house, ghost, demon, possession, supernatural, monster, paranormal, "
                    "exorcism, curse, creepy, frightening",
    },
    "adrenaline": {
        "label": "Adrenaline", "emoji": "💥",
        "triggers": ["action", "adrenaline", "pumped", "hype", "energy", "explosive", "fight"],
        "genres": ["Action", "Adventure"],
        "avoid": ["Romance", "Documentary"],
        "keywords": "martial arts, fight, chase, revenge, mission, explosion, hero, shootout, car chase, "
                    "one man army, exciting",
    },
    "thoughtful": {
        "label": "Make me think", "emoji": "🧠",
        "triggers": ["think", "deep", "philosoph", "smart", "reflect", "existential", "curious"],
        "genres": ["Science Fiction", "Drama", "Mystery"],
        "avoid": ["Comedy", "Family"],
        "keywords": "philosophy, artificial intelligence (a.i.), dystopia, time travel, memory, identity, "
                    "existentialism, reality, thoughtful, complicated, mind-bending",
    },
    "emotional": {
        "label": "Good cry", "emoji": "😢",
        "triggers": ["cry", "emotional", "tearjerker", "sad movie", "grief", "heartbreak"],
        "genres": ["Drama", "Romance"],
        "avoid": ["Horror", "Action", "Comedy"],
        "keywords": "grief, loss of loved one, death, terminal illness, sacrifice, tragedy, melancholy, "
                    "sad, tearjerker, heartbreak, father son relationship",
    },
    "adventurous": {
        "label": "Adventure", "emoji": "🗺️",
        "triggers": ["adventure", "travel", "explore", "escape", "wanderlust", "journey", "fantasy"],
        "genres": ["Adventure", "Fantasy"],
        "avoid": ["Horror"],
        "keywords": "journey, quest, road trip, exploration, magic, treasure hunt, self-discovery, "
                    "travel, wilderness, epic",
    },
}


# TMDB's tone/mood tags: useful for mood search, misleading as "shared themes" between two films
TONES = set("""admiring amused amazed angry anxious apathetic approving assertive audacious awestruck
baffled bold callous cautionary celebratory cheerful comforting compassionate complicated critical
cruel defiant demeaning depressing desperate didactic disgusted dramatic earnest embarrassed empathetic
enchanting enthusiastic exhilarated excited factual familiar frantic frightened harsh hopeful horrified
hilarious informative inspirational intense joyful joyous lighthearted melancholy mischievous ominous
optimistic playful powerful provocative reflective sad sentimental serious sincere somber straightforward
suspenseful sympathetic tense thoughtful tragic vibrant witty whimsical wry absurd ambiguous aggressive
awkward distressing exciting curious romantic comedic cheerful feel-good wholesome mind-bending
grim bleak uplifting heartwarming""".split()) | {"mean spirited", "feel good"}

# Places: weak evidence that two films are alike, so they count less and are shown last
PLACES = set("""usa america england britain uk london paris france germany berlin italy rome spain madrid
japan tokyo china beijing shanghai hong kong korea seoul india mumbai delhi chennai russia moscow mexico
canada australia brazil ireland scotland egypt israel iran turkey istanbul greece thailand vietnam
california texas florida new york city manhattan brooklyn los angeles las vegas chicago san francisco
new orleans boston washington d.c. hawaii alaska new jersey montmartre venice sicily naples
barcelona amsterdam vienna prague poland sweden norway denmark finland africa europe asia""".split("\n"))
PLACES = {w.strip() for line in PLACES for w in line.split()} | {
    "new york city", "los angeles", "san francisco", "hong kong", "south korea", "north korea",
    "las vegas", "new orleans", "washington d.c.", "new jersey", "united kingdom", "soviet union",
    "east germany", "west germany", "new york", "south africa", "latin america"}
# Never shown in explanations on a public page (still used for matching)
HIDE_IN_WHY = {"incest", "rape", "urination", "sadism", "nudity", "sex", "erotic", "pornography",
               "masturbation", "prostitute", "prostitution", "duringcreditsstinger", "aftercreditsstinger",
               "woman director", "based on novel or book", "voiceover", "sequel", "remake"}


def _fold(s):
    """Accent-free, lowercase, doubled letters collapsed: 'Bāhubali' and 'Baahubali' both -> 'bahubali'."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"[^a-z0-9]", "", s)          # "K.G.F" -> "kgf", "3 Idiots" -> "3idiots"
    return re.sub(r"(.)\1+", r"\1", s)


def _squash(s):
    return re.sub(r"\W+", "", str(s).lower())


def _kw_token(phrase):
    p = phrase.strip().lower()
    return ("t_" if p in TONES else "k_") + re.sub(r"\W+", "_", p).strip("_")


def _split(s):
    return [p for p in str(s).split("|") if p] if isinstance(s, str) else []


class MovieMaster:
    TWIN_MIN_SIM = 0.10   # below this, a cross-language "twin" isn't convincing, so we skip that language

    def __init__(self, csv_path):
        df = pd.read_csv(csv_path, low_memory=False)
        for col in ["genres", "keywords", "overview", "tagline", "director", "writers", "composer",
                    "cast", "mpaa", "poster_path", "original_title"]:
            df[col] = df[col].fillna("")
        df["year"] = df["year"].astype("Int64")
        df["genre_list"] = df["genres"].map(_split)
        df["kw_list"] = df["keywords"].map(_split)
        df["lang"] = df["original_language"].map(lambda c: LANG_NAMES.get(c, c.upper()))
        df = df.reset_index(drop=True)

        df["quality"] = self._quality(df)
        # Popularity within its own language (0-1), so thresholds are fair to smaller film industries
        df["lang_rank"] = df.groupby("original_language")["vote_count"].rank(pct=True)
        df["family_ok"] = df["mpaa"].isin(["G", "PG"]) | (
            (df["mpaa"] == "") & df["genre_list"].map(lambda g: bool({"Family", "Animation"} & set(g))))

        self.df = df
        self.genre_sets = df["genre_list"].map(set)
        self.kw_sets = df["kw_list"].map(lambda k: {x.lower() for x in k})
        self._build_matrix()

        # Search labels: "Title (year)", made unique where titles repeat
        labels = df["title"] + " (" + df["year"].astype(str).str.replace("<NA>", "n.d.") + ")"
        dup = labels.duplicated(keep=False)
        labels[dup] = labels[dup] + " · " + df.loc[dup, "lang"]
        self.labels = labels.tolist()
        self.label_index = {l: i for i, l in enumerate(self.labels)}
        self.titles_lower = df["title"].str.lower().tolist()
        self._t_lower = df["title"].str.lower()
        self._o_lower = df["original_title"].str.lower()
        self._f_lower = df["title"].map(_fold)

    # ------------------------------------------------------------------ setup
    @staticmethod
    def _quality(df):
        """Weighted rating with a per-language vote threshold, blended with IMDb where available."""
        C = df["vote_average"].mean()
        m = df.groupby("original_language")["vote_count"].transform(lambda v: v.quantile(0.5))
        v, R = df["vote_count"], df["vote_average"]
        wr = (v / (v + m)) * R + (m / (v + m)) * C
        has = df["imdb_score"].notna()
        if has.any():
            iv, iR = df.loc[has, "imdb_votes"], df.loc[has, "imdb_score"]
            im = iv.quantile(0.6)
            wr[has] = 0.5 * wr[has] + 0.5 * ((iv / (iv + im)) * iR + (im / (iv + im)) * iR.mean())
        return (wr - wr.min()) / (wr.max() - wr.min())

    def _build_matrix(self):
        df = self.df
        people = lambda col, prefix="p_": df[col].map(lambda s: " ".join(prefix + _squash(n) for n in _split(s)))
        soup = (
            df["genre_list"].map(lambda g: " ".join("g_" + _squash(x) for x in g) + " ") * 3
            + df["kw_list"].map(lambda k: " ".join(_kw_token(x) for x in k if x.lower() not in TONES | PLACES) + " ") * 2
            + df["kw_list"].map(lambda k: " ".join(_kw_token(x) for x in k if x.lower() in TONES | PLACES) + " ")
            + df["overview"].str.lower() + " " + df["tagline"].str.lower() + " "
            + (people("director") + " ") * 2
            + people("writers") + " " + people("composer") + " " + people("cast")
        )
        self.tfidf = TfidfVectorizer(stop_words="english", token_pattern=r"(?u)\b\w\w+\b",
                                     min_df=2, max_features=80000, sublinear_tf=True)
        self.matrix = self.tfidf.fit_transform(soup)
        self.idf = dict(zip(self.tfidf.get_feature_names_out(), self.tfidf.idf_))

    # ---------------------------------------------------------------- helpers
    def find(self, name):
        """Index from a search label or a typed title (typos allowed)."""
        if name in self.label_index:
            return self.label_index[name]
        name = name.lower().strip()
        if name in self.titles_lower:
            return self.titles_lower.index(name)
        match = difflib.get_close_matches(name, self.titles_lower, n=1, cutoff=0.6)
        return self.titles_lower.index(match[0]) if match else None

    def search(self, query, n=8):
        """Top title matches for a search box: substring match on English and original titles,
        titles that start with the query first, then by popularity. Falls back to fuzzy matching."""
        q = query.lower().strip()
        if not q:
            return []
        t, o = self._t_lower, self._o_lower
        exact = t.str.contains(q, regex=False) | o.str.contains(q, regex=False)
        fq = _fold(q)
        folded = self._f_lower.str.contains(fq, regex=False) if len(fq) >= 3 else exact & False
        hit = exact | folded
        if hit.any():
            starts = t.str.startswith(q) | o.str.startswith(q)
            if len(fq) >= 3:
                starts |= self._f_lower.str.startswith(fq)
            full = (t == q) | (o == q) | ((self._f_lower == fq) if len(fq) >= 3 else False)
            cand = pd.DataFrame({"full": full[hit], "starts": starts[hit], "votes": self.df.loc[hit, "vote_count"]})
            return cand.sort_values(["full", "starts", "votes"], ascending=False).index[:n].tolist()
        if len(q) >= 3:   # typo fallback, limited to the 8,000 most-voted titles for speed
            pool = self.titles_lower[:8000]
            close = difflib.get_close_matches(q, pool, n=n, cutoff=0.6)
            return [pool.index(c) for c in close]
        return []

    def language_options(self, min_films=40):
        counts = self.df["original_language"].value_counts()
        return [c for c in counts.index if counts[c] >= min_films and c in LANG_NAMES and c != "xx"]

    def _mask(self, lang=None, family_only=False, min_rank=0.0):
        ok = self.df["lang_rank"].values >= min_rank
        if lang:
            ok &= self.df["original_language"].values == lang
        if family_only:
            ok &= self.df["family_ok"].values
        return ok

    @staticmethod
    def _pick(score, ok, n, langs=None, per_lang_cap=None):
        order = np.argsort(np.where(ok, score, -np.inf))[::-1]
        picked, seen = [], {}
        for i in order:
            if not ok[i] or len(picked) == n:
                break
            if per_lang_cap:
                l = langs[i]
                if seen.get(l, 0) >= per_lang_cap:
                    continue
                seen[l] = seen.get(l, 0) + 1
            picked.append(i)
        return picked

    def explain(self, i, j):
        """Plain-English reason why movie j was recommended for movie i."""
        a, b = self.df.loc[i], self.df.loc[j]
        reasons = []
        same_dir = set(_split(a["director"])) & set(_split(b["director"]))
        if same_dir:
            reasons.append("Same director: " + ", ".join(sorted(same_dir)))
        same_writer = set(_split(a["writers"])) & set(_split(b["writers"]))
        if same_writer and not same_dir:
            reasons.append("Same writer: " + ", ".join(sorted(same_writer)[:2]))
        same_cast = [c for c in _split(a["cast"]) if c in set(_split(b["cast"]))]
        if same_cast:
            reasons.append("Also stars " + ", ".join(same_cast[:2]))
        shared_kw = (self.kw_sets[i] & self.kw_sets[j]) - TONES - HIDE_IN_WHY
        themes = sorted(shared_kw - PLACES, key=lambda k: -self.idf.get(_kw_token(k), 0))
        places = sorted(shared_kw & PLACES)
        if themes:
            reasons.append("Shared themes: " + ", ".join(themes[:3]))
        elif places and len(reasons) < 2:
            reasons.append("Also set in " + ", ".join(p.title() for p in places[:2]))
        if not reasons:
            shared_g = [g for g in a["genre_list"] if g in self.genre_sets[j]]
            reasons.append(("Both " + " · ".join(shared_g[:3])) if shared_g else "Similar story and tone")
        return " · ".join(reasons[:2])

    def _result(self, idx, score, reasons=None):
        cols = ["id", "title", "original_title", "original_language", "lang", "year", "genre_list",
                "vote_average", "vote_count", "overview", "director", "runtime", "mpaa", "imdb_score",
                "poster_path"]
        out = self.df.loc[idx, cols].copy()
        out["score"] = np.round(score[idx], 3) if len(idx) else []
        out["why"] = reasons if reasons is not None else ""
        return out.reset_index(drop=True)

    # ----------------------------------------------------------- mode 1
    def similar(self, name, n=5, lang=None, family_only=False, mix=False):
        i = self.find(name)
        if i is None:
            return None, None
        sims = linear_kernel(self.matrix[i], self.matrix).ravel()
        score = sims * (0.8 + 0.4 * self.df["quality"].values)   # rating nudges, similarity decides
        ok = self._mask(lang, family_only, min_rank=0.1)
        ok[i] = False
        cap = 2 if (mix and not lang) else None
        top = self._pick(score, ok, n, self.df["original_language"].values, cap)
        return i, self._result(top, score, [self.explain(i, j) for j in top])

    def twins(self, i, n=6, family_only=False):
        """Closest match in each of several other languages."""
        seed_lang = self.df.loc[i, "original_language"]
        langs = [l for l in TWIN_LANGS if l != seed_lang][:n]
        sims = linear_kernel(self.matrix[i], self.matrix).ravel()
        score = sims * (0.8 + 0.4 * self.df["quality"].values)   # rating nudges, similarity decides
        seed_g = self.genre_sets[i]
        shares_genre = self.genre_sets.map(lambda g: bool(g & seed_g)).values
        picks = []
        for l in langs:
            ok = self._mask(l, family_only, min_rank=0.2) & shares_genre & (sims >= self.TWIN_MIN_SIM)
            ok[i] = False
            picks += self._pick(score, ok, 1)
        return self._result(picks, score, [self.explain(i, j) for j in picks])

    # ----------------------------------------------------------- mode 2
    def detect_moods(self, text):
        text = text.lower()
        hits = {m: sum(t in text for t in p["triggers"]) for m, p in MOODS.items()}
        hits = {m: h for m, h in hits.items() if h}
        return sorted(hits, key=hits.get, reverse=True)[:2]

    def by_mood(self, text, n=5, moods=None, lang=None, family_only=False, mix=False):
        moods = moods if moods is not None else self.detect_moods(text)
        if moods:
            phrases = [p.strip() for m in moods for p in MOODS[m]["keywords"].split(",")]
            query = " ".join(_kw_token(p) for p in phrases) + " " + " ".join(phrases)
            want = set().union(*[MOODS[m]["genres"] for m in moods])
            avoid = set().union(*[MOODS[m]["avoid"] for m in moods])
            avoid_mpaa = set().union(*[MOODS[m].get("avoid_mpaa", []) for m in moods])
        else:
            phrases, query, want, avoid, avoid_mpaa = [], text.lower(), set(), set(), set()

        kw = linear_kernel(self.tfidf.transform([query]), self.matrix).ravel()
        if kw.max() == 0 and not moods:      # nothing in the text matched any movie
            return [], self._result([], kw)
        kw = kw / kw.max() if kw.max() > 0 else kw
        genre = self.genre_sets.map(lambda g: len(g & want) / len(want) if want else 0).values
        penalty = self.genre_sets.map(lambda g: 0.5 if g & avoid else 0).values
        penalty = penalty + self.df["mpaa"].isin(avoid_mpaa).values * 0.5
        score = 0.25 * genre + 0.50 * kw + 0.25 * self.df["quality"].values - penalty

        ok = self._mask(lang, family_only, min_rank=0.25 if lang else 0.75)
        if want:
            ok &= genre > 0          # results must fit at least one of the mood's genres
        cap = 2 if (mix and not lang) else None
        top = self._pick(score, ok, n, self.df["original_language"].values, cap)

        wanted = {p.lower() for p in phrases}
        reasons = []
        for j in top:
            hit = sorted((self.kw_sets[j] & wanted) - HIDE_IN_WHY, key=lambda k: -self.idf.get(_kw_token(k), 0))[:3]
            if hit:
                reasons.append("Matches: " + ", ".join(hit))
            else:
                g = [x for x in self.df.loc[j, "genre_list"] if x in want]
                reasons.append(("Genre fit: " + " · ".join(g)) if g else "Matches your words")
        return moods, self._result(top, score, reasons)
