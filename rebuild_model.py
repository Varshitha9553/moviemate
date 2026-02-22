import os
import pandas as pd
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# --------------------------------------------------
# 0. PATH SETUP (SINGLE SOURCE OF TRUTH)
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_DIR = os.path.join(BASE_DIR, "Dataset")
MODEL_DIR = os.path.join(BASE_DIR, "model_files")

os.makedirs(MODEL_DIR, exist_ok=True)

MOVIES_CSV = os.path.join(DATASET_DIR, "tmdb_5000_movies.csv")
CREDITS_CSV = os.path.join(DATASET_DIR, "tmdb_5000_credits.csv")

MOVIE_PKL = os.path.join(MODEL_DIR, "movie_list.pkl")
SIM_PKL = os.path.join(MODEL_DIR, "similarity.pkl")

print("REBUILD CWD:", os.getcwd())
print("USING MOVIES CSV:", MOVIES_CSV)
print("USING CREDITS CSV:", CREDITS_CSV)

# --------------------------------------------------
# 1. LOAD DATASETS
# --------------------------------------------------

movies = pd.read_csv(MOVIES_CSV, encoding="latin1", low_memory=False)
credits = pd.read_csv(CREDITS_CSV, encoding="latin1", low_memory=False)

print("CSV FILES LOADED SUCCESSFULLY")
print("Total movies in CSV:", movies.shape[0])
print("Last 10 movies in CSV:")
print(movies[["id", "title"]].tail(10))

# --------------------------------------------------
# 2. NORMALIZE ID COLUMNS
# --------------------------------------------------

movies["id"] = pd.to_numeric(movies["id"], errors="coerce")
credits["movie_id"] = pd.to_numeric(credits["movie_id"], errors="coerce")

movies = movies.dropna(subset=["id"])
credits = credits.dropna(subset=["movie_id"])

movies["id"] = movies["id"].astype(int)
credits["movie_id"] = credits["movie_id"].astype(int)

# --------------------------------------------------
# 3. DEDUPLICATION (SAFE, AFTER ID REPAIR)
# --------------------------------------------------

movies = movies.drop_duplicates(subset="id", keep="last")
credits = credits.drop_duplicates(subset="movie_id", keep="last")

print("After ID cleanup:")
print("Movies:", movies.shape[0])
print("Credits:", credits.shape[0])

# --------------------------------------------------
# 4. MERGE (LEFT JOIN — THIS IS THE FIX)
# --------------------------------------------------

df = movies.merge(
    credits,
    left_on="id",
    right_on="movie_id",
    how="left"
)

# fill missing credits safely
df["cast"] = df["cast"].fillna("[]")
df["crew"] = df["crew"].fillna("[]")

print("DATASETS MERGED SUCCESSFULLY")
print("Movies after merge:", df.shape[0])

# --------------------------------------------------
# 5. SELECT & RENAME COLUMNS
# --------------------------------------------------

df = df[
    ["id", "title_x", "overview", "genres", "keywords", "cast", "crew", "original_language"]
]

df.rename(columns={"title_x": "title"}, inplace=True)

# --------------------------------------------------
# 6. FINAL CLEANUP
# --------------------------------------------------

df.fillna("", inplace=True)
df.drop_duplicates(subset="id", inplace=True)

# --------------------------------------------------
# 7. CREATE TAGS
# --------------------------------------------------

df["tags"] = (
    df["overview"].astype(str) + " " +
    df["genres"].astype(str) + " " +
    df["keywords"].astype(str)
)

print("TEXT FEATURES CREATED")

# --------------------------------------------------
# 8. VECTORIZATION
# --------------------------------------------------

vectorizer = TfidfVectorizer(
    max_features=5000,
    stop_words="english"
)

vectors = vectorizer.fit_transform(df["tags"])

# --------------------------------------------------
# 9. SIMILARITY MATRIX
# --------------------------------------------------

similarity = cosine_similarity(vectors)

# --------------------------------------------------
# 10. SAVE MODEL ARTIFACTS (THIS CREATES PKLS)
# --------------------------------------------------

with open(MOVIE_PKL, "wb") as f:
    pickle.dump(df, f)

with open(SIM_PKL, "wb") as f:
    pickle.dump(similarity, f)

print()
print("MODEL ARTIFACTS SAVED SUCCESSFULLY")
print("Saved to:", MODEL_DIR)
print("Total movies in model:", df.shape[0])
print("Last 10 movies in model:")
print(df[["id", "title"]].tail(10))

import numpy as np


# hit rate: “Does the recommended list contain a relevant movie?”
def evaluate_hit_rate_at_k(similarity, k=5, sample_size=200):
    hits = 0
    total = 0

    n = min(sample_size, similarity.shape[0])

    for i in range(n):
        scores = list(enumerate(similarity[i]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        # ignore self (index 0)
        recommended = [idx for idx, _ in scores[1:k+1]]

        # assume top-1 similar movie is relevant
        relevant = scores[1][0]

        if relevant in recommended:
            hits += 1
        total += 1

    return hits / total


#precision: “Out of the recommended movies, how many are actually relevant?”
def evaluate_precision_at_k(similarity, k=5, sample_size=200):
    precision_sum = 0
    n = min(sample_size, similarity.shape[0])

    for i in range(n):
        scores = list(enumerate(similarity[i]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        recommended = [idx for idx, _ in scores[1:k+1]]
        relevant = scores[1][0]

        if relevant in recommended:
            precision_sum += 1 / k

    return precision_sum / n


#Mean Reciprocal Rank (MRR): “How early does the relevant movie appear in recommendations?”
def evaluate_mrr(similarity, sample_size=200):
    rr_sum = 0
    n = min(sample_size, similarity.shape[0])

    for i in range(n):
        scores = list(enumerate(similarity[i]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)

        relevant = scores[1][0]

        for rank, (idx, _) in enumerate(scores[1:], start=1):
            if idx == relevant:
                rr_sum += 1 / rank
                break

    return rr_sum / n

print("Evaluating recommendation model...\n")

hit_rate = evaluate_hit_rate_at_k(similarity, k=5, sample_size=200)
precision = evaluate_precision_at_k(similarity, k=5, sample_size=200)
mrr = evaluate_mrr(similarity, sample_size=200)

print(f"Hit Rate@5      : {hit_rate:.4f}")
print(f"Precision@5     : {precision:.4f}")
print(f"MRR             : {mrr:.4f}")
