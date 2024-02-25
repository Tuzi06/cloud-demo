from copy import deepcopy
from flask import Flask,request
from multiprocessing import Process,Manager
from bs4 import BeautifulSoup as bs
import time,requests,traceback,datetime,json,random

from scraper import getUser,grabing
class Scraper():
    def __init__(self,userScrapers,postScrapers,dburl,goal):
        self.state = 'ready'
        self.userScraper = userScrapers
        self.postScraper = postScrapers
        self.dburl = dburl
        self.headers = json.load(open('headers.json','r'))
        self.cookies = json.load(open('cookies.json','r'))
        self.goal = goal
        # requests.get('https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend',headers = self.headers['htmlHeaders'])

    def antiDetect(self,response,url):
        if 'https://www.xiaohongshu.com/website-login/error?redirectPath=' in response.url or response.status_code != 200:
            # time.sleep(2)
            if response.status_code != 200:
                print(response.status_code)
            # else:
            #     print(response.url)
            headers=deepcopy(self.headers['htmlHeaders'])
            # headers['cookie'] = self.updateCookie(url)
            headers['cookie'] = random.choice(self.cookies)
            response = requests.get(url,headers = headers)
            # print(response.url)
            # time.sleep(100)
        return response
    
    def updateCookie(self,url):
        response= requests.get(url,headers = self.headers['htmlHeaders'])
        newAd = response.headers['Set-Cookie'].split('; ')[0]
        newCookie = [newAd] + self.headers['cookie'].split('; ')[1:]
        newCookie = '; '.join(newCookie)

        # print(newCookie)
        return newCookie
    
    def homePageScraper(self,userlinkPool):
        start = time.perf_counter()
        print(datetime.datetime.now(),'\n')
        if requests.get(f'{self.dburl}/state').content.decode("utf-8") == 'cold':
            requests.get(f'{self.dburl}/start')    
        num = requests.get(f'{self.dburl}/count').content.decode("utf-8")
        # print(num)
        requestnum = self.goal- int(num) # the num of post we need 
        print(f"{requestnum} post need be scrapped")
        # return 
        url = "https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend"
        headers = deepcopy(self.headers['htmlHeaders'])
        cookie = deepcopy(self.cookies[0])
        update = 0 
        suceed = 0
        crash = 0

        lasttime = start
        lastprogress = 0
        userlinks = []
        while True:
            progress= int(requests.get(f'{self.dburl}/count').content.decode("utf-8"))
            current = time.perf_counter()

            percent = ("{0:." + str(2) + "f}").format(100 * (progress/ float(int(num)+requestnum)))
            speed =  ("{0:." + str(2) + "f}").format((progress-lastprogress)/(current-lasttime))
            print(f'\r progress: {percent}% Completed, speed: {speed} posts per second, last batch size:{len(userlinks)}    ', end = '\r')
            lasttime = current
            lastprogress = progress
            if userlinkPool.qsize()>self.userScraper * 2:
                time.sleep(1)
                continue
            try:
                headers['cookie'] = cookie
                # headers['cookie'] = random.choice(self.cookies)
                response = requests.get(url ,headers = headers)
                response = self.antiDetect(response,url)

                html = bs(response.content,'html.parser')
                # print(html.prettify())
                # open('a.html','w').write(html.prettify())
                # time.sleep(5)
                # return 
                userlinks =[title['href']for title in html.findAll('a',class_='author')]
                
                # print('success:',suceed,' url update:',update, ' crash:',crash,' num of userlinks:',len(userlinks),end='\r')
                
                # if len(userlinks) != 0 and len(userlinks)<20:
                #     # open('a.html','w').write(html.prettify())
                #     print('response has errors')
                #     return 
                filtered = requests.get(f'{self.dburl}/checkExist',json = {'data':userlinks}).json()
                # print(filtered)
                for userlink in filtered:
                    userlinkPool.put('https://www.xiaohongshu.com'+userlink)
                if len(filtered)!=0:
                    requests.post(f'{self.dburl}/addlog',json ={'id':'users','data':[userlink.split('/')[-1] for userlink in filtered]})

                if progress>=int(num)+requestnum:
                    end = time.perf_counter()
                    print('\n Time is %4f hours'%((end - start)/3600)) 
                    break 

                if len(userlinks) == 0:
                    if int(progress)%2!=0:
                        cookie = self.updateCookie(url)
                    else:
                        cookie = random.choice(self.cookies)
                    # print(cookie)
                    update += 1  
                    continue 
                suceed +=1 
            except:
                traceback.print_exc()
                crash+=1
                return
                continue

    def userPageScraper(self,userlinkPool,userInfoPipline): 
        headers = deepcopy(self.headers['htmlHeaders'])
        cookie = deepcopy(self.headers['cookie'])
        while True:
            # headers['cookie'] = cookie
            if userlinkPool.empty() or userInfoPipline.qsize()>self.postScraper:
                time.sleep(1)
                continue
            userlink = userlinkPool.get()
            try:
                response = requests.get(userlink,headers = headers)
                response = self.antiDetect(response,userlink)
                # self.headers = response.headers
                soup = bs(response.content,'html.parser')
                # open('a.html','w').write(soup.prettify())
                userInfo = getUser(soup)   
                linklist =soup.findAll('a','title')
                if ('W' in userInfo['follow'] or 'K' in userInfo['follow']) and 'W' in userInfo['like'] and len(linklist)>=10:
                    userInfo['longID'] = userlink.split('/')[-1]
                    # userInfo.pop('like')
                    # userInfo.pop('follow')
                    # print(userInfo)
                    userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in linklist[:10]]})
                # return 
            except:
                try:
                    cookie = self.updateCookie(userlink)
                except:
                    continue
                # print(response.headers)
                # traceback.print_exc()
                # return 
                # print('fail on users')            
            
    def postPageScrapers(self,userInfoPipline):
        headers = deepcopy(self.headers['htmlHeaders'])
        # cookie = deepcopy(self.headers['cookie'])
        while True:
            if userInfoPipline.empty():
                time.sleep(1)
                continue
            # headers['cookie'] = cookie
            userInfo,links = userInfoPipline.get().values()
            idx = 0
            userInfo['posts'] = []
            # cookie = random.choice(self.cookies)
            cookie = self.cookies[0]
            posts=[]
            for link in links:
                try:
                    url = 'https://www.xiaohongshu.com'+link
                    response = requests.get(url,headers = headers)
                    response = self.antiDetect(response,url)

                    soup = bs(response.content.decode('utf-8'),'html.parser')
                    idx,post= grabing(soup,self.headers,cookie,userInfo,idx)
                    # return 
                except:
                    # traceback.print_exc()
                    # return
                    # print('fail on post')
                    try:
                        cookie = self.updateCookie(url)
                        continue
                    except:
                        continue
                post['url'] = url
                posts.append(post)
                # id = requests.post(f"{self.dburl}/insert",json = {'id':'posts','data':post}).content.decode("utf-8")
                # userInfo['posts'].append(id)
            if len(posts)!=0:
                userInfo['posts'] = requests.post(f"{self.dburl}/insert",json = {'id':'posts','data':posts}).json()
            requests.post(f"{self.dburl}/insert",json = {'id':'users','data':userInfo})   
            # break      

app = Flask(__name__)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/start')
def start():
    global userInfoPipline,userlinkPool,posts,scraper,processes
    userInfoPipline =Manager().Queue()
    userlinkPool =Manager().Queue()
    # print(userInfoPipline.qsize(),userlinkPool.qsize())
    posts = Manager().list()
    userScrapers,postScrapers,dburl,goal = request.get_json().values()
    scraper = Scraper(userScrapers,postScrapers,dburl,goal)
    processes = []
    for _ in range(1):
        processes.append(Process(target = scraper.homePageScraper,args=[userlinkPool]))
    for _ in range(scraper.userScraper):
        processes.append(Process(target=scraper.userPageScraper,args=[userlinkPool,userInfoPipline]))
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