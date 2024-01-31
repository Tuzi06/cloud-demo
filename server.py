from flask import Flask,request
from multiprocessing import Process,Manager
from bs4 import BeautifulSoup as bs
import time,requests,traceback,datetime

from lowlevel.scraper import getUser,grabing
class Scraper():
    def __init__(self,userScrapers,postScrapers):
        self.state = 'ready'
        self.userScraper = userScrapers
        self.postScraper = postScrapers
        self.headers = {
            'authority': 'www.xiaohongshu.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'cache-control': 'max-age=0',
            'cookie': 'abRequestId=17d4f392-daf3-504b-9705-ea26a4637bac; xsecappid=xhs-pc-web; a1=18d5cd4ab08x3trygpmg4i55k50ucknlg926zmnja40000152067; webId=0654c522ba49343049a7bf1834ce2ffe; gid=yYf2Sf4D48k2yYf2Sf40Dj6I8YCq9FvkU6k4JV0322T28K487STI1u888y2J8KW8fqj42y84; webBuild=4.1.6; websectiga=f3d8eaee8a8f63016320d94a1bd00562d516a5417bc43a032a80cbf70f07d5c0; sec_poison_id=4910a48c-54e0-486e-a460-768738daebd2; unread={%22ub%22:%22659e142b000000001e0062d2%22%2C%22ue%22:%2265a5fb0300000000110331b1%22%2C%22uc%22:26}; cache_feeds=[]',
            'referer': 'https://www.google.com/',
            'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }

    def antiDetect(self,response,url):
        if 'https://www.xiaohongshu.com/website-login/error?redirectPath=' in response.url:
            time.sleep(5)
            response = requests.get(url,headers = self.headers)
        return response
    
    def homePageScraper(self,userlinkPool):
        start = time.perf_counter()
        print(datetime.datetime.now(),'\n')
        requests.get('http://127.0.0.1:3001/start')    
        num = requests.get('http://127.0.0.1:3001/count').content.decode("utf-8")
        requestnum = 10000 - int(num) # the num of post we need 
        print(f"{requestnum} post need be scrapped")

        url = "https://www.xiaohongshu.com/explore"
        while True:
            if userlinkPool.qsize()>5:
                time.sleep(1)
                continue
            time.sleep(1)
            try:
                response = requests.get(url ,headers = self.headers)
                response = self.antiDetect(response,url)
                # self.headers = response.headers
                html = bs(response.content,'html.parser')
                # print(html.prettify())
                # open('a.html','w').write(html.prettify())
                # time.sleep(5)
                # return 
                userlinks = ['https://www.xiaohongshu.com'+title['href']for title in html.findAll('a',class_='author')]
                if len(userlinks) == 0:
                    url = "https://www.xiaohongshu.com/explore" if url != "https://www.xiaohongshu.com/explore" else 'https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend'
                    print(url)
                    continue
                for userlink in userlinks:
                    userlinkPool.put(userlink)
                    progress= int(requests.get('http://127.0.0.1:3001/count').content.decode("utf-8"))
                    percent = ("{0:." + str(2) + "f}").format(100 * (progress/ float(requestnum)))
                    print(f'\r progress: {percent}% Complete', end = '\r')
                if progress>= requestnum:
                    end = time.perf_counter()
                    print('\n Time is %4f hours'%((end - start)/3600)) 
                    break 
            except:
                continue

    def userPageScraper(self,userlinkPool,userInfoPipline,userLog): 
        while True:
            if userlinkPool.empty() or userInfoPipline.qsize()>10:
                time.sleep(1)
                continue
            userlink = userlinkPool.get()
            if userlink in userLog:
                continue
            userLog.append(userlink)
            try:
                response = requests.get(userlink,headers = self.headers)
                response = self.antiDetect(response,userlink)
                # self.headers = response.headers
                soup = bs(response.content,'html.parser')
                userInfo = getUser(soup)    
                if ('W' in userInfo['follow'] or 'K' in userInfo['follow']) and 'W' in userInfo['like']:
                    linklist =soup.findAll('a','title')
                    if len(linklist)>=10:
                        userInfo.pop('like')
                        userInfo.pop('follow')
                        # print(userInfo)
                        userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in linklist[:10]]})
                # return 
            except:
                # print(response.url)
                # traceback.print_exc()
                # return 
                # print('fail on users')
                continue
            
    def postPageScrapers(self,userInfoPipline):
        while True:
            if userInfoPipline.empty():
                time.sleep(1)
                continue
            userInfo,links = userInfoPipline.get().values()
            idx = 0
            userInfo['posts'] = []
            for link in links:
                try:
                    url = 'https://www.xiaohongshu.com'+link
                    response = requests.get(url,headers = self.headers)
                    response = self.antiDetect(response,url)

                    soup = bs(response.content.decode('utf-8'),'html.parser')
                    idx,post= grabing(soup,self.headers,userInfo,idx)
                except:
                    # traceback.print_exc()
                    # return
                    # print('fail on post')
                    continue
                post['url'] = url
                id = requests.post(f"http://127.0.0.1:3001/insert",json = {'id':'posts','data':post}).content.decode("utf-8")
                userInfo['posts'].append(id)
            requests.post(f"http://127.0.0.1:3001/insert",json = {'id':'users','data':userInfo})
            

app = Flask(__name__)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/start')
def start():
    global userInfoPipline,userlinkPool,posts,userLog,scraper,processes
    userInfoPipline =Manager().Queue()
    userlinkPool =Manager().Queue()
    print(userInfoPipline.qsize(),userlinkPool.qsize())
    posts = Manager().list()
    userScrapers,postScrapers,userlog = request.get_json().values()
    userLog = Manager().list(userlog)
    scraper = Scraper(userScrapers,postScrapers)
    processes = []
    processes.append(Process(target = scraper.homePageScraper,args=[userlinkPool]))
    for _ in range(scraper.userScraper):
        processes.append(Process(target=scraper.userPageScraper,args=[userlinkPool,userInfoPipline,userLog]))
    for _ in range (scraper.postScraper):
         processes.append(Process(target=scraper.postPageScrapers,args=[userInfoPipline]))
    for process in processes:
        process.start()
    return 'finish starting'

@app.route('/state')
def fetchState():
    try:
        if userlinkPool.qsize()>15:
            return 'full'
        else:
            return 'ready'
    except:
        return 'cold'

@app.route('/download')
def download():
    return list(posts)

@app.route('/progress')
def checkProgress():
    return str(len(posts))

@app.route('/poolState')
def poolState():
    return str(f"userInfoQueue:{userlinkPool.qsize()}, postQueue:{userInfoPipline.qsize()}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000)

    # docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=40 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_SESSION_TIMEOUT=86400 selenium/standalone-chrome
    # docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=40 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_SESSION_TIMEOUT=864000 seleniarm/standalone-chromium

    # docker kill $(docker ps -q)
    # docker buildx build --platform linux/amd64 -t tuzi06/scraper-x86:latest --push .
    # docker buildx build  -t tuzi06/scraper-arm:latest --push .
    # docker rm $(docker ps --filter status=exited -q) 