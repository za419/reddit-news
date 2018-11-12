import sys
from bs4 import BeautifulSoup
from readability.readability import Document
import urllib.request

def scrape(URL):
    html = urllib.request.urlopen(URL).read()
    doc = Document(html)
    doc.parse(["summary", "short_title"])
    readable_article = doc.summary()
    soup = BeautifulSoup(readable_article, 'html.parser')
    text = soup.get_text()
    return text
