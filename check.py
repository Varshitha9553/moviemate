import pandas as pd

movies = pd.read_csv("Dataset/tmdb_5000_movies.csv", encoding="latin1", low_memory=False)

print("Total movies:", len(movies))

print(
    movies.tail(20)[["id", "title"]]
)

credits = pd.read_csv("Dataset/tmdb_5000_credits.csv", encoding="latin1", low_memory=False)

movie_ids = set(movies["id"])
credit_ids = set(credits["movie_id"])

missing = movie_ids - credit_ids

print("Movies without credits:", len(missing))
list(missing)[:10]
