#!/usr/bin/env python3

import praw
import os
import sys
import traceback
from configparser import ConfigParser

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

# Get target url
if len(sys.argv)!=2:
    try:
        print("Usage: {0} <target>".format(argv[0]))
    except:
        print("Usage: python client.py <target>")
    print("  <target> can either be a link to a Reddit thread, or just a submission ID.")
    sys.exit(1)

reddit=praw.Reddit(user_agent="Comment Fetcher", client_id=secrets['client_id'],
                   client_secret=secrets['client_secret'])

# Get a submission object
submission=None
# The submission is a URL if it includes 'reddit.com', else an ID
try:
    if "reddit.com" in sys.argv[1]:
        submission=reddit.submission(url=sys.argv[1])
    else:
        submission=reddit.submission(id=sys.argv[1])
except:
    print("Unable to find reddit submission.\n{0}".format(exc_message()))
    sys.exit(1)


# Now, iterate over all comments, and print them all out
try:
    # Remove 'more comments' and the like
    submission.comments.replace_more(limit=None)
    all=submission.comments.list()
except:
    print("Unable to get comments from submission.\n{0}".format(exc_message()))
    sys.exit(1)

print() # Extra newline for legibility

for comment in submission.comments.list():
    try:
        # Skip printing deleted comments
        if not comment.body:
            continue

        print("Comment {0} at {1}:".format(comment.id, comment.permalink))
        print() # Extra newline for legibility
        print(comment.body)
        print() # Extra newline for legibility
        print() # Extra newline for legibility
    except:
        pass # Silently skip comments we can't print for some reason
