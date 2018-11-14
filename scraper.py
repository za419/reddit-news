#!/usr/bin/env python3

import sys
from bs4 import BeautifulSoup
from readability.readability import Document
import urllib.request

def scrape(URL):
    """
    Return the text of the article found at URL
    Some whitespace changes will usually occur.
    """

    html = urllib.request.urlopen(URL).read()
    doc = Document(html)
    doc.parse(["summary", "short_title"])
    readable_article = doc.summary()
    soup = BeautifulSoup(readable_article, 'html.parser')
    text = soup.get_text()
    return text

if __name__ == "__main__":
    # Get target url
    if len(sys.argv)!=2:
        try:
            print("Usage: python {0} <url>".format(sys.argv[0]))
        except:
            print("Usage: python scraper.py <url>")
        print("  <url> should point to an article from which to scrape text.")
        sys.exit(1)

    # Under Python 3.7, use utf-8 output
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

    print(scrape(sys.argv[1]))
