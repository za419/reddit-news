# Reddit News
EECS 338 project  
[View live](http://ec2-18-224-65-64.us-east-2.compute.amazonaws.com/)

## Requirements
### pip
To host Reddit News, you need to use `pip` to install the following packages:  
- `bs4`
- `praw`
- `spacy`
- `git+https://github.com/stalkerg/python-readability`

Additionally, you need to run the command:  
`python -m spacy download en`

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
Run `python scraper.py <url>`

Where `<url>` is a URL to an article to scrape.

The output may not preserve whitespace.

### Webserver
Run `python server.py <port> <path to directory> [-c [seconds]]`.

`<port>` is which port to serve the site on. If it's privileged (like 80), the server may require root access.

The `<path to directory>` is the path to the root of the site (ie, the front-end folder). You probably want "public" if you're running it from this directory.

If you provide `-c` (recommended), the server will instruct browsers they are permitted to cache resources. If you provide an integer after that flag, it will set the number of seconds advertised for caching, otherwise it will default to 3600 (one hour).

Server logs are stored next to the server itself, in a folder called "logs".

I also advise that you look over `default-config.ini` to see what parameters can be configured for the server. If you wish to override any, do not modify that file, but instead place them in a new file named `config.ini` following the same format. Any parameters in the latter file will be used preferentially.

## Related artwork

![image](https://imgs.xkcd.com/comics/python.png)

![image](https://external-preview.redd.it/CjZOp8TpXqT5nmKPemBC_Ad0GedT6UMVyOXAd549cH4.jpg?width=298&s=09cacf3749968b66b55a20eb6396c7480b373bef)

![image](https://imgs.xkcd.com/comics/not_enough_work.png)
