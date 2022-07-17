"""

"""

import re
import json

from bs4 import BeautifulSoup
from fastapi import FastAPI
from urllib.request import urlopen, Request
from fuzzywuzzy import fuzz


app = FastAPI()

@app.get("/medium")
async def root():
    url = 'https://medium.com/swlh/high-performers-dont-quit-jobs-they-quietly-quit-these-things-e4eff96d4c51'

    req = Request(url, headers = {'User-Agent': 'XYZ/3.0'})
    webpage = urlopen(req, timeout=10)
    #return webpage
    html = webpage
    print(html.read())
    soup = BeautifulSoup(html.read(), 'html.parser')
    return soup

def get_lastest():
    pass

def scrape():
    #url = 'https://medium.com/swlh/high-performers-dont-quit-jobs-they-quietly-quit-these-things-e4eff96d4c51'
    url = "https://medium.com/@anas_ali/gpt-3-a-deep-learning-model-for-natural-language-406afde92733?source=tag_archive---------3-----------------------"    #


    # first is sign in
    # second is my user agent while incognito
    user_agents = [
        'Mozilla/5.0 (X11; CrOS x86_64 10066.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
        'XYZ/3.0',
        'Mozilla/5.0']


    req = Request(url, headers={'User-Agent': user_agents[3]})
    page = urlopen(req, timeout=10)
    soup = BeautifulSoup(page, 'html.parser')

    #text
    body_text = ""
    text_boxes = list(soup.body.article.find_all("p"))
    for t in text_boxes:
        body_text += " "
        body_text += t.get_text()

    #headers
    h1_headers = [h.get_text() for h in soup.body.find_all('h1')]
    h2_headers = [h.get_text() for h in soup.body.find_all('h2')]
    h3_headers = [h.get_text() for h in soup.body.find_all('h3')]
    h4_headers = [h.get_text() for h in soup.body.find_all('h4')]
    h5_headers = [h.get_text() for h in soup.body.find_all('h5')]
    h6_headers = [h.get_text() for h in soup.body.find_all('h6')]

    content = str(soup.find(property="article:author")).split(" ")[1]
    author_page = content.split('"')[1]
    author = author_page.split('/')[-1][1:]

    # yeah yeah DRY whatever
    content = str(soup.find(property="article:published_time")).split(" ")[1]
    published_time = content.split('"')[1]


    # title,  formatted like "My Title | By author lastname | Medium"
    title = soup.head.title.get_text()
    title_text = title.split("|")[0].strip()
    # covers special case if '|' char in title (which is allowed),
    # title_text = "".join(title.split("|")[:-2])

    # claps and responses
    claps = None
    responses = None
    reading_time = None

    #parse "window.__APOLLO_STATE__", a script where a bunch of data is stored
    apollo_window = "window.__APOLLO_STATE__ = "
    pattern = re.compile("^" + apollo_window)
    apollo = soup.body.find("script", text=pattern).string
    if apollo.startswith(apollo_window):
        apollo = apollo[len(apollo_window):]
        x = json.loads(apollo)

        # get posts from script where title matches
        posts = [x[p] for p in x.keys() if p.startswith("Post")]
        # fuzzy match because of annoying character
        posts = [p for p in posts if fuzz.ratio(title, p["title"]) > 0.9]
        if posts: # because of the fuzzy match, this could be totally wrong

            # with this method clapCount is parsed as an int, but some articles have Claps as something like "2.1K"
            # and maybe it's stored as string, and I would need to convert to 2100
            claps = posts[0]["clapCount"]
            responses = posts[0]["postResponses"]["count"]
            reading_time = posts[0]["readingTime"]

    data_model = {
        "author_page": author_page,
        "author": author,
        "article_title": title_text,
        "images": None,
        "date_published": published_time,
        "date_accessed": None,
        "reading_time": reading_time,
        "claps": claps,
        "responses": responses,
        "article_url": url,
        "text": body_text,
        "h1_headers": h1_headers,
        "h2_headers": h2_headers,
        "h3_headers": h3_headers,
        "h4_headers": h4_headers,
        "h5_headers": h5_headers,
        "h6_headers": h6_headers,
    }
    # other things which can be added:
        # shares on facebook, linkedin, twitter, etc.

    print(data_model)

if __name__ == '__main__':
    scrape()
