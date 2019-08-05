import requests
import json
from bs4 import BeautifulSoup
import datetime
import csv
import datetime


def main():
    main_page_url = 'https://www.villagecinemas.gr/el/tainies/paizontai-tora/'
    # get all the movies with their links from the main page
    crawl_main_page(main_page_url)


# method that crawls the main page of village cinemas for every movie's title and url
def crawl_main_page(url):

    r = requests.get(url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    movies_boxes = soup.findAll('div', {'class': 'movie_box'})

    # iterate the movie boxes and save the important info (links, titles, etc) to a dictionary
    movie_info_dict = {}
    for movie in movies_boxes:
        link = movie.find('a')['href']
        title = movie.find('div', {'class': 'box_title2'}).text
        movie_info_dict[title] = 'https://www.villagecinemas.gr'+link

    return movie_info_dict


def crawl_movie_page(movie_url):

    r = requests.get(movie_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    # iterate all the views in every cinema and extract usefull info
    views_container = soup.findAll('div', {'class': 'view'})
    cinema_program_per_hall_dict = {}
    for view in views_container:
        cinema_title = view.find('div', {'class': 'cinema FloatLeft'}).text
        # find all the halls that the cinema is screening the movie
        halls_container = view.findAll('div', {'class': 'hall_container'})
        hall_program_per_day_dict = {}
        for hall in halls_container:
            hall_name = hall.find('div', {'class': 'hall_title'}).text.lstrip().rstrip()
            # iterate all the dates that the specific cinema is showing this movie and extract the date info
            view_dates = hall.findAll('div', {'class': 'hall_row row'})
            dates_list = []
            for date in view_dates:
                # the tag has the attribute in the following format: MON. 7/8
                # So, i first split the string on the space to take the second part and then I split on the "/" to seperate
                # the day and the month
                day_month_combo = date.find('div', {'class': 'date FloatLeft'}).text.split(" ")[1].split("/")
                day = day_month_combo[0]
                month = day_month_combo[1]
                starting_times = date.findAll('div', {'class': 'hour FloatLeft'})
                times_list = [time.text for time in starting_times]
                dates_list.append({'day': day, 'month': month, 'starting_times': times_list})
            hall_program_per_day_dict[hall_name] = dates_list.copy()
            cinema_program_per_hall_dict[cinema_title] = hall_program_per_day_dict.copy()


# get all the movie's ids from the main page
def get_movie_ids_list(main_page_url):

    r = requests.get(main_page_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    # half of the movies belong to the class 'media media_item_first vc-movie vc-process' and the other half belong to
    # the class 'media media_item_sec vc-movie vc-process'. So i have to do the same thing twice. Weird flex but ok...
    movies_ids_list = []
    movies_container = soup.findAll('div', {'class': 'media media_item_first vc-movie vc-process'})
    for movie in movies_container:
        movies_ids_list.append(movie['data-vc-movie'])

    movies_container = soup.findAll('div', {'class': 'media media_item_sec vc-movie vc-process'})
    for movie in movies_container:
        movies_ids_list.append(movie['data-vc-movie'])

    return movies_ids_list


def get_cinemas_list(main_page_url):

    r = requests.get(main_page_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    screening_halls_container = soup.findAll('a', {'class': 'datepick vc-cinema vc-process'})
    screening_halls_ids_list = []
    for hall in screening_halls_container:
        screening_hall_name = hall.find('span').text
        screening_halls_ids_list.append(hall['data-vc-cinema'])

    return screening_halls_ids_list


def experimental_Crawler():
    main_page_url = 'https://www.villagecinemas.gr/WebTicketing/'
    movies_ids_list = get_movie_ids_list(main_page_url)
    cinemas_ids_list = get_cinemas_list(main_page_url)
    screenings_data = []

    for movie_id in movies_ids_list:
        for cinema_id in cinemas_ids_list:

            page_url = 'https://www.villagecinemas.gr/WebTicketing/?CinemaCode='+cinema_id+'&MovieCode='+movie_id
            r = requests.get(page_url)
            url = r.content
            soup = BeautifulSoup(url, 'html.parser')

            # this container will always have data, even if there are no dates available for the specific movie-cinema_hall combination
            possible_screening_dates_container = soup.find('div', {'class': 'choose-day'})

            # this call will determine if the movie-cinema_hall combination has available date (The list will have elements or
            # it will be empty)
            possible_dates_list = possible_screening_dates_container.findAll('a', {'class': 'datepick'})
            dates_ids_list = []
            dates_dict = {}
            if len(possible_dates_list) > 0:
                print('Yes!!!) cinema_id:'+cinema_id+'   movie_id:'+movie_id+'  ->   '+page_url)

                for screening_date_container in possible_dates_list:
                    date_code = screening_date_container['data-vc-selecteddate']
                    dates_ids_list.append(date_code)
                # print('dates_ids_list: '+str(dates_ids_list))
                for date_id in dates_ids_list:
                    # print('date_id: '+str(date_id))
                    screening_info_list = []
                    times_container = soup.find('div', {'id': 'timeof' + date_id}).findAll('a')
                    # print('times_container: '+str(times_container))
                    for time in times_container:
                        # print('time: '+str(time))
                        time_id = time['id']
                        starting_time = time.find('span', {'class': 'str-time'}).text
                        screening_hall = time.find('span', {'class': 'type-item'}).text
                        ticket_selection_url = 'https://www.villagecinemas.gr/WebTicketing/TicketsSelection?CinemaCode='+cinema_id+'&SessionId='+time_id
                        screening_info_list.append({'time_id': time_id, 'screening_hall': screening_hall, 'starting_time': starting_time, 'ticket_selection_url': ticket_selection_url})
                    dates_dict[date_id] = screening_info_list
                # print(movie_id+'    '+cinema_id)
                # print(str(dates_dict))
                screenings_data.append({'movie_id': movie_id, 'cinema_id': cinema_id, 'dates': dates_dict.copy()})
            else:
                print('Nope) cinema_id:'+cinema_id+'   movie_id:'+movie_id+'  ->   '+page_url)

