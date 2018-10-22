#!/usr/bin/env python3

import praw
import os
from configparser import ConfigParser

# Get client info from secrets file
secrets = ConfigParser(interpolation=None)
secrets.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'secrets.ini'))
secrets=secrets['SECRETS']

reddit=praw.Reddit(user_agent="Comment Fetcher", client_id=secrets['client_id'],
                   client_secret=secrets['client_secret'])
