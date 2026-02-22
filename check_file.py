import pandas as pd

movies = pd.read_csv("Dataset/tmdb_5000_movies.csv", encoding="latin1", low_memory=False)

dup_ids = movies[movies.duplicated(subset="id", keep=False)]

print("Duplicate IDs:")
print(dup_ids.sort_values("id")[["id", "title"]])
