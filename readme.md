# The Scraper 2.0  (Not finish yet, information below may not fit how code is working)
This project is to scrape post contents on [小红书](https://www.xiaohongshu.com/explore) a chinese version of instagram. The entire process is devided to Scraping Server (with mutliple stages and parallel processing for each stage to maximize performance) and Database Server, for distributing the bots or workload to different machines and places( for example: different region on aws) to enhance the reliability and overall performance.
## Installation
```python
pip3 install -r requirements.txt
```
## Settings
If you would like custom and connect to your own database (which you should), your db file needs to have routes:
* start (for starting in the database middleware to contect with your external database (here I use mongodb to store all the data set)
* state (return value should either be "started" or "cold" to define whether the server is started)
* count (return the numbers of posts that have been stored)
* log (return the numbers of users that have been stored)
* insert (insert data into correspond table (collection if you use mongodb),needs has two tables:user and posts). You may have something like 
    ```python
     _id = db[data['id']].insert_one(data['data'])
        return str(_id.inserted_id)
    ```
  for your insert query and if possible return the id of that document or row(unique identifier for post).

If you would like change the filter of users, you can change the if statement at the bottom of userPageScraper in server.py which is: 
```python
if ('W' in userInfo['follow'] or 'K' in userInfo['follow']) and 'W' in userInfo['like']:
```
  
## Data Structure in Database
### User Example:
```
{'_id': 'cmsh2024',
 'name': '莓Something🔴',
 'info': '水到渠成💦\n@CMSH 草莓生活 \n👆',
 'sex': '', # 'female','male' or '' if user did not select the sex
 'tag': [], # user tags
 'posts': ['65d3e3d7b4663623338e5f75',
  '65d3e3dab4663623338e5f82',
  '65d3e3dcb4663623338e5f99',
  '65d3e3dfb4663623338e5fb6',
  '65d3e3e1b4663623338e5fd3',
  '65d3e3e3b4663623338e5fed',
  '65d3e3e5b4663623338e600c',
  '65d3e3e8b4663623338e6028',
  '65d3e3eab4663623338e6043',
  '65d3e3edb4663623338e6063'] # an array of post ids
}
```
### Post Example:
```
{'_id': ObjectId('65d3e3d7b4663623338e5f75'),
 'user-id': 'cmsh2024',
 'post': {'title': '问保温杯👀过来',
  'text': '素材来自@CMSH 草莓生活🛒👆-',
  'tag': [],
  'comments': [{'朴心': '可你这个吸管和视频里的不一样',
    'replys': {'莓Something🔴': '一样的哦 这里只是漏出了吸管嘴'}},
   {'冰冰': '这个杯子哪里买'}]},
 'pictures': {'cmsh2024-0': 'http://sns-webpic-qc.xhscdn.com/202402200727/3d938d84d024d112cf1ff95befa5339a/1040g2sg30v6rcm8sle005obtdv90k4g6l1m6380!nd_dft_wlteh_webp_3'},
 'url': 'https://www.xiaohongshu.com/user/profile/617d6fd20000000002021206/65cdfd270000000007004282'}
```

## How to Use
To start scraping processes, a request with json:
```
{
    "userScrapers":20,
    "postScrapers":60,
    "dburl":"http://127.0.0.1" # your database middleware server that can be run indepedently
}
```
needs to sent to "/start" route. 

###Notice: 

The ratio between number of userScrapers and postScrapers should be at least 1:3, and are recommand in 1:2 for a consistent run. As each post may take about 2 to 2.5 seconds to scrape, the overall scraping speed for script can be defined as 1/2 of postScrapers, and peak perfromance will be the internet bendwidth (the difference between 60 postScrapers and 100 postScrapers are minimal, at least this is the result when I tested).Also, a vpn or some proxy service are recommand.

As this script can be seen as a DDOS attack, we kind of spam the server with get requests, a high number of scrapers setting can leads to an ip tempoary block by server or so. For reference the setting in the example above has the performance of a 100k posts scraping job can be done in 3 hours with lightly cpu usage.

We can test the availability of cookies in cookies.json as follows:
``` python
import requests,json
from bs4 import BeautifulSoup as bs
header= json.load(open('headers.json','r'))['htmlHeaders']
cookies = json.load(open('cookies.json','r'))
url = 'https://www.xiaohongshu.com/explore'
requests.get(url,headers=header)
for cookie in cookies:
    header['cookie'] = cookie
    html = bs(requests.get(url,headers=header).content,'html.parser')
    print(len(html.findAll('a',class_='author')))
```
if all the results are 0 (cookies may expires), we re-scrape the 20 new cookies using selenium as follows:
```python
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
import time,json,sys
if sys.platform == 'linux':
    service = Service(executable_path= 'drivers/chromedriver-linux64/chromedriver')
elif sys.platform == 'darwin':
    service = Service(executable_path='drivers/chromedriver-mac-arm64/chromedriver')
options =ChromeOptions()
options.add_argument('disable-blink-features=AutomationControlled')
# options.add_argument('headless')
cookies = []
for h in hs[1:-1]:
    ls.append(h.split('; ')[1])
for _ in range(20):
    driver = Chrome(options = options,service=service)
    driver.get('https://www.xiaohongshu.com/explore')
    time.sleep(5)
    cs = driver.get_cookies()
    t = dict()
    s = ''
    ls = ['abRequestId','webBuild','xsecappid','a1','webId','websectiga','sec_poison_id','gid','web_session']
    for c in cs:
       t[c['name']] = c['value']
    for l in ls:
        s+= l+'='+t[l]+'; '
    print(s)
    cookies.append(s)
    driver.quit()
open('cookies.json','w').write(json.dumps(cookies,indent=4))
```
Notice: make sure you have the latest version of webdriver that correspond your operating system.

## Todos
* Find a way to get the around the recapatcha things and ip block if setting are high enough.
* Scrape more replys, something like reply of reply of reply?
* Experience and test the realtionship between performance and better hardwares( a higher bendwidth and a higher tier mongodb servvice)
