# Introduction


## Installation
```python
pip3 install -r requirements.txt
```
## Configuration
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

## Usage
To start scraping processes, a request with json:
```
{"userScrapers":20,
"postScrapers":60}
```
needs to sent to "/start" route. Notice: the ratio between number of userScrapers and postScrapers should be at least 1:3, and are recommand in 1:2 for a consistent run.

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

