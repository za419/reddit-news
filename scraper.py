import sys
from bs4 import BeautifulSoup
from readability.readability import Document
import urllib.request

sys.stdout.reconfigure(encoding='utf-8')
html = urllib.request.urlopen('https://www.theguardian.com/us-news/2018/nov/04/pittsburgh-shooting-robert-bowers-jewish-nurse').read()
doc = Document(html)
doc.parse(["summary", "short_title"])
readable_article = doc.summary()
readable_title = doc.short_title()
soup = BeautifulSoup(readable_article, 'html.parser')
text = soup.get_text()
print(text)