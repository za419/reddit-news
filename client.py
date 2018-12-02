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
    Returns the Reddit submission object corresponding to the given target.
    The target can either be a thread URL or a thread ID.
    """

    reddit=praw.Reddit(user_agent="Comment Fetcher", client_id=secrets['client_id'],
                       client_secret=secrets['client_secret'])

    # Get a submission object
    out=None
    # The submission is a URL if it includes 'reddit.com', else an ID
    if "reddit.com" in target:
        out=reddit.submission(url=target)
    else:
        out=reddit.submission(id=target)

    return out

def connected_comments(sub):
    """
    Returns a collection of string tuples, where each tuple consists of a comment ID, comment URL, and the contents of the comment.
    Accepts a Reddit submission object.
    (see the comments() variant if you have a Reddit target, as accepted by submission() )
    """

    return connected_comments2(sub, None)

def comments(target):
    """
    Returns a collection of string tuples, where each tuple consists of a comment ID, comment URL, and the contents of the comment.
    Accepts either a Reddit thread url or a Reddit thread ID.
    This is an alias for calling both submission() and connected_comments().
    If you also need to do scraping on the same target, it would be more efficient to store the submission object.
    """

    return connected_comments(submission(target))

def connected_comments2(sub, limit=32):
    """
    Returns a collection of string tuples, where each tuple consists of a comment ID, comment URL, and the contents of the comment.
    Accepts a Reddit submission object.
    (see the comments2() variant if you have a Reddit target, as accepted by submission() )
    This version allows a limit on the number of MoreComments objects to be replaced.
    Since the duration taken by the function is proportional to the number of replaced objects, this is an approximate performance control.
    """

    # Iterate over all comments, and print them all out
    # Remove 'more comments' and the like
    sub.comments.replace_more(limit=limit)
    all=sub.comments.list()

    return ((comment.id, comment.permalink, comment.body) for comment in all)

def comments2(target, limit=32):
    """
    Returns a collection of string tuples, where each tuple consists of a comment ID, comment URL, and the contents of the comment.
    Accepts either a Reddit thread url or a Reddit thread ID.
    This is an alias for calling both submission() and connected_comments2().
    If you also need to do scraping on the same target, it would be more efficient to store the submission object.
    This version allows a limit on the number of MoreComments objects to be replaced.
    Since the duration taken by the function is proportional to the number of replaced objects, this is an approximate performance control.
    """

    return connected_comments2(submission(target), limit)

def connected_scrape(sub):
    """
    Returns the scraped article text for the article linked in the given Reddit submission.
    Accepts a Reddit submission object.
    (see the scrape() variant if you have a Reddit target, as accepted by submission() )
    """

    return scraper.scrape(sub.url)

def scrape(target):
    """
    Returns the scraped article text for the article linked in the given Reddit submission.
    Accepts either a Reddit thread URL or a Reddit thread ID.
    This is an alias for calling both submission() and connected_scrape().
    If you also need to do comment fetching on the same target, it would be more efficient to store the submission object.
    """

    return connected_scrape(submission(target))

def connected_fetchall(sub):
    """
    Returns a tuple, consisting of the scraped article text and the fetched comments for the given Reddit submission.
    Accepts a Reddit submission object.
    (see the fetchall() variant if you have a Reddit target, as accepted by submission() )
    """

    return (connected_scrape(sub), connected_comments(sub))

def fetchall(target):
    """
    Returns a tuple, consisting of the scraped article text and the fetched comments for the given Reddit submission.
    Accepts either a Reddit thread URL or a Reddit thread ID.
    """

    return connected_fetchall(submission(target))

def connected_fetchall2(sub, limit=32):
    """
    Returns a tuple, consisting of the scraped article text and the fetched comments for the given Reddit submission.
    Accepts a Reddit submission object.
    (see the fetchall() variant if you have a Reddit target, as accepted by submission() )
    This version allows a limit on the number of MoreComments objects to be replaced.
    Since the duration taken by the function is proportional to the number of replaced objects, this is an approximate performance control.
    """

    return (connected_scrape(sub), connected_comments(sub, limit))

def fetchall2(target, limit=32):
    """
    Returns a tuple, consisting of the scraped article text and the fetched comments for the given Reddit submission.
    Accepts either a Reddit thread URL or a Reddit thread ID.
    """

    return connected_fetchall2(submission(target), limit)

if __name__=="__main__":
    # Get target url
    if len(sys.argv)!=2:
        try:
            print("Usage: python {0} <target>".format(sys.argv[0]))
        except:
            print("Usage: python client.py <target>")
        print("  <target> can either be a link to a Reddit thread, or just a submission ID.")
        sys.exit(1)

    # Get the submission object for our target
    sub=submission(sys.argv[1])

    for comment in connected_comments(sub):
        print("Comment {0} from {1}:\n{2}\n\n".format(comment[0], comment[1], comment[2]))

    print() # Extra newline for legibility
    input("Press Enter to view scraped article text. ")
    print("Article text (with whitespace alterations):")
    print() # Extra newline for legibility

    print(connected_scrape(sub))
