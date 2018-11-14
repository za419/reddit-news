#!/usr/bin/env python3

import praw
import os
import sys
import traceback
import scraper
from configparser import ConfigParser

# On Python 3.7, output utf-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

# Helper functions
def exc_message():
    """
    Returns a string containing tracebackless exception data.
    Must only be called within an exception handler.
    """

    ex_type, ex_value, ex_traceback = sys.exc_info()

    trace=traceback.extract_tb(ex_traceback)[0]

    return "{0}: {1}. From line {2} ({3})".format(ex_type.__name__, ex_value, trace[1], trace[3])

# Get client info from secrets file
secrets = ConfigParser(interpolation=None)
secrets.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.ini'))
secrets=secrets['SECRETS']

def submission(target):
    """
    Returns the Reddit submission object corresponding tothe given target.
    """

    reddit=praw.Reddit(user_agent="Comment Fetcher", client_id=secrets['client_id'],
                       client_secret=secrets['client_secret'])

    # Get a submission object
    submission=None
    # The submission is a URL if it includes 'reddit.com', else an ID
    if "reddit.com" in target:
        submission=reddit.submission(url=target)
    else:
        submission=reddit.submission(id=target)

    return submission

def comments(target):
    """
    Returns a collection of string tuples, where each tuple consists of a comment ID, comment URL, and the contents of the comment.
    Accepts either a URL or a submission ID.
    """

    sub=submission(target)

    # Now, iterate over all comments, and print them all out
    # Remove 'more comments' and the like
    sub.comments.replace_more(limit=None)
    all=sub.comments.list()

    return ((comment.id, comment.permalink, comment.body) for comment in all)

def scrape(target):
    """
    Returns the scraped article text for the article linked in the given Reddit submission.
    """

    sub=submission(target)

    return scraper.scrape(sub.url)

# Get target url
if len(sys.argv)!=2:
    try:
        print("Usage: python {0} <target>".format(sys.argv[0]))
    except:
        print("Usage: python client.py <target>")
    print("  <target> can either be a link to a Reddit thread, or just a submission ID.")
    sys.exit(1)

for comment in comments(sys.argv[1]):
    print("Comment {0} from {1}:\n{2}\n\n".format(comment[0], comment[1], comment[2]))

print() # Extra newline for legibility
input("Press Enter to view scraped article text. ")
print("Article text (with whitespace alterations):")
print() # Extra newline for legibility

print(scrape(sys.argv[1]))
