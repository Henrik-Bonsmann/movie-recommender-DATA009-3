import pandas as pd
import numpy as np
import re
import streamlit as st
from sklearn.metrics.pairwise import cosine_similarity

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
    movies_df['title'] = movies_df['title'].str.replace(r" \(.*\)","")
    #movies_df['genres'] = movies_df['genres'].str.split("|")

    for i in range(len(movies_df)):
        if ', The' in movies_df.title[i]:
            movies_df.title[i] = movies_df.title[i].split(", ")[1] + ' '+ movies_df.title[i].split(", ")[0]

    ratings_df['timestamp'] = pd.to_datetime(ratings_df['timestamp'], unit='s')
    tags_df['timestamp'] = pd.to_datetime(tags_df['timestamp'], unit='s')

def best_rated(n=10):
    best = ratings_df.groupby('movieId', as_index = False).aggregate({'userId': 'count', 'rating':'mean'})
    best["opinion"] = best["rating"]*np.log(best["userId"])
    rank = movies_df.merge(best, on= 'movieId')
    rank = rank.nlargest(n, 'opinion')[['title', 'rating', 'userId']].rename(columns = {'title': 'Title', 'rating': 'Rating', 'userId': '#Ratings'})
    rank.index = rank.reset_index().index+1
    return rank

def movie_recommendation_user_based(id, n): # id of the user
    users_items_sparse = pd.pivot_table(data=ratings_df,
                                        values='rating',
                                        index='userId',
                                        columns='movieId')
  
  
    mid = (ratings_df['rating'].min() + ratings_df['rating'].max())/2
    users_items = users_items_sparse.fillna(mid)
    user_similarities = pd.DataFrame(cosine_similarity(users_items),
                                    columns=users_items.index, 
                                    index=users_items.index)

    not_watched_movies = (users_items.loc[users_items.index!=id, users_items_sparse.loc[id,:].isna()])
    weights = user_similarities.query("userId!=@id")[id] / sum(user_similarities.query("userId!=@id")[id])
  
    weighted_averages = pd.DataFrame(not_watched_movies.T.dot(weights), columns=["predicted_rating"])

    recommendations = weighted_averages.merge(movies_df, left_index=True, right_on="movieId").sort_values("predicted_rating", ascending=False).head(n)
    recommendations.index = recommendations.reset_index().index +1 

    return recommendations[["title", "genres"]]

def user_recommend():
    username = st.text_input("username")
    if username:
        try:
            username = int(username)
        except:
            st.write("username needs to be number")
        if isinstance(username, int) & (username in ratings_df.userId.unique()):
            st.header("Chosen for You:")
            st.table(movie_recommendation_user_based(username, 5))
        else:
            st.write('No valid username detected.')



def movie_recommendation_item_based(id, n): #id of a movie
    # Get the ratings of a target restuarant without NA values
    movies_crosstab = pd.pivot_table(data=ratings_df, values='rating', index='userId', columns='movieId')
    my_movie_ratings = movies_crosstab[id]
    my_movie_ratings = my_movie_ratings[my_movie_ratings>=0]

    movie_similarities = movies_crosstab.corrwith(my_movie_ratings)
    movie_similarities.dropna(inplace=True)

    corr_my_movie = pd.DataFrame(movie_similarities, columns=['PearsonR'])
    corr_my_movie.dropna(inplace=True)

    rating = pd.DataFrame(ratings_df.groupby('movieId')['rating'].mean())
    rating['rating_count'] = ratings_df.groupby('movieId')['rating'].count()

    my_movie_corr_summary = corr_my_movie.join(rating['rating_count'])
    my_movie_corr_summary.drop(id, inplace=True) # drop my_movie itself

    top_similar = my_movie_corr_summary[my_movie_corr_summary['rating_count']>=10].sort_values('PearsonR', ascending=False).head(n)
    top_similar = top_similar.merge(movies_df, on= 'movieId')
    top_similar.index = top_similar.reset_index().index +1

    return top_similar[['title', 'genres']]

def get_movie_id(film):
    return movies_df[movies_df['title']==film]['movieId'].values[0]
    
def chatbot():
    st.header("Let us help You!")
    moviename = st.text_input("Tell me a movie you like and I'll suggest something similar!")
    if moviename:
        suggestions = movies_df["title"].str.lower().str.contains(moviename.lower())
        if suggestions.any():
            if suggestions.sum() == 1:
                film = movies_df[suggestions]['title'].values[0]
                st.write(f"Here's some movies similar to \"{film}\":")
                st.table(movie_recommendation_item_based(get_movie_id(film), 3))
            else:
                st.write('I have found multiple movies!')
                choice = movies_df[suggestions]['title']
                choice.index = choice.reset_index().index +1
                st.table(choice)
                select = st.text_input("Please pick from the list.")
                if select:
                    try:
                        select = int(select)
                    except:
                        st.write("pick a number")
                    if isinstance(select, int):
                        #We should really test to see that this is a valid number!
                        movieno = movies_df[suggestions].iloc[select-1]['title']
                        st.write(f"Here's some movies similar to \"{movieno}\":")
                        st.table(movie_recommendation_item_based(get_movie_id(movieno), 3))

                
        else:
            st.write("Sorry, I couldn't find that.")

def search_engine():
    moviename = st.text_input('Search')
    if moviename:
        suggestions = movies_df["title"].str.lower().str.contains(moviename.lower())
        if suggestions.any():
            found = movies_df[suggestions][['title', 'genres', 'year']]
            found.index = found.reset_index().index +1
            st.table(found)
        else:
            st.write("No movies with this name in database.")

def main():
    get_data()
    st.title('WBSFlix')
    
    search_engine()

    user_recommend()

    st.header('Best rated Movies!')
    st.table(best_rated(10))

    chatbot()
    
main()
