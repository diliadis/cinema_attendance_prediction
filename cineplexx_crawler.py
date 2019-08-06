import requests
import json
from bs4 import BeautifulSoup
import datetime
import csv
import datetime
import re


def main():
    crawl_main_page()


def crawl_main_page():
    url = 'https://www.cineplexx.gr'
    r = requests.get(url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    images_container = soup.findAll('a')
    movies_counter = 0
    movies_url_list = []
    for i in images_container:
        movie_url = i['href']
        if movie_url.startswith('//www.cineplexx.gr/movie/') and movies_counter < 6:
            movies_counter += 1
            movies_url_list.append(movie_url)


    counter = 0
    for movie_url in movies_url_list:
        start = movie_url.find('movie/')
        movie_name = movie_url[start+len('movie/'):-1]
        print(str(counter)+') '+str(movie_name))
        counter += 1

    choice = input("Give the index of the movie you want to see: ")

    crawl_view(movies_url_list[int(choice)].replace('//', 'https://'))


def crawl_view(url):

    start = url.find('movie/')
    output_file_name = url[start+len('movie/'):-1]
    now = datetime.datetime.now()
    output_file_name += now.strftime("_%Y-%m-%d_%H:%M")

    with open(output_file_name+".csv", "w") as my_empty_csv:
        pass

    my_empty_csv.close()

    data_list = []
    data_list.append(['Date', 'hour', 'screening_hall', 'screening_mode', 'free', 'sold'])

    # url = 'https://www.cineplexx.gr/movie/avengers-endgame/'
    r = requests.get(url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    screenings_per_day_container = soup.findAll('div', {'class': 'row-fluid separator time-row'})

    for daily_screenings in screenings_per_day_container:
        date = daily_screenings.find('time').text
        print(str(date))
        for screening in daily_screenings.findAll('a'):
            starting_time = screening.find('p', {'class': 'time-desc'}).text.strip()
            screening_url = screening['data-link']
            screening_mode = screening.find('p', {'class': 'mode-desc'}).text.strip()
            screening_hall = screening.find('p', {'class': 'room-desc'}).text

            print(starting_time)
            print(screening_url)

            if screening_mode.isspace():
                screening_mode = '2d'
            else:
                print(screening_mode)
            '''
               example of the url 
               https://www.cineplexx.gr/tickets/#/center/670/movie/160174/date/2019-05-11/program/5499/select
               in this example the first_code is 670 and the second_code is 5499
            '''
            # old approach
            # start = screening_url.find('/center/')
            # end = screening_url.find('/movie/')
            # first_code = screening_url[start+len('/center/'):end]
            # new approach
            first_code = re.search('/center/(.+?)/movie/', screening_url).group(1)

            # start = screening_url.find('/program/')
            # end = screening_url.find('/select')
            # second_code = screening_url[start+len('/program/'):end]
            second_code = re.search('/program/(.+?)/select', screening_url).group(1)


            seating_arr_url = 'https://www.cineplexx.gr/restV/cinemas/' + first_code + '/program/' + second_code + '/seat-selection-view/?sessionid=f'

            jsondata = requests.request("GET", seating_arr_url)
            jsondata = jsondata.json()
            seatplan_rows = jsondata['seatPlan']['areas'][0]['rows']
            sold_seats_counter = 0
            free_seats_counter = 0

            for i in seatplan_rows:
                for seat in i['seats']:
                    seat_status = seat['category']
                    if seat_status == 'SOLD':
                        sold_seats_counter += 1
                    else:
                        free_seats_counter += 1
            print('sold seats: '+str(sold_seats_counter))
            print('available seats: '+str(free_seats_counter))
            print('')
            data_list.append([date, starting_time, screening_hall, screening_mode.rstrip(), free_seats_counter, sold_seats_counter])


    with open('cineplexx_csvs/'+output_file_name + ".csv", "w") as csv_File:
        writer = csv.writer(csv_File)
        writer.writerows(data_list)

    csv_File.close()



if __name__ == "__main__": main()