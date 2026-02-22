import pandas as pd
movies = pd.read_csv("Dataset/tmdb_5000_movies.csv")
print("movie dups:", movies[movies.duplicated("id")])
