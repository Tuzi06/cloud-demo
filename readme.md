# Introduction


# Installation

```python
pip3 install -r requirements.txt
```

# Usage
As the crawler can goes into issues, such as when web page did not render properly (when we scroll down to the bottom of home page, it may not render the new posts, and stuck there), where they can crash the entire crawler process. Also running multi-parallel process locally can be a insufficent solution for the entire crawling job. The entire process is divided to local part and cloud part.
The home page of xhs contents a list of posts which have the user link of each post in the html file. The job of main.py is to get these links and pass to the service.py that running on the cloud.

### Running service.py at cloud
Initiallizing webdrivers if you prefer running docker image of webdriver such as chrome:

```docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=40 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_SESSION_TIMEOUT=86400 selenium/standalone-chrome```
More information for the command: [selenium/standalone](https://hub.docker.com/r/selenium/standalone-chrome)

or choose whatever docker image you like.

If you

Then running service.py by
```python3 service.py```
or Running docker image:
```
x86-84:
arm: 
```

### Running main.py
Run command at terminal
```python3 main.py```

# Feature Work
1. Current selenium and webdriver configuration takes quite a bit of computing power to run. Changing to python's native request library should free those part of performance at both cpu and internet loads (no need to require those pictures that ), and leads to add a couple more parallel proccesses into server side.

2. we currently store all the data for user info, posts, comments and replys at ram. Changing from store these data at ram to external database, such as mongodb, can leads to much better deal with crash of server side, and maybe store pictures of posts on the fly.
