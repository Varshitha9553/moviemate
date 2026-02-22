import pickle

movies = pickle.load(open("model_files/movie_list.pkl", "rb"))
similarity = pickle.load(open("model_files/similarity.pkl", "rb"))

print("Movies type:", type(movies))
print("Movies shape:", movies.shape)
print("Similarity shape:", similarity.shape)

print("\nFirst 5 movies:")
print(movies[["id", "title"]].head())

print("\nLast 5 movies:")
print(movies[["id", "title"]].tail())
