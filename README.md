# 🎬 **MoviMate — Your Movie Matchmaker**

MoviMate is a **content-based movie recommendation system** that helps users discover movies similar to their interests using metadata-driven similarity analysis.  
It is designed to be **simple, fast, and intuitive**, focusing on meaningful recommendations rather than overwhelming users with options.

---

## 🚀 Features

- 🔍 **Search-based Recommendations**  
  Get movie suggestions similar to a selected movie using cosine similarity.

- 🌍 **Browse by Language**  
  Explore popular movies filtered by language.

- 🎲 **Surprise Me Mode**  
  Get randomly recommended movies when you don’t know what to watch.

- 🎭 **Genre Awareness**  
  Recommendations consider genres and descriptive metadata.

- 🖼️ **Poster Integration**  
  Movie posters are fetched dynamically using TMDB API.

---

## 🧠 How It Works (In Simple Terms)

1. Movie metadata is cleaned and processed.
2. Text features are converted into vectors.
3. **Cosine similarity** is used to find movies that are most alike.
4. Top similar movies are ranked and displayed to the user.

This is a **content-based filtering** approach — it does not rely on user ratings or history.

---

## 🛠️ Tech Stack

- **Python**
- **Pandas & NumPy** – data processing
- **Scikit-learn** – vectorization & similarity
- **Streamlit** – user interface
- **TMDB API** – posters & movie data

---

## 📂 Project Structure
```
MoviMate
├── app.py # Streamlit application
├── rebuild_model.py # Script to rebuild similarity model
├── movies.csv # Movie metadata
├── credits.csv # Cast & crew data
├── model_files/ # Generated model files (ignored in git)
├── assets/ # Images/screenshots (optional)
├── .gitignore
└── README.md
```

⚠️ Important Note:
Large `.pkl` files are **intentionally not pushed to GitHub**.

To generate them locally:
go to `bash` and run:  python rebuild_model.py

---
▶️ How to Run the Project
1️⃣ Clone the Repository
`git clone https://github.com/JanakiVeluri006/MoviMate.git`
`cd MoviMate`

2️⃣ Install Dependencies
`pip install -r requirements.txt `

3️⃣ Run the App
`streamlit run app.py`

---
### 🎯 Use Cases
 - Finding similar movies to a favorite title
 - Discovering movies in a specific language
 - Exploring new content effortlessly
 - Academic demonstration of recommender systems
---
### 🔮 Future Enhancements
 1. Hybrid recommendations (content + collaborative)
 2. User profiles & preferences
 3. Improved similarity weighting
 4. Scalable deployment
 5. Enhanced UI/UX
---
## 👤 Author 
Janaki Veluri
Computer Science & Engineering Student

“MoviMate is built to make choosing a movie feel easy, not exhausting.”

⭐ If you like this project, feel free to star the repository!
