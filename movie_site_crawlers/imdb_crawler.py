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
