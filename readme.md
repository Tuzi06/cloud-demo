# Introduction
This project is to scrape post contents on [小红书](https://www.xiaohongshu.com/explore) a chinese version of instagram. The entire process is devided to Scraping Server (with mutliple stages and parallel processing for each stage to maximize performance) and Database Server, for distributing the bots or workload to different machines and places( for example: different region on aws) to enhance the reliability and overall performance.

# Installation
```python
pip3 install -r requirements.txt
```
# Configuration
1. By default scraping post information processes(server.py) will running in the configuration of 5 userScrapers and 5 infoScrapers. If you want to change the setting, you can change at line 41 in master.py:
```python
if self.checkState() == 'cold':
    requests.get(f"{self.url}/start",json= {'url':self.url[:-5],'userScraper':5,'postScraper':5,'userlog':userlog},timeout=1000)
```
Notice: sum of userScraper and postScraper should smaller or equal to the number of webdrivers you initallized, i.e.  the value of "SE_NODE_MAX_SESSIONS" when you initallize the webdrivers at docker. For more information about webdriver running in docker, please forward to: **[Running at cloud](#running-service.py-at-cloud)**<br>

2. Copy and paste the external ip to
    ``` python
     url = 'http://35.208.236.78:8080'
    ```
    at line 83 in master.py. Or simply change to http://localhost:8080 if the server is running locally. Noticed server will be listen to port 8080 by default.
   
# Usage
As the crawler can goes into issues, such as when web page did not render properly (when we scroll down to the bottom of home page, it may not render the new posts, and stuck there), where they can crash the entire crawler process. Also running multi-parallel process locally can be a insufficent solution for the entire crawling job. The entire process is divided to local part and cloud part.
The home page of xhs contents a list of posts which have the user link of each post in the html file. The job of main.py is to get these links and pass to the service.py that running on the cloud.

## Running Service.py At Cloud
Initiallizing webdrivers if you prefer running docker image of webdriver such as chrome:

```docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=10 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_SESSION_TIMEOUT=86400 selenium/standalone-chrome```

More information for the command: [selenium/standalone](https://hub.docker.com/r/selenium/standalone-chrome).
Or choose whatever docker image you like.

Uncomment line 19 and 20 and comment line 16 and 17 if you want to run webdriver locally, be sure you have the latest webdriver store in the lowlevel folder.

Then running service.py by
```python3 service.py```
or Running docker image(currently do not have the ability to custom number of parallel processes for each scraper):
```
x86-84: docker run tuzi06/scraper-x86
arm:  docker run tuzi06/scraper-arm
```

### Running main.py
Run command at terminal
```python3 main.py```

# Feature Work
1. Current selenium and webdriver configuration takes quite a bit of computing power to run. Changing to python's native request library should free those part of performance at both cpu and internet loads (no need to require those pictures that ), and leads to add a couple more parallel proccesses into server side.

2. we currently store all the data for user info, posts, comments and replys at ram. Changing from store these data at ram to external database, such as mongodb, can leads to much better deal with crash of server side, and maybe store pictures of posts on the fly.
