import pandas as pd
import numpy as np
import re
import streamlit as st

def get_data():
    """
    Initializes the app. Loads and cleans datasets.
    """

    # Import the datasets
    global links_df, movies_df, ratings_df, tags_df

    # Links
    url_links = "https://drive.google.com/file/d/14ULP-ZyKnutIAs-x0SgB77S9SsCVUoOQ/view?usp=share_link"
    path_links = 'https://drive.google.com/uc?export=download&id='+url_links.split('/')[-2]
    links_df = pd.read_csv(path_links)

    # Movies
    url_movies = "https://drive.google.com/file/d/1MKtLF_mSpZS8rMf4OOWOrs4M-Y-L3xPl/view?usp=share_link"
    path_movies = 'https://drive.google.com/uc?export=download&id='+url_movies.split('/')[-2]
    movies_df = pd.read_csv(path_movies)

    # Ratings
    url_ratings = "https://drive.google.com/file/d/159evBRRd6a0kqGBV0Fk28C53LD5J7LJW/view?usp=share_link"
    path_ratings = 'https://drive.google.com/uc?export=download&id='+url_ratings.split('/')[-2]
    ratings_df = pd.read_csv(path_ratings)

    # Tags
    url_tags = "https://drive.google.com/file/d/1EZWKZE7IfwWSrACcoZ9sDdI9DSOtkkNA/view?usp=share_link"
    path_tags = 'https://drive.google.com/uc?export=download&id='+url_tags.split('/')[-2]
    tags_df = pd.read_csv(path_tags)

    
    movies_df['year'] = movies_df['title'].str.extract(r"\(([0-9]+)\)")
    movies_df['title'] = movies_df['title'].str.replace(r"\(.*\)","")
    #movies_df['genres'] = movies_df['genres'].str.split("|")

    ratings_df['timestamp'] = pd.to_datetime(ratings_df['timestamp'], unit='s')
    tags_df['timestamp'] = pd.to_datetime(tags_df['timestamp'], unit='s')

def best_rated(n=10):
    best = ratings_df.groupby('movieId', as_index = False).aggregate({'userId': 'count', 'rating':'mean'})
    best["opinion"] = best["rating"]*np.log(best["userId"])
    rank = movies_df.merge(best, on= 'movieId')
    return rank.nlargest(n, 'opinion')[['title', 'rating', 'userId']].rename(columns = {'title': 'Title', 'rating': 'Rating', 'userId': '#Ratings'})

def ini(n):
    get_data()
    st.title('WBSFlix')
    st.header('Best rated Movies!')
    st.table(best_rated(n))

def main():
    n = 10
    logged_in = False
    name = ''
    ini(n)
    '''
    while True:
        if logged_in:
            st.write(f"Welcome, {name}")
            logged_in = ~st.button("Log Out")
        else: #not logged in
            name = st.text_input('Username')
            logging = st.button("Log In")
            if logging & (name != ''):
                logged_in = True
    '''

main()