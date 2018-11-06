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

## Related artwork

![image](https://imgs.xkcd.com/comics/python.png)

![image](https://external-preview.redd.it/CjZOp8TpXqT5nmKPemBC_Ad0GedT6UMVyOXAd549cH4.jpg?width=298&s=09cacf3749968b66b55a20eb6396c7480b373bef)

![image](https://imgs.xkcd.com/comics/not_enough_work.png)
