import time
import multiprocessing as mp
from flask import Flask,request
from multiprocessing import Process,Pipe,Manager
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from threading import Thread
from lowlevel.xhs2 import prepare_driver, wait_for_page,getUser,grabing

class Scraper():
    def __init__(self):
        self.state = 'ready'
        # self.options = webdriver.ChromeOptions()
        # self.options.add_argument('disable-blink-features=AutomationControlled')
        # self.options.add_argument('headless')
        # self.userInfoBrowser = [webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options) for _ in range(10)]
        # self.postBrowser = [webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options) for _ in range(10)]
        self.userInfoBrowsers=prepare_driver([],1)
        self.postBrowsers=prepare_driver([],1,False)
        self.stateParent,self.stateChild = Pipe()
        self.stop = False
        time.sleep(10)
    

    def userPageScraper(self,userlinkPool):
        return 
        while not self.stop:
            if userlinkPool.empty():
                time.sleep(3)
                continue
            # userlink = userlinkPool.get()
            # browser.get(userlink)
            # wait_for_page(browser,'note-item')
            # soup = bs(browser.page_source,'html.parser')
            # userInfo = getUser(soup)
            # if userlink not in userLog and ('W' in userInfo['follow'] or '万' in userInfo['follow']):
            #     self.userLog.append(userlink)
            #     userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
            # else:
                # userInfoPipline.put({'userInfo':userInfo,'links':[]})

    def postPageScrapeFarm(self,userInfoPipline,posts):
        def load(browser,userInfoPipline,posts):
            while True:
                if userInfoPipline.empty:
                    time.sleep(3)
                    continue
                userInfo,links = userInfoPipline.get().values()
                idx = 0
                for link in links:
                    try:
                        browser.get('https://www.xiaohongshu.com'+link)
                        wait_for_page(browser,'comment-item')
                        soup = bs(browser.page_source,'html.parser')
                        idx,post= grabing(soup,userInfo,idx)
                        posts.append(post)
                    except:
                        continue

        processes = []
        for browser in self.postBrowsers:
            processes.append(Process(target=load,args=[browser,userInfoPipline,posts]))
            processes[-1].start()
        while not self.stop:
            continue
        for process in processes:
            process.kill()
    
    def maintainPipline(self,stateChild,userlinkPool):
        self.stateChild = stateChild
        while not self.stop:
            if userlinkPool.qsize()>10:
                self.stateChild.send('full')
            else:
                self.stateChild.send('ready')

app = Flask(__name__)

@app.route('/start')
def start():
    mp.get_context('spawn')
    userInfoPipline =mp.Queue()

    global userlinkPool
    userlinkPool = mp.Queue()

    global posts
    posts = Manager().list()
    userLog = Manager().list()

    global scraper
    scraper = Scraper()

    for browser in scraper.userInfoBrowsers:
        Process(target=scraper.userPageScraper,args=[userlinkPool]).start()
    return 'ffff'
    Process(target=scraper.postPageScrapeFarm,args=[userInfoPipline,posts]).start()
    return 'ffff'
    Process(target=scraper.maintainPipline,args=[scraper.stateChild,userlinkPool]).start()
    time.sleep(10)
    return 'finish starting'

@app.route('/state')
def fetchState():
    try:
        if scraper.stateParent.poll(timeout=3):
            scraper.state = scraper.stateParent.recv()
        return scraper.state
    except:
        return 'cold'

@app.route('/processJob',methods = ['GET','POST'])
def processJob():
    userlinkPool.put(request.get_json()['userlink'])
    return 'process is ongoing'

@app.route('/stop')
def stop():
    scraper.stop = True
    for browser in scraper.postBrowsers+scraper.userInfoBrowsers:
        browser.quit()
    return list(posts)

@app.route('/progress')
def checkProgress():
    return str(len(list(posts)))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)



    #docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=5 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true selenium/standalone-chrome