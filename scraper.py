from bs4 import BeautifulSoup
import requests

html = requests.get('https://www.theguardian.com/us-news/2018/nov/04/pittsburgh-shooting-robert-bowers-jewish-nurse').content

soup = BeautifulSoup(html, 'html.parser')
text = soup.get_text()
print(text)