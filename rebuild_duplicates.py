import pandas as pd

# -------------------------------
# LOAD FILES
# -------------------------------
movies = pd.read_csv(
    "Dataset/tmdb_5000_movies.csv",
    encoding="latin1",
    low_memory=False
)

credits = pd.read_csv(
    "Dataset/tmdb_5000_credits.csv",
    encoding="latin1",
    low_memory=False
)

# -------------------------------
# NORMALIZE ID TYPES
# -------------------------------
movies["id"] = pd.to_numeric(movies["id"], errors="coerce")
credits["movie_id"] = pd.to_numeric(credits["movie_id"], errors="coerce")

movies = movies.dropna(subset=["id"])
credits = credits.dropna(subset=["movie_id"])

movies["id"] = movies["id"].astype(int)
credits["movie_id"] = credits["movie_id"].astype(int)

# -------------------------------
# FIND MAX EXISTING ID
# -------------------------------
max_id = movies["id"].max()
print("Starting max ID:", max_id)

# -------------------------------
# FIND DUPLICATE MOVIE IDs
# -------------------------------
duplicate_ids = movies[movies.duplicated(subset="id", keep=False)]["id"].unique()
print("Duplicate IDs found:", duplicate_ids)

# -------------------------------
# REPAIR DUPLICATES SAFELY
# -------------------------------
for dup_id in duplicate_ids:
    dup_movies = movies[movies["id"] == dup_id]

    # keep FIRST movie as original
    for idx, row in dup_movies.iloc[1:].iterrows():
        max_id += 1
        new_id = max_id
        title = row["title"]

        # update movie id
        movies.at[idx, "id"] = new_id

        # update ONLY the matching credits row(s)
        credits.loc[
            (credits["movie_id"] == dup_id),
            "movie_id"
        ] = new_id

        print(f"Reassigned ID for '{title}': {dup_id} → {new_id}")

# -------------------------------
# FINAL SAFETY CHECK
# -------------------------------
assert not movies["id"].duplicated().any(), "❌ Duplicate IDs still exist!"

# -------------------------------
# SAVE BACK (ONLY AFTER FILES ARE CLOSED)
# -------------------------------
movies.to_csv("Dataset/tmdb_5000_movies.csv", index=False)
credits.to_csv("Dataset/tmdb_5000_credits.csv", index=False)

print("✅ Duplicate IDs repaired successfully")

#duplicate_ids = movies[movies.duplicated(subset="id", keep=False)]["id"].unique() #print("Duplicate IDs found:", duplicate_ids)
