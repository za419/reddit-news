#!/usr/bin/env python3

import praw
import os
import sys
from configparser import ConfigParser

# Get client info from secrets file
secrets = ConfigParser(interpolation=None)
secrets.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.ini'))
secrets=secrets['SECRETS']

# Get target url
if len(sys.argv)!=2:
    print("Usage: {0} <target>".format(argv[0]))
    print("  <target> can either be a link to a Reddit thread, or just a submission ID.")

reddit=praw.Reddit(user_agent="Comment Fetcher", client_id=secrets['client_id'],
                   client_secret=secrets['client_secret'])

# Get a submission object
submission=None
# The submission is a URL if it includes 'reddit.com', else an ID
if "reddit.com" in sys.argv[1]:
    submission=reddit.submission(url=sys.argv[1])
else:
    submission=reddit.submission(id=sys.argv[1])
