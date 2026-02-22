import streamlit as st
import pandas as pd
import pickle
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
import ast

movies = pickle.load(open("model_files/movie_list.pkl", "rb"))
similarity = pickle.load(open("model_files/similarity.pkl", "rb"))

def extract_genres(genres_str):
    try:
        return [g["name"] for g in ast.literal_eval(genres_str)]
    except:
        return []

# Create genre list column
movies["genre_list"] = movies["genres"].apply(extract_genres)

# Languages - currently available
language_map = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "ta": "Tamil",
    "ml": "Malayalam",
    "kn": "Kannada",
}

movies["language_name"] = movies["original_language"].map(language_map).fillna("Other")


# ------------------------------
# Page Configuration
# ---------------------------------
st.set_page_config(
    page_title="MoviMate",
    page_icon="📽️",
    layout="wide"
)

# setting dark theme for the app
st.markdown("""
<style>

/* ---------- GLOBAL ---------- */
html, body, [data-testid="stApp"] {
    background-color: #0f0f0f;
    color: #e5e7eb;
}

/* Remove top padding */
.block-container {
    padding-top: 1rem;
}

/* ---------- STREAMLIT TOP BAR (native) ---------- */
header[data-testid="stHeader"] {
    background: #0f0f0f;
    border-bottom: 1px solid #1f1f1f;
}

/* ---------- SIDEBAR ---------- */
section[data-testid="stSidebar"] {
    background-color: #0b0b0b;
    border-right: 1px solid #1f1f1f;
}

section[data-testid="stSidebar"] * {
    color: #d1d5db;
}

/* ---------- BUTTONS / CARDS ---------- */
button[kind="secondary"], button[kind="primary"] {
    background-color: #18181b !important;
    color: #e5e7eb !important;
    border-radius: 12px;
    border: 1px solid #262626;
}

button:hover {
    background-color: #27272a !important;
}

/* ---------- CAPTIONS / TEXT ---------- */
.stCaption, .stMarkdown, .stText {
    color: #d1d5db !important;
}

/* ---------- IMAGES ---------- */
img {
    border-radius: 14px;
}

</style>
""", unsafe_allow_html=True)

# top bar css
st.markdown("""
<style>
.brand {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: 0.14em;
    color: #ffffff;
}

.brand span {
    color: #ff4b4b;
}

.brand-sub {
    margin-left: 1rem;
    font-size: 0.9rem;
    color: #9ca3af;
}
</style>
""", unsafe_allow_html=True)



# css for clickable recommend movie poster
st.markdown("""
<style>
.movie-card button {
    width: 100%;
    padding: 0;
    border-radius: 16px;
    border: none;
    background: #ffffff;
    box-shadow: 0 4px 14px rgba(0,0,0,0.12);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.movie-card button:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 22px rgba(0,0,0,0.18);
}

.movie-card img {
    border-top-left-radius: 16px;
    border-top-right-radius: 16px;
}

.movie-title {
    padding: 10px;
    font-weight: 600;
    text-align: center;
    color: #333;
}
</style>
""", unsafe_allow_html=True)

 
# ------------------------------
# Session State Initialization
# ------------------------------
if "history" not in st.session_state:
    st.session_state.history = []  # Stores movie_title of recently viewed movies
if "mode" not in st.session_state:
    st.session_state.mode = None
if "selected_movie" not in st.session_state:
    st.session_state.selected_movie = None
if "random_movie" not in st.session_state:
    st.session_state.random_movie = None
if "favourites" not in st.session_state:
    st.session_state.favourites = []
if "grid_locked" not in st.session_state:
    st.session_state.grid_locked = False


# ------------------------------
# TMDB API and Helper Functions
# ------------------------------
TMDB_API_KEY = st.secrets["tmdb"]["api_key"]

def requests_retry_session(
    retries=5,
    backoff_factor=1,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_poster(movie_title):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
        data = requests_retry_session().get(url).json()
        if data.get("results"):
            poster_path = data["results"][0].get("poster_path")
            if poster_path:
                return "https://image.tmdb.org/t/p/w500/" + poster_path
    except Exception as e:
        print("POSTER ERROR:", e)
    return None


def fetch_watch_providers(movie_id, region="IN"):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}/watch/providers?api_key={TMDB_API_KEY}"
        data = requests_retry_session().get(url).json()

        providers = data.get("results", {}).get(region, {})
        flatrate = providers.get("flatrate", [])

        return [p["provider_name"] for p in flatrate]

    except Exception as e:
        print("WATCH PROVIDER ERROR:", e)
        return []


# helper function for clickable movie cards
def movie_card(movie_title, poster_url, key_prefix):
    with st.container():
        if poster_url:
            st.image(poster_url, use_container_width=True)

        # Title as clickable button
        if st.button(
            movie_title,
            key=f"{key_prefix}_{movie_title}",
            use_container_width=True
        ):
            st.session_state.mode = "search"
            st.session_state.selected_movie = movie_title
           # st.session_state.select_movie = movie_title  # sync dropdown



def fetch_trailer(movie_title):
    try:
        # Step 1: search by title to get movie ID
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={movie_title}"
        search_resp = requests_retry_session().get(search_url)
        if search_resp.status_code != 200:
            return None

        search_data = search_resp.json()
        if not search_data.get("results"):
            return None

        movie_id = search_data["results"][0]["id"]

        # Step 2: fetch videos using ID
        video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
        response = requests_retry_session().get(video_url)

        if response.status_code == 200:
            for video in response.json().get("results", []):
                if video.get("type") == "Trailer" and video.get("site") == "YouTube":
                    return f"https://youtu.be/{video['key']}"
    except Exception as e:
        print("TRAILER ERROR:", e)
    return None



def get_movie_details(movie_title):
    try:
        # STEP 1: Search movie by title
        search_url = (
            f"https://api.themoviedb.org/3/search/movie"
            f"?api_key={TMDB_API_KEY}&query={movie_title}"
        )
        search_resp = requests_retry_session().get(search_url)

        if search_resp.status_code != 200:
            return None

        search_data = search_resp.json()
        if not search_data.get("results"):
            return None

        movie_id = search_data["results"][0]["id"]

        # STEP 2: Fetch movie details using ID
        details_url = (
            f"https://api.themoviedb.org/3/movie/{movie_id}"
            f"?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
        )
        response = requests_retry_session().get(details_url)
        watch_providers = fetch_watch_providers(movie_id)

        if response.status_code != 200:
            return None

        data = response.json()

        # Directors
        directors = [
            crew["name"]
            for crew in data.get("credits", {}).get("crew", [])
            if crew.get("job") == "Director"
        ]

        # Cast (top 5)
        cast_details = []
        for actor in data.get("credits", {}).get("cast", [])[:5]:
            cast_details.append({
                "name": actor.get("name"),
                "character": actor.get("character"),
                "profile": (
                    f"https://image.tmdb.org/t/p/w500{actor['profile_path']}"
                    if actor.get("profile_path") else None
                )
            })
        if st.button("❤️ Add to Favourites"):
            if movie_title not in st.session_state.favourites:
                st.session_state.favourites.append(movie_title)
                st.success("Added to favourites!")

        return {
            "rating": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "release_date": data.get("release_date"),
            "runtime": data.get("runtime"),
            "tagline": data.get("tagline"),
            "overview": data.get("overview"),
            "director": ", ".join(directors) if directors else "N/A",
            "cast": cast_details,
            "genres": ", ".join([g["name"] for g in data.get("genres", [])]) or "N/A",
            "budget": f"${data['budget']:,}" if data.get("budget", 0) > 0 else "N/A",
            "revenue": f"${data['revenue']:,}" if data.get("revenue", 0) > 0 else "N/A",
            "available_in": ", ".join(
                [lang["english_name"] for lang in data.get("spoken_languages", [])]
            ) or "N/A",
            "watch_providers": watch_providers
        }

    except Exception as e:
        print("DETAIL FETCH ERROR:", e)

    return None


def recommend(movie):
    width=300
    index = movies[movies["title"] == movie].index[0]
    distances = sorted(
        list(enumerate(similarity[index])),
        reverse=True,
        key=lambda x: x[1]
    )

    recommendations = []
    seen_titles = set()

    for i, score in distances:
        rec_movie_title = movies.iloc[i]["title"]

        if rec_movie_title == movie:
            continue
        if rec_movie_title in seen_titles:
            continue

        poster = fetch_poster(rec_movie_title)
        if not poster:
            continue
        recommendations.append({
            "title": rec_movie_title,
            "poster": poster,
            "trailer": fetch_trailer(rec_movie_title)
        })

        seen_titles.add(rec_movie_title)

        if len(recommendations) == 5:
            break

    return recommendations

def get_random_movie():
    random_movie = movies.sample(1).iloc[0]
    title = random_movie["title"]

    return {
        "title": title,
        "poster": fetch_poster(title),
        "trailer": fetch_trailer(title),
        "movie_title": title   # keep key name if UI expects it
    }




def update_history(movie_title):
    if not st.session_state.history or st.session_state.history[-1] != movie_title:
        st.session_state.history.append(movie_title)
        if len(st.session_state.history) > 5:
            st.session_state.history.pop(0)


def get_trending_movies():
    try:
        url = f"https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}"
        response = requests_retry_session().get(url)

        if response.status_code == 200:
            data = response.json()
            trending = data.get("results", [])[:5]
            trending_list = []

            for movie in trending:
                title = movie.get("title")

                trending_list.append({
                    "title": title,
                    "poster": (
                        f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"
                        if movie.get("poster_path") else None
                    ),
                    "movie_title": title   # TITLE, not ID
                })

            return trending_list

        return []

    except Exception as e:
        print("TRENDING ERROR:", e)
        return []

# ------------------------------
# Load Data
# ------------------------------
#movies = pd.read_csv("Dataset/tmdb_5000_movies.csv", encoding="latin1")
#credits = pd.read_csv("Dataset/tmdb_5000_credits.csv", encoding="latin1")

# ------------------------------
# UI Configuration and Header
# ------------------------------
st.markdown("""
<style>
.hero {
    text-align: center;
    padding: 4rem 1rem 3rem 1rem;
    background: radial-gradient(circle at top, #1a1a2e 0%, #0f0f1a 55%, #000000 100%);
}

.hero-title {
    font-size: 4rem;
    font-weight: 800;
    letter-spacing: 0.15em;
    color: #eaeaea;
    margin-bottom: 0.5rem;
}

.hero-title span {
    color: #ff4b4b;
}

.hero-subtitle {
    font-size: 1.4rem;
    color: #b5b5c3;
    margin-bottom: 1.2rem;
}

.hero-tagline {
    font-size: 1.1rem;
    color: #8f8fa3;
    letter-spacing: 0.08em;
}

.divider {
    margin-top: 3rem;
    height: 1px;
    background: linear-gradient(to right, transparent, #333, transparent);
}
</style>

<div class="hero">
    <div class="hero-title">
        MOVI<span>MATE</span> 🎬
    </div>
    <div class="hero-subtitle">
        Your Movie Matchmaker
    </div>
    <div class="hero-tagline">
        Discover • Decide • Dive In ✨
    </div>
    <div class="divider"></div>
</div>
""", unsafe_allow_html=True)


# ------------------------------
# Trending Movies Section
# ------------------------------
st.markdown("""
    <h2 style='text-align: center; color: #FF4B4B; margin-bottom: 1rem;'>
        🔥 Trending
    </h2>
""", unsafe_allow_html=True)

trending_movies = get_trending_movies()
trending_cols = st.columns(5)
for idx, movie in enumerate(trending_movies):
    with trending_cols[idx]:
        #if movie.get("poster"):
        movie_card(
            movie_title=movie["title"],
            poster_url=movie["poster"],
            key_prefix="rec"
        )

            

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("---")

# ------------------------------
# Main Selection Section
# ------------------------------

# ------------------------------
# Genre Based Selection
# ------------------------------
st.markdown("### 🎞️ Browse by Genre or Language 🌍")

all_genres = sorted(
    {genre for genres in movies["genre_list"] for genre in genres}
)

selected_genre = st.selectbox(
    "Choose a genre 👇",
    ["All"] + all_genres,
    key="genre_select"
)

if selected_genre == "All":
    available_languages = sorted(movies["language_name"].unique())
else:
    available_languages = sorted(
        movies[
            movies["genre_list"].apply(lambda g: selected_genre in g)
        ]["language_name"].unique()
    )


selected_language = st.selectbox(
    "Choose a language 👇",
    ["All"] + available_languages,
    key="genre_language_select"
)

# -------- Filter movies --------
if selected_genre == "All":
    genre_filtered = movies.copy()
else:
    genre_filtered = movies[
        movies["genre_list"].apply(lambda g: selected_genre in g)
    ]

genre_filtered = genre_filtered.drop_duplicates(subset="title")

if selected_language != "All":
    genre_filtered = genre_filtered[
        genre_filtered["language_name"] == selected_language
    ]
genre_movies = genre_filtered.head(5)

# 🔧 CHANGE 2: proper 2 × 5 grid (no gaps)
for row_start in range(0, len(genre_movies), 5):
    genre_cols = st.columns(5)

    for col_idx, row in enumerate(
        genre_movies.iloc[row_start:row_start + 5].itertuples()
    ):
        with genre_cols[col_idx]:
            poster = fetch_poster(row.title)

            # 🔧 CHANGE 3: keep space if poster missing
            if poster:
                st.image(poster, width=300)
            else:
                st.markdown(
                    "<div style='height:450px;'>Poster Not Available</div>",
                    unsafe_allow_html=True
                )

            if st.button(row.title, key=f"genre_{row.id}"):
                st.session_state.mode = "search"
                st.session_state.selected_movie = row.title
                st.session_state.select_movie = row.title

col_search, col_spacer, col_surprise = st.columns([3, 1, 2])

with col_search:
    st.subheader("🔍 Search a Movie")
    selected_movie = st.selectbox("Type to search...👇🏻", movies["title"].values, key="select_movie", help="Start typing to find your movie")
    if st.button("Show Details & Recommendations", key="show_details"):
        st.session_state.mode = "search"
        st.session_state.selected_movie = selected_movie

with col_surprise:
    st.subheader("🎁 Let the Model Decide!")
    if st.button("Surprise Me!", key="surprise_me"):
        st.session_state.mode = "surprise"
        st.session_state.random_movie = get_random_movie()

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------
# Content Section: Movie Details & Recommendations
# ------------------------------
if "mode" in st.session_state and st.session_state.mode:
    if st.session_state.mode == "search":
        movie_title = st.session_state.selected_movie
        #movie_row = movies[movies["title"] == movie_title].iloc[0]
        matched = movies[movies["title"] == movie_title]

        if matched.empty:
            st.error("⚠️ This movie is not available in the recommendation dataset.")
            st.stop()

        movie_row = matched.iloc[0]

        update_history(movie_title)
        details = get_movie_details(movie_title)
        trailer_url = fetch_trailer(movie_title)

        st.markdown("<div style='border-top: 2px solid #eee; margin: 2rem 0;'></div>", unsafe_allow_html=True)
        # Highlighting the movie name in red using HTML inside the markdown
        st.markdown(f"<h2>🎬 Details of: <span style='color: #FF4B4B;'>{movie_title}</span></h2>", unsafe_allow_html=True)

        # Display poster and details side-by-side
        detail_col_left, detail_col_right = st.columns([1, 2])
        with detail_col_left:
            poster = fetch_poster(movie_title)
            if poster:
                st.image(poster, use_container_width=True)
        with detail_col_right:
            if details:
                # Group 1: Ratings & Runtime
                st.markdown("#### ⭐ Ratings & Runtime ⌛")
                info_cols = st.columns([1, 1, 1])
                with info_cols[0]:
                    rating = details.get('rating', 'N/A')
                    st.markdown(f"**Rating:** <span style='color:green;'>{rating}</span>/10", unsafe_allow_html=True)
                with info_cols[1]:
                    vote_count = details.get('vote_count', 'N/A')
                    st.markdown(f"**No. of Ratings:** <span style='color:green;'>{vote_count}</span>", unsafe_allow_html=True)
                with info_cols[2]:
                    runtime = f"{details.get('runtime', 'N/A')} mins" if details.get('runtime') else "N/A"
                    st.markdown(f"**Runtime:** <span style='color:green;'>{runtime}</span>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                # Tagline in a blue info box
                if details.get("tagline"):
                    st.info(details["tagline"])
                # Overview
                st.markdown("**Overview:**")
                st.write(details.get("overview", "N/A"))

                st.markdown("<br>", unsafe_allow_html=True)
                # Group 2: Release & Financials
                st.markdown("#### 💰 Release & Financials")
                row1_cols = st.columns([1, 1, 1])
                with row1_cols[0]:
                    st.markdown(f"**Release Date:** {details.get('release_date', 'N/A')}")
                with row1_cols[1]:
                    st.markdown(f"**Budget:** {details.get('budget', 'N/A')}")
                with row1_cols[2]:
                    st.markdown(f"**Revenue:** {details.get('revenue', 'N/A')}")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                # Group 3: Production Details
                st.markdown("#### 🎞️ Production Details")
                row2_cols = st.columns([1, 1, 1])
                with row2_cols[0]:
                    st.markdown(f"**Genres:** {details.get('genres', 'N/A')}")
                with row2_cols[1]:
                    st.markdown(f"**Available in:** {details.get('available_in', 'N/A')}")
                with row2_cols[2]:
                    st.markdown(f"**Directed by:** {details.get('director', 'N/A')}")
                if details.get("watch_providers"):
                    st.markdown("#### 📺 Available On")
                    st.write(", ".join(details["watch_providers"]))
                else:
                    st.markdown("#### 📺 Available On")
                    st.write("Availability data not found")
       
                st.markdown("<br>", unsafe_allow_html=True)
                # Cast Section
                if details.get("cast"):
                    st.markdown("#### 🎭 Cast")
                    cast_cols = st.columns(len(details["cast"]))
                    for idx, actor in enumerate(details["cast"]):
                        with cast_cols[idx]:
                            if actor.get("profile"):
                                st.image(actor["profile"], use_container_width=True)
                            st.caption(f"{actor.get('name')} as {actor.get('character')}")
            else:
                st.error("Could not retrieve movie details. Please try another movie.")

            if trailer_url:
                with st.expander("Watch Trailer 📽️"):
                    st.video(trailer_url)

        # Display Recommendations
        with st.spinner("Fetching Recommendations..."):
            recommendations = recommend(movie_title)
        st.markdown("<div style='border-top: 2px solid #eee; margin: 2rem 0;'></div>", unsafe_allow_html=True)
        st.subheader("🚀 Recommended Movies")
        rec_cols = st.columns(5)

        for idx, rec in enumerate(recommendations):
            with rec_cols[idx]:
                movie_card(
                    movie_title=rec["title"],
                    poster_url=rec["poster"],
                    key_prefix="rec"
                )

                if rec.get("trailer"):
                     with st.expander("Trailer"):
                        st.video(rec["trailer"])

                        
    elif st.session_state.mode == "surprise":
        random_data = st.session_state.random_movie
        movie_title = random_data["title"]
        #movie_title = random_data.get("movie_title")
        if not movie_title:
            movie_row = movies[movies["title"] == movie_title].iloc[0]
            movie_title = movie_row.movie_title
        update_history(movie_title)
        details = get_movie_details(movie_title)
        trailer_url = fetch_trailer(movie_title)

        st.markdown("<div style='border-top: 2px solid #eee; margin: 2rem 0;'></div>", unsafe_allow_html=True)
        # Highlighting the movie name in red using HTML inside the markdown
        st.markdown(f"<h2>🎉 Your Surprise Movie: <span style='color: #FF4B4B;'>{movie_title}</span></h2>", unsafe_allow_html=True)

        detail_col_left, detail_col_right = st.columns([1, 2])
        with detail_col_left:
            poster = fetch_poster(movie_title)
            if poster:
                st.image(poster, use_container_width=True)
        with detail_col_right:
            if details:
                # Group 1: Ratings & Runtime
                st.markdown("#### Ratings & Runtime")
                info_cols = st.columns([1, 1, 1])
                with info_cols[0]:
                    rating = details.get('rating', 'N/A')
                    st.markdown(f"**Rating:** <span style='color:green;'>{rating}</span>/10", unsafe_allow_html=True)
                with info_cols[1]:
                    vote_count = details.get('vote_count', 'N/A')
                    st.markdown(f"**No. of Ratings:** <span style='color:green;'>{vote_count}</span>", unsafe_allow_html=True)
                with info_cols[2]:
                    runtime = f"{details.get('runtime', 'N/A')} mins" if details.get('runtime') else "N/A"
                    st.markdown(f"**Runtime:** <span style='color:green;'>{runtime}</span>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                # Tagline in a blue info box
                if details.get("tagline"):
                    st.info(details["tagline"])
                # Overview
                st.markdown("**Overview:**")
                st.write(details.get("overview", "N/A"))

                st.markdown("<br>", unsafe_allow_html=True)
                # Group 2: Release & Financials
                st.markdown("#### Release & Financials")
                row1_cols = st.columns([1, 1, 1])
                with row1_cols[0]:
                    st.markdown(f"**Release Date:** {details.get('release_date', 'N/A')}")
                with row1_cols[1]:
                    st.markdown(f"**Budget:** {details.get('budget', 'N/A')}")
                with row1_cols[2]:
                    st.markdown(f"**Revenue:** {details.get('revenue', 'N/A')}")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                # Group 3: Production Details
                st.markdown("#### Production Details")
                row2_cols = st.columns([1, 1, 1])
                with row2_cols[0]:
                    st.markdown(f"**Genres:** {details.get('genres', 'N/A')}")
                with row2_cols[1]:
                    st.markdown(f"**Available in:** {details.get('available_in', 'N/A')}")
                with row2_cols[2]:
                    st.markdown(f"**Directed by:** {details.get('director', 'N/A')}")
                    
                st.markdown("<br>", unsafe_allow_html=True)
                # Cast Section
                if details.get("cast"):
                    st.markdown("#### Cast")
                    cast_cols = st.columns(len(details["cast"]))
                    for idx, actor in enumerate(details["cast"]):
                        with cast_cols[idx]:
                            if actor.get("profile"):
                                st.image(actor["profile"], use_container_width=True)
                            st.caption(f"{actor.get('name')} as {actor.get('character')}")
            else:
                st.error("Could not retrieve movie details. Please try another movie.")

            if trailer_url:
                with st.expander("Watch Trailer"):
                    st.video(trailer_url)

# ------------------------------
# Sidebar: Recently Viewed
# ------------------------------

with st.sidebar:
    st.header("🕒 Recently Viewed")
    if st.session_state.history:
        for i, hist_id in enumerate(reversed(st.session_state.history)):
            hist_poster = fetch_poster(hist_id)
            col_img, col_btn = st.columns([1, 3])
            with col_img:
                if hist_poster:
                    st.image(hist_poster, use_container_width=True)

            with col_btn:
                if st.button(
                    hist_id,
                    key=f"hist_{hist_id}_{i}",
                    use_container_width=True
                ):
                    st.session_state.mode = "search"
                    st.session_state.selected_movie = hist_id
                    st.rerun()
    else:
        st.caption("No watch history")
with st.sidebar:
    st.header("❤️ Favourites")
    if st.session_state.favourites:
        for fav in st.session_state.favourites:
            if st.button(fav, key=f"fav_{fav}"):
                st.session_state.mode = "search"
                st.session_state.selected_movie = fav
                st.session_state.select_movie = fav
                st.rerun()
    else:
        st.write("No favourites yet")
