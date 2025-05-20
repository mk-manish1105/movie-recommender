import streamlit as st
import pickle
import gzip
import numpy as np
import pandas as pd
import requests
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("TMDB_API_KEY")

# Fetch poster image URL
def fetch_poster(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get('poster_path')
        if poster_path:
            return "https://image.tmdb.org/t/p/w500/" + poster_path
    except requests.exceptions.RequestException as e:
        print("Error fetching poster:", e)
    return "https://via.placeholder.com/150"

# Fetch movie metadata: genre, year, rating
def fetch_metadata(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        genres = ", ".join([genre['name'] for genre in data.get('genres', [])])
        release_date = data.get('release_date', '')
        year = release_date.split("-")[0] if release_date else "N/A"
        rating = data.get('vote_average', 'N/A')
        return genres, year, rating
    except requests.exceptions.RequestException as e:
        print("Error fetching metadata:", e)
        return "N/A", "N/A", "N/A"

# Fetch YouTube trailer URL
def fetch_trailer(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={api_key}&language=en-US"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get('results', [])
        for video in results:
            if video['site'] == 'YouTube' and video['type'] == 'Trailer':
                return f"https://www.youtube.com/watch?v={video['key']}"
    except requests.exceptions.RequestException as e:
        print("Error fetching trailer:", e)
    return None

# Load saved data
movies = pickle.load(open('movies.pkl', 'rb'))

with gzip.open('similarity.pkl.gz', 'rb') as f:
    similarity = pickle.load(f)

def recommend(movie, n_recommendations=5):
    try:
        index = movies[movies['title'] == movie].index[0]
        distances = similarity[index]
        movie_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:n_recommendations+1]

        recommended_movie_names = []
        recommended_movie_posters = []
        recommended_movie_metadata = []
        recommended_movie_trailers = []

        for i in movie_list:
            movie_id = movies.iloc[i[0]]['movie_id']
            recommended_movie_names.append(movies.iloc[i[0]].title)
            recommended_movie_posters.append(fetch_poster(movie_id))
            recommended_movie_metadata.append(fetch_metadata(movie_id))
            recommended_movie_trailers.append(fetch_trailer(movie_id))

        return recommended_movie_names, recommended_movie_posters, recommended_movie_metadata, recommended_movie_trailers
    except Exception as e:
        st.error(f"Failed to fetch recommendations: {e}")
        return None

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🎬 Movie Recommender System")
st.write("Select a movie you like and get recommendations based on content similarity.")

selected_movie = st.selectbox("Search for a movie", movies['title'].values)

if st.button("Show Recommendations"):
    result = recommend(selected_movie)

    if result is None:
        st.error("Could not fetch recommendations due to an error.")
    else:
        names, posters, metadata, trailers = result
        cols = st.columns(5)
        for i in range(5):
            with cols[i]:
                st.image(posters[i], use_container_width=True)
                st.markdown(f"**🎞 Title:** {names[i]}")
                genre, year, rating = metadata[i]
                st.markdown(f"📅 Year: {year}")
                st.markdown(f"🎭 Genre: {genre}")
                st.markdown(f"⭐ Rating: {rating}/10")
                if trailers[i]:
                    st.markdown(f"[▶️ Watch Trailer 🎥]({trailers[i]})", unsafe_allow_html=True)
                else:
                    st.markdown("Trailer not available")
