import requests
from bs4 import BeautifulSoup
import datetime


def crawl_movie_page(movie_title):
    main_page_url = 'https://www.rottentomatoes.com/m/'
    # remove spaces before and after the title and replace all the spaces between the words with underscores
    temp_movie_title = movie_title.strip().replace('-', '_').replace(' ', '_').replace(':', '').lower()
    '''
        sometimes the link has to have the year of the movie in the end because there already exist movies with the same
        title. For this reason i create a list that holds my different endings for the final url. These endings will be
        tested until one of them returns the info we want.
        
        For example if i want to crawl the page for the movie 'The lion king' that was released in 2019 i will have to use
        the following link   https://www.rottentomatoes.com/m/the_lion_king_2019. If i use the same link but without the
        2019 in the end i will end up in the page for the original 'The lion king' that was released in 1994.
    
    '''
    posible_titles_list = []
    posible_titles_list.append(main_page_url+temp_movie_title)

    current_year = str(datetime.datetime.now().year)
    posible_titles_list.append(main_page_url+temp_movie_title+'_'+current_year)

    if 'the' not in temp_movie_title:
        posible_titles_list.append(main_page_url+'the_'+temp_movie_title)
        posible_titles_list.append(main_page_url+'the_'+temp_movie_title + '_' + current_year)


    correct_link_found = False
    for link_version in posible_titles_list:
        r = requests.get(link_version)
        url = r.content
        soup = BeautifulSoup(url, 'html.parser')

        # check if there is something wrong with the page we get from rotten tomatoes
        if check_for_current_year(r.status_code, soup) and (r.status_code != 404):
            correct_link_found = True
            break
        else:
            print(link_version+'   Denied')

    result = {}
    if not correct_link_found:
        print("could not find a suitable version of the movie's title that was accepter by rotten tomatoes...")
    else:
        print(link_version+' did the trick')
        critics_container = soup.find('section', {'class': 'mop-ratings-wrap__row js-scoreboard-container'})
        tomatometer_percentage = critics_container.find('span', {'class': 'mop-ratings-wrap__percentage'}).text.strip()[:-1]
        tomatometer_total_count = critics_container.find('small', {'class': 'mop-ratings-wrap__text--small'}).text.strip()

        audience_container = soup.find('div', {'class': 'mop-ratings-wrap__half audience-score'})
        audience_rating_percentage = audience_container.find('span', {'class': 'mop-ratings-wrap__percentage'}).text.strip()[:-1]
        audience_ratings_num = audience_container.find('strong', {'class': 'mop-ratings-wrap__text--small'}).text.split('Verified Ratings: ')[1]

    result = {'tomatometer_percentage': tomatometer_percentage, 'tomatometer_votes': tomatometer_total_count,
         'audience_rating_percentage': audience_rating_percentage, 'audience_votes': audience_ratings_num}

    return result


# method that checks if the movie page we load is of the correct movie. One way to do that is to check if the movie
# was released the current year.
def check_for_current_year(status_code, html_soup):
    if status_code == 404:
        result = False
    else:
        current_year = datetime.datetime.now().year
        movie_release_year = int(html_soup.find('div', string='In Theaters: ').parent()[1].find('time').text[-4:])

        if current_year == movie_release_year:
            result = True
        else:
            result = False

    return result





