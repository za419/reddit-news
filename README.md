# Reddit News
EECS 338 project

## Requirements
### pip
To host Reddit News, you need to use `pip` to install the following packages:  
- `bs4`
- `praw`
- `git+https://github.com/stalkerg/python-readability`

### secrets.ini
To host Reddit News, you also need to have Reddit authentication set up, and provide this information in a file named `secrets.ini`, placed in the root directory of the repository (next to this README file).

#### Reddit authentication
First, sign into your reddit account.  
Then, go to your Application Preferences page ([found here](https://www.reddit.com/prefs/apps)), and at the bottom, create a new application.  
Fill in the requested data, and you will be presented with information about your application. As of the time of writing, an example looks like this:

![Example application info](https://github.com/za419/reddit-news/raw/assets/appinfo.png)

Create your `secrets.ini` file, and then fill it in with the information found where `client_id` and `client_secret` appear in the example. When done, your file should follow this format:

    [SECRETS]
    
    client_id=<client_id>
    client_secret=<client_secret>

Following the information found from Reddit.

If done correctly, you should be able to perform comment fetches.

## Usage
### Comment fetching
Run `python client.py <token>`

Where `<token>` is either a URL to a Reddit thread, or the ID of one. Valid examples of either:

- `https://www.reddit.com/r/funny/comments/5gn8ru/guardians_of_the_front_page/`
- `5gn8ru`

The output on large threads is very large, as it consists of every comment on the thread. Consider piping the output to your favorite pager:

`python client.py 5gn8ru | less`

This will take a few seconds to complete, due to API limitations.

### Article scraper
At the moment, the article scraper does not support alternative articles to the hardcoded default (see #2).

Therefore, just run `python scraper.py`.

## Related artwork

![image](https://imgs.xkcd.com/comics/python.png)

![image](https://external-preview.redd.it/CjZOp8TpXqT5nmKPemBC_Ad0GedT6UMVyOXAd549cH4.jpg?width=298&s=09cacf3749968b66b55a20eb6396c7480b373bef)

![image](https://imgs.xkcd.com/comics/not_enough_work.png)
