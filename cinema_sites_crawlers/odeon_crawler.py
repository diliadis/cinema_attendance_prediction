import requests
import json
from bs4 import BeautifulSoup
import datetime
import csv
import re


def main():
    main_page_url = 'https://www.i-ticket.gr/main/evtypes.jsp?evsubid=0002'
    data_list = []
    movies_urls_list = get_movies_urls_from_main_page(main_page_url)

    for movie_url in movies_urls_list:
        print('movie: '+movie_url)
        cinemas_urls_list = get_cinema_halls_urls(movie_url)

        for cinema_url in cinemas_urls_list:
            print('         cinema: '+cinema_url)
            screening_times_urls_list = get_dates_urls(cinema_url)

            for screening_times_url in screening_times_urls_list:
                print('             screening: '+str(screening_times_url))

                url = 'https://www.i-ticket.gr/main/insticket_res.jsp?PLACE=02469&CG1=1&CGNOALLOWED1=1.0000000000&HD1=1&' \
                      'CG2=0&CGNOALLOWED2=1.0000000000&HD2=2&' \
                      'CG3=0&CGNOALLOWED3=1.0000000000&HD3=244&' \
                      'CG4=0&CGNOALLOWED4=1.0000000000&HD4=3&' \
                      'CG5=0&CGNOALLOWED5=2.0000000000&HD5=36&' \
                      'CG6=0&CGNOALLOWED6=2.0000000000&HD6=5&' \
                      'CG7=0&CGNOALLOWED7=1.0000000000&HD7=68&' \
                      'CG8=0&CGNOALLOWED8=2.0000000000&HD8=880&' \
                      'TOTAL=8&SCD_ID='+screening_times_url['scdid']+'&multiid='+screening_times_url['multiid']+'&' \
                      'eventid='+screening_times_url['eventid']+'&lng=0&cmdOK=%CE%A3%CE%A5%CE%9D%CE%95%CE%A7%CE%95%CE%99%CE%91'

                screening_info = get_seat_counts(url)
                if screening_info is not None:
                    movie_title, cinema_name, cinema_hall_name, starting_time, date, reserved_seats_count, available_seats_count = screening_info

                    d = {'date': date, 'starting_time': starting_time, 'cinema_name': cinema_name, 'screening_hall': cinema_hall_name,
                                      'movie_title': movie_title, 'free': available_seats_count, 'sold': reserved_seats_count}
                    print('                         '+str(d))
                    data_list.append(d)

    dict_to_csv(data_list, '../datasets/odeon_csvs/dataset.csv')


def dict_to_csv(list_of_dicts, filename):
    keys = list_of_dicts[0].keys()

    with open(filename, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)

def get_movies_urls_from_main_page(main_page_url):
    r = requests.get(main_page_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    movies_container = soup.findAll('td', {'bgcolor': '#C0EF42'})
    # iterate the main page to extract the urls for every movie available
    movies_urls_list = []
    for movie in movies_container:
        movies_urls_list.append('https://www.i-ticket.gr/main/'+movie.find('a')['href'])

    return movies_urls_list


def get_cinema_halls_urls(movie_url):
    r = requests.get(movie_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    cinemas_container = soup.findAll('span', {'class': 'style2'})
    # pop the first element because it has nothing to do with the cinema halls. Is is actually the title of the movie
    del cinemas_container[0]
    cinemas_urls_list = []
    for cinema_hall in cinemas_container:
        cinemas_urls_list.append('https://www.i-ticket.gr/main/'+cinema_hall.find('a')['href'])

    return cinemas_urls_list


def get_dates_urls(cinema_url):
    # cinema_url = 'https://www.i-ticket.gr/main/scheduled.jsp?eventid=7110&multiid=00025'
    r = requests.get(cinema_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    screening_times_urls_list = []
    screening_times_container = soup.findAll('td', {('bgcolor'): ('#0066FF')})
    for screening_time in screening_times_container:
        sub_url = screening_time.find('a')['href']
        multiid = re.search('multiid=(.+?)&', sub_url).group(1)
        scdid = re.search('scdid=(.+?)&', sub_url).group(1)
        eventid = re.search('eventid=(.+?)&', sub_url).group(1)

        screening_times_urls_list.append({'multiid': multiid, 'scdid': scdid, 'eventid': eventid})

    return screening_times_urls_list


def get_seat_counts(screening_time_url):

    r = requests.get(screening_time_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    reserved_seats_list = soup.findAll('td', {('bgcolor'): ('#0000FF')})
    available_seats_list = soup.findAll('td', {('bgcolor'): ('#00CCFF')})
    reserved_seats_count = len(reserved_seats_list)-3 # the -3 is added because there are 3 elements with the same color that are not actually free seats
    available_seats_count = len(available_seats_list)+1 # the +1 is for the seat that i have selected and has another color

    movie_title_element = soup.find('span', {('class'): ('style18')})
    if movie_title_element is not None:
        movie_title = movie_title_element.text.strip()
        cinema_hall_name = soup.find('b').find('u').text
        cinema_name = soup.find('span', {('class'): ('style12')}).text.split('-')[0]
        starting_time = soup.find('b').find('font').text
        temp_date_string = soup.find('b').text.split('\n')[1].strip().split(' ')
        date = temp_date_string[1]+' '+temp_date_string[2]+' '+temp_date_string[3]

        return [movie_title, cinema_name, cinema_hall_name, starting_time, date, reserved_seats_count, available_seats_count]
    else:
        print('This is a summer hall screening and you cannot choose where you sit')
        return None


main()

