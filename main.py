import datetime
import json
import re

from bs4 import BeautifulSoup
from fastapi import FastAPI
from urllib.request import urlopen, Request
from fuzzywuzzy import fuzz



def get_links():
    # tag list from https://medium.com/feedium/list-of-medium-top-writer-tags-number-of-hits-and-amount-of-writers-34ce3f4234a6
    # given a list of tags where top writer topics are listed, then make a list of archive urls
    # each archive page will have links to the articles published that day.
    # after getting a list of archive urls
    # go through with beautiful soup and scrape the url, and parse the html to get links to articles

    # another thing to try would be to go through each publication
    #     url = f'https://medium.com/{publication_name}/archive/2022/{month}/{day}'
    # https://hackernoon.com/how-to-scrape-a-medium-publication-a-python-tutorial-for-beginners-o8u3t69

    with open("top_writer_topics.txt") as topics:
         topic_list = topics.read()

    # formate topic tags
    tag_list = [tag.replace(" ","-") for tag in topic_list]

    # get the list of archive urls
    url_list = []
    for tag in tag_list:
        for month in range(1, 7): # june is last month, 13 for full year
            if month in [1, 3, 5, 7, 8, 10, 12]:
                n_days = 31
            elif month in [4, 6, 9, 11]:
                n_days = 30
            else:
                n_days = 28

            for day in range(1, n_days + 1):

                month, day = str(month), str(day)

                if len(month) == 1:
                    month = f'0{month}'
                if len(day) == 1:
                    day = f'0{day}'
                url = f'https://medium.com/tag/{tag}/archive/2022/{month}/{day}'
                url_list.append(url)

    # note these urls have a set of "related tags" inside the class "tags tags--postTags tags--light"
    # which could be added to the tags list

    # should be ~100 tags * 100 days ~ 10k urls

    # testing url_list = ["https://medium.com/tag/self-driving-cars/archive/2022/01/17"]
    # get stories
    article_links = []

    for url in url_list:
        try:
            user_agents = [
                'Mozilla/5.0 (X11; CrOS x86_64 10066.0.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
                'XYZ/3.0',
                'Mozilla/5.0']

            req = Request(url, headers={'User-Agent': user_agents[3]})
            page = urlopen(req, timeout=10)
            soup = BeautifulSoup(page, 'html.parser')

            #get links from page
            data_source = soup.find_all('div', attrs={'data-source':True})
            for data in data_source:
                refs = data.find_all('a', attrs={'href':True})

                for r in refs:
                    if r.get('data-action-source'): # odd how '... in r' doesn't work
                        if r['data-action-source'] == 'preview-listing':
                            article_links.append(r['data-action-value'])
        except Exception as e:
            print(e)

        if len(article_links) > 100:
            break
    print(article_links)

    #save links to file
    with open('links.txt', 'w') as file:
        for line in article_links:
            file.write(f"{line}\n")



def scrape(url):
    #url = 'https://medium.com/swlh/high-performers-dont-quit-jobs-they-quietly-quit-these-things-e4eff96d4c51'
    #url = "https://medium.com/@anas_ali/gpt-3-a-deep-learning-model-for-natural-language-406afde92733?source=tag_archive---------3-----------------------"    #

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

    try:
        #text
        body_text = ""
        text_boxes = list(soup.body.article.find_all("p"))
        for t in text_boxes:
            body_text += " "
            body_text += t.get_text()
    except Exception as e:
           print(e)

    try:
        #headers
        h1_headers = [h.get_text() for h in soup.body.find_all('h1')]
        h2_headers = [h.get_text() for h in soup.body.find_all('h2')]
        h3_headers = [h.get_text() for h in soup.body.find_all('h3')]
        h4_headers = [h.get_text() for h in soup.body.find_all('h4')]
        h5_headers = [h.get_text() for h in soup.body.find_all('h5')]
        h6_headers = [h.get_text() for h in soup.body.find_all('h6')]
    except Exception as e:
        print(e)

    try:
        content = str(soup.find(property="article:author")).split(" ")[1]
        author_page = content.split('"')[1]
        author = author_page.split('/')[-1][1:].split('.')[0]
    except Exception as e:
        print(e)

    try:
        # yeah yeah DRY whatever
        content = str(soup.find(property="article:published_time")).split(" ")[1]
        published_time = content.split('"')[1]
        accessed_time = datetime.datetime.utcnow().isoformat() + "Z"

    except Exception as e:
        print(e)

    try:
        # title,  formatted like "My Title | By author lastname | Medium"
        title = soup.head.title.get_text()
        title_text = title.split("|")[0].strip()
        # covers special case if '|' char in title (which is allowed),
        # title_text = "".join(title.split("|")[:-2])
    except Exception as e:
        print(e)

    # claps and responses
    claps = None
    responses = None
    reading_time = None

    # If I can get detailed div tags then try following:
    # https://hackernoon.com/how-to-scrape-a-medium-publication-a-python-tutorial-for-beginners-o8u3t69

    try:
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
    except Exception as e:
        print(e)

    data_model = {
        "author_page": author_page,
        "author": author,
        "article_title": title_text,
        "images": None,
        "date_published": published_time,
        "date_accessed": accessed_time,
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

    return data_model
    # print(data_model)


app = FastAPI()

@app.get("/medium/")
async def root(url):
    # example url: http://127.0.0.1:8000/medium/?url=https://medium.com/..."
    data_model = scrape(url)
    json_object = json.dumps(data_model)
    return json_object

if __name__ == '__main__':
    get_links()
    #scrape()
