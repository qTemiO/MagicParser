from bs4 import BeautifulSoup as BS
import pandas as pd
import requests

from loguru import logger

HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'ru,en;q=0.9',
    'Connection': 'keep-alive',
    'Cookie': 'lastLogin=2459372.063; LastLoginDT=06-06-2021%2006%3A30%20AM; DaysPrune=10; NameStorage=yes; Password=temio; UserName=Temio',
    'Host': 'forums.magictraders.com',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 YaBrowser/21.5.2.638 Yowser/2.5 Safari/537.36'
}

PARSER_TEST_LIMIT = 2
PARSER_ITEM_TEST_LIMIT = 20

def parseProfile(url):
    req = requests.get(url, headers=HEADERS).text
    soup = BS(req, 'lxml')
    name = soup.find('b').text.replace('Profile for ', '')
    email = ''
    tables = soup.find_all('table')
    trs = tables[len(tables) - 1].find_all('tr')
    
    for tr in trs[:len(trs) - 2]:
        key = tr.find_all('td')[0].text
        value = tr.find_all('td')[1].text
        key = key.replace('\n', '')
        if 'Current Email' in key: email = value

    email = email.replace('@', '%40')
    email = email.replace('.', '%2e')

    data = {
        'email': email[:-1],
        'name': name
    }
    return data

def collectPageUrls(pageUrl):
    page_urls = []

    req = requests.get(pageUrl, headers=HEADERS).text
    soup = BS(req, 'lxml')
    tables = soup.find_all('table')
    table = tables[len(tables) - 1]
    trs = table.find_all('tr')
    for tr in trs[1:]:
        page_urls.append(tr.find('td').find('a')['href'])
    return list(set(page_urls))

def collectLetterPageUrls(letterUrl):
    letter_urls = []
    pattern_url = letterUrl

    req = requests.get(letterUrl, headers=HEADERS).text
    soup = BS(req, 'lxml')
    a = soup.find_all('a')
    last_page = a[len(a) - 1].text
    for page in range(int(last_page)):
        end = pattern_url[pattern_url.find('=')+2:]
        begining = pattern_url[:pattern_url.find('=')+1]
        url = begining + str(page+1) + end
        letter_urls.append(url)
    return letter_urls

def collectLettersUrls(siteUrl):
    req = requests.get(siteUrl, headers=HEADERS).text
    soup = BS(req, 'lxml')
    alphabet = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z'
    alphabet = alphabet.split()

    urls = []

    for letter in alphabet:
        urls.append(siteUrl[:len(siteUrl) - 1] + letter)
    return urls

def parse():
    letterUrls = collectLettersUrls('http://forums.magictraders.com/memberlist.cgi?page=1&sortby=&letter=X')
    df = pd.DataFrame(columns=['Name', 'Email'])

    if PARSER_TEST_LIMIT < len(letterUrls):
        limit = PARSER_TEST_LIMIT
    else:
        limit = len(letterUrls)

    totalPageUrls = []
    for letterUrl in letterUrls[:limit]:
        logger.info(f'Current letter - { letterUrl }')
        pageUrls = collectLetterPageUrls(letterUrl)
        for pageUrl in pageUrls:
            totalPageUrls.append(pageUrl)
        logger.debug(f'Current pages length - { len(totalPageUrls) }')

    logger.success(f'\nPage urls collected!\nTotal urls - { len(totalPageUrls) }')
    
    if PARSER_TEST_LIMIT < len(totalPageUrls):
        limit = PARSER_TEST_LIMIT
    else:
        limit = len(totalPageUrls)

    totalProfileUrls = []
    for pageUrl in totalPageUrls[:limit]:
        profileUrls = collectPageUrls(pageUrl)
        for url in profileUrls:
            totalProfileUrls.append(url)
            #logger.debug(url)

    logger.success(f'Profiles urls collected { len(totalProfileUrls) }')

    if PARSER_ITEM_TEST_LIMIT < len(totalProfileUrls):
        limit = PARSER_ITEM_TEST_LIMIT
    else:
        limit = len(totalProfileUrls)

    for profileUrl in totalProfileUrls[:limit]:
        data = parseProfile(profileUrl)
        df = df.append({'Name': data['name'], 'Email': data['email']}, ignore_index=True)
    return df

df = parse()
df.to_excel('collected.xlsx', engine='xlsxwriter')

with open("collected.txt", "w") as file:
    for index in range(len(df)):
        data = (f"{df['Name'][index] } - { df['Email'][index] }\n")
        file.write(data)