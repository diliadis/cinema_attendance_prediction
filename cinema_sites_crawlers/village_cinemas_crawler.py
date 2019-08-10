import requests
from bs4 import BeautifulSoup
import csv
import time
import pickle
import os
import datetime
import gmail_auth
import smtplib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


def main():
    # main_page_url = 'https://www.villagecinemas.gr/el/tainies/paizontai-tora/'
    # get all the movies with their links from the main page
    # crawl_main_page(main_page_url)

    main_page_url = 'https://www.villagecinemas.gr/WebTicketing/'
    if os.path.isfile('../datasets/village_cinemas_csvs/dataset.txt'):
        with open('../datasets/village_cinemas_csvs/dataset.txt', "rb") as fp:  # Unpickling
            screenings_data = pickle.load(fp)
    else:
        screenings_data = get_scan_of_screening_schedules(main_page_url)
        with open('../datasets/village_cinemas_csvs/dataset.txt', "wb") as fp:  # Pickling
            pickle.dump(screenings_data, fp)

    data_list = get_seats_per_screening(main_page_url, screenings_data)


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


def get_cinemas_ids_list(main_page_url):

    r = requests.get(main_page_url)
    url = r.content
    soup = BeautifulSoup(url, 'html.parser')

    screening_halls_container = soup.findAll('a', {'class': 'datepick vc-cinema vc-process'})
    screening_halls_ids_list = []
    for hall in screening_halls_container:
        screening_hall_name = hall.find('span').text
        screening_halls_ids_list.append(hall['data-vc-cinema'])

    return screening_halls_ids_list


def get_scan_of_screening_schedules(main_page_url):

    movies_ids_list = get_movie_ids_list(main_page_url)
    cinemas_ids_list = get_cinemas_ids_list(main_page_url)
    screenings_data = []

    r = requests.post(main_page_url)
    main_page_cookies = r.cookies

    for movie_id in movies_ids_list:
        page_url = 'https://www.villagecinemas.gr/WebTicketing/?MovieCode=' + movie_id
        r = requests.post(page_url)
        url = r.content
        soup = BeautifulSoup(url, 'html.parser')

        # extract the movie title
        movie_title_container = soup.find(attrs={"data-vc-movie": movie_id})
        movie_title = movie_title_container.findAll('h5')[-1].text
        print(movie_title)

        for cinema_id in cinemas_ids_list:
            print('cinema_id:' + cinema_id + '   movie_id:' + movie_id)
            # cinema_id = '21'
            # movie_id = 'HO00105127'
            page_url = 'https://www.villagecinemas.gr/WebTicketing/?CinemaCode='+cinema_id+'&MovieCode='+movie_id
            # r = requests.get(page_url)
            r = requests.post(page_url)
            url = r.content
            soup = BeautifulSoup(url, 'html.parser')

            # extract the cinema_name
            cinema_name_container = soup.find(attrs={"data-vc-cinema" : cinema_id})
            cinema_name = cinema_name_container.find('span').text
            print(cinema_name)

            # this container will always have data, even if there are no dates available for the specific movie-cinema_
            # hall combination
            possible_screening_dates_container = soup.find('div', {'class': 'choose-day'})

            # this call will determine if the movie-cinema_hall combination has available date (The list will have
            # elements or it will be empty)
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
                    screening_info_list = []
                    # every time element has an id with a value the corresponds to a specific day (the data-vc-
                    # selecteddate value of that day element)
                    times_container = soup.find('div', {'id': 'timeof' + date_id}).findAll('a')
                    for time in times_container:
                        time_id = time['id']
                        starting_time = time.find('span', {'class': 'str-time'}).text
                        screening_hall = time.find('span', {'class': 'type-item'}).text
                        ticket_selection_url = 'https://www.villagecinemas.gr/WebTicketing/TicketsSelection?CinemaCode='+cinema_id+'&SessionId='+time_id+'&RenewSession=True'
                        screening_info_list.append({'time_id': time_id, 'screening_hall': screening_hall, 'starting_time': starting_time, 'ticket_selection_url': ticket_selection_url})
                    dates_dict[date_id] = screening_info_list
                screenings_data.append({'movie_id': movie_id, 'movie_title': movie_title, 'cinema_id': cinema_id, 'cinema_name': cinema_name, 'dates': dates_dict.copy()})
            else:
                print('Nope) cinema_id:'+cinema_id+'   movie_id:'+movie_id+'  ->   '+page_url)

    return screenings_data


# a crawler for a specific screening that uses selenium (the window_mode can also take the value visible)
# selenium_crawler("https://www.villagecinemas.gr/WebTicketing", 'HO00105127', '21', '20191009', '206437', window_mode='silent')
def get_seats_html_with_selenium_crawler(main_page_url, movie_id, cinema_id, day_id, time_id, window_mode='silent'):
    if window_mode == 'silent':
        options = Options()
        options.add_argument('--headless')
        driver = webdriver.Chrome(options=options)
    elif window_mode == 'visible':
        driver = webdriver.Chrome()
    result = None
    # go the main page
    driver.get("https://www.villagecinemas.gr/WebTicketing")
    try:
        # click on the movie
        movie_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-vc-movie='"+movie_id+"']"))
        )
        movie_element.click()
        print('click on movie done')

        # click on the cinema hall
        cinema_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-vc-cinema='"+cinema_id+"']"))
        )
        cinema_element.click()
        print('click on cinema done')

        # click on the date
        day_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@data-vc-selecteddate='"+day_id+"']"))
        )
        day_element.click()
        print('click on day done')

        # click on time
        time_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[@id='"+time_id+"']"))
        )
        actionChains = ActionChains(driver)
        actionChains.double_click(time_element).perform()
        print('double click on time done')

        # increase the ticket counter by one
        increase_ticket_count_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div/input[@data-vc-ticketname='Eticket ' or @data-vc-ticketname='Eticket' or @data-vc-ticketname='Special events Eticket']/../div[@class='inc button']"))
        )
        increase_ticket_count_element.click()
        print('click on ticket counter done')

        # click to submit the form
        submit_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//button[@type='submit']"))
        )
        submit_element.click()
        print('click on submit done')

        # wait until this element is loaded, so that you can obtain the html script that contains the
        # seating arrangement
        seat_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@class='col-xs-3 comments comment-seat-left']"))
        )
        print('waiting on seat element to load done')

        html = driver.page_source

        result = BeautifulSoup(html, 'html.parser')
    except:
        print('There is a network issue...')
    finally:
        driver.quit()

    return result


# gets the html of the seating arrangements page and returns the number of available and reserved seats
def get_available_and_reserved_seats(html_soup):

    # container with the available seats
    available_seats_container = html_soup.findAll('form', {'class': 'seats seat-available'})
    # container with the reserved seats
    reserved_seats_container = html_soup.findAll('span', {'class': 'seats seat-not-available'})

    # i increment the number of available seats by one to include the seat that is selected for me and belows to the
    # 'seats seat-choiced' class
    return len(available_seats_container)+1, len(reserved_seats_container)


def get_seats_per_screening(main_page_url, screenings_data):
    data_list = []
    screenings_counter = 0
    for i in screenings_data:
        movie_id = i['movie_id']
        cinema_id = i['cinema_id']
        cinema_name = i['cinema_name']
        movie_title = i['movie_title']
        dates = i['dates']
        for day_id, l in dates.items():
            for specific_screening_info in l:
                screenings_counter += 1
                time_id = specific_screening_info['time_id']
                print(str(screenings_counter)+') Crawling for -> movie_id:' + movie_id + ' / ' + 'cinema_id:' + cinema_id + ' / ' + 'date_id:' + day_id + ' / ' + 'time_id:' + time_id)
                start_time = time.time()
                seats_found = False
                false_connection_counter = 0
                # if you are unable to get the seats html for 10 consecutive times send an email to notify the user
                while (not seats_found) and (false_connection_counter < 10):
                    # use the selenium crawler to get the html for the seating arrangements
                    html_soup = get_seats_html_with_selenium_crawler(main_page_url, movie_id, cinema_id, day_id, time_id,
                                                         window_mode='visible')
                    print('completed in '+str(time.time() - start_time)+' secs')
                    if html_soup is None:
                        false_connection_counter += 1
                        print('Something went wrong!!!!!!!!!!!')
                        print('Trying again !!!!!!!!!!!!!!!')
                    else:
                        seats_found = True
                if false_connection_counter == 10:
                    send_email('There is something wrong with the village_cinemas_crawler!!!', 'check your program')

                # get the number of available and reserved seats for the specific screening
                num_available, num_reserved = get_available_and_reserved_seats(html_soup)
                print('available: '+str(num_available)+'    /    reserved: '+str(num_reserved))
                d = {'date': day_id, 'starting_time': specific_screening_info['starting_time'], 'cinema_name': cinema_name,
                     'screening_hall': specific_screening_info['screening_hall'],
                     'movie_title': movie_title, 'free': num_available, 'sold': num_reserved}
                data_list.append(d)

    current_date = datetime.date.today()
    current_time = datetime.datetime.now().time()
    file_name = str(current_date)+'_'+current_time.strftime("%H:%M:%S")
    dict_to_csv(data_list, 'village_cinemas_csvs/attendance_per_screening_'+file_name+'.csv')

    return data_list


def dict_to_csv(list_of_dicts, filename):
    keys = list_of_dicts[0].keys()

    with open(filename, 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(list_of_dicts)


# method that sends and email to the user. It is used when the program has difficulty with the selenium crawler
def send_email(subject, body):
    gmail_user = gmail_auth.gmail_username
    gmail_password = gmail_auth.gmnail_password

    sent_from = gmail_user
    to = ['JimmyHliad@gmail.com']
    subject = subject
    body = body

    email_text = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sent_from, ", ".join(to), subject, body)

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()

        print('Email sent!')
    except:
        print('Something went wrong with the email......')


main()