import urllib.request
import json
import omdb_keys as keys
import os
import pandas as pd


def get_movie_json(movie_title):
    temp_movie_title = movie_title.replace(' ', '_').lower()
    url = 'http://www.omdbapi.com/?t='+temp_movie_title.encode("ascii", errors="ignore").decode()+'&y=2019&apikey='+keys.apikey
    data = json.load(urllib.request.urlopen(url))
    print(str(data))
    return data


def load_csv_to_dataframe(filename):
    data = None
    if os.path.isfile(filename):
        data = pd.read_csv(filename)
    else:
        print("The file "+str(filename)+" doesn't exists...")
    return data


def get_movie_info():

    movies_info_list = []
    data = load_csv_to_dataframe('datasets/odeon_csvs/dataset.csv')
    movie_titles_list = data['movie_title'].unique().tolist()

    for movie_title in movie_titles_list:
        # many movie titles have aditional info about the language and the screening tech that uses
        filtered_movie_title = movie_title.replace('(3D)', '').replace('(GR)', '').replace('(ENG)', '')
        print('getting info for '+filtered_movie_title)
        movie_json_info = get_movie_json(filtered_movie_title)
        movies_info_list.append(movie_json_info)