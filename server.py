from copy import deepcopy
from http.cookiejar import Cookie
from flask import Flask,request
from multiprocessing import Process,Manager
from bs4 import BeautifulSoup as bs
import time,requests,traceback,datetime,json

from lowlevel.scraper import getUser,grabing
class Scraper():
    def __init__(self,userScrapers,postScrapers):
        self.state = 'ready'
        self.userScraper = userScrapers
        self.postScraper = postScrapers
        self.headers = json.load(open('headers.json','r'))
    def antiDetect(self,response,url,headers):
        if 'https://www.xiaohongshu.com/website-login/error?redirectPath=' in response.url:
            time.sleep(5)
            response = requests.get(url,headers = headers)
        return response
    
    def updateCookie(self,url):
        response= requests.get(url,headers = self.headers['htmlHeaders'])
        newAd = response.headers['Set-Cookie'].split('; ')[0]
        newCookie = [newAd] + self.headers['cookie'].split('; ')[1:]
        newCookie = '; '.join(newCookie)
        # print(newCookie)
        self.headers['cookie'] = newCookie
    
    def homePageScraper(self,userlinkPool):
        start = time.perf_counter()
        print(datetime.datetime.now(),'\n')
        if requests.get('http://127.0.0.1:3001/state').content.decode("utf-8") == 'cold':
            requests.get('http://127.0.0.1:3001/start')    
        num = requests.get('http://127.0.0.1:3001/count').content.decode("utf-8")
        print(num)
        requestnum = 100000 - int(num) # the num of post we need 
        print(f"{requestnum} post need be scrapped")

        url =  "https://www.xiaohongshu.com/explore"
        headers = deepcopy(self.headers['htmlHeaders'])
        update = 0 
        suceed = 0
        crash = 0
        while True:
            # print('success:',suceed,' url update:',update, ' crash: ',crash,end='\r')
            if userlinkPool.qsize()>20:
                time.sleep(1)
                continue
            try:
                headers['cookie'] = self.headers['cookie']
                response = requests.get(url ,headers = headers)
                # response = self.antiDetect(response,url,headers)

                html = bs(response.content,'html.parser')
                # print(html.prettify())
                # open('a.html','w').write(html.prettify())
                # time.sleep(5)
                # return 
                userlinks = ['https://www.xiaohongshu.com'+title['href']for title in html.findAll('a',class_='author')]
                for userlink in userlinks:
                    userlinkPool.put(userlink)
                progress= int(requests.get('http://127.0.0.1:3001/count').content.decode("utf-8"))
                percent = ("{0:." + str(2) + "f}").format(100 * (progress/ float(progress+requestnum)))
                print(f'\r progress: {percent}% Complete', end = '\r')

                if progress>= progress+requestnum:
                    end = time.perf_counter()
                    print('\n Time is %4f hours'%((end - start)/3600)) 
                    break 

                if len(userlinks) == 0:
                    self.updateCookie(url)
                    update += 1   
                    continue
                suceed +=1 
            except:
                # traceback.print_exc()
                crash+=1
                # return
                continue

    def userPageScraper(self,userlinkPool,userInfoPipline,userLog): 
        headers = deepcopy(self.headers['htmlHeaders'])
        headers['cookie'] = self.headers['cookie']
        while True:
            if userlinkPool.empty() or userInfoPipline.qsize()>10:
                time.sleep(1)
                continue
            userlink = userlinkPool.get()
            if userlink in userLog:
                continue
            userLog.append(userlink)
            try:
                response = requests.get(userlink,headers = headers)
                response = self.antiDetect(response,userlink,headers)
                # self.headers = response.headers
                soup = bs(response.content,'html.parser')
                # open('a.html','w').write(soup.prettify())
                userInfo = getUser(soup)    
                if ('W' in userInfo['follow'] or 'K' in userInfo['follow']) and 'W' in userInfo['like']:
                    linklist =soup.findAll('a','title')
                    if len(linklist)>=10:
                        userInfo.pop('like')
                        userInfo.pop('follow')
                        # print(userInfo)
                        userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in linklist[:10]]})
                return 
            except:
                self.updateCookie(userlink)
                # print(response.headers)
                # traceback.print_exc()
                # return 
                # print('fail on users')
                continue
            
    def postPageScrapers(self,userInfoPipline):
        headers = deepcopy(self.headers['htmlHeaders'])
        while True:
            if userInfoPipline.empty():
                time.sleep(1)
                continue
            headers['cookie'] = self.headers['cookie']
            userInfo,links = userInfoPipline.get().values()
            idx = 0
            userInfo['posts'] = []
            for link in links:
                try:
                    url = 'https://www.xiaohongshu.com'+link
                    response = requests.get(url,headers = headers)
                    response = self.antiDetect(response,url,headers)

                    soup = bs(response.content.decode('utf-8'),'html.parser')
                    
                    idx,post= grabing(soup,self.headers,userInfo,idx)
                    # return 
                except:
                    self.updateCookie(url)
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
    for _ in range(1):
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