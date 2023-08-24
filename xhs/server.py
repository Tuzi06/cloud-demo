from queue import Queue
import time
from flask import Flask,request
from multiprocessing import Process,Pipe
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from lowlevel.xhs2 import prepare_driver, wait_for_page,getUser,grabing

class Scraper():
    def __init__(self):
        self.state = 'ready'
        # self.options = webdriver.ChromeOptions()
        # self.options.add_argument('disable-blink-features=AutomationControlled')
        # self.options.add_argument('headless')
        # self.userInfoScraper = webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options)
        # self.postScraper = webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options)
        self.userInfoScraper=prepare_driver([],1,False)[0]
        self.postScraper=prepare_driver([],1,False)[0]
        self.userInfoPipline = Queue()
        self.stateParent,self.stateChild = Pipe
        self.requestParent,self.requestChild = Pipe
        self.responseParent,self.responseChild = Pipe
        self.userLog = []
        self.stop = False

    def getUserInfo(self,requestChild):
        self.requestChild = requestChild
        while not self.stop:
            userlink = self.requestChild.recv()
            if not userlink:
                time.sleep(3)
                continue
            self.userInfoScraper.get(userlink)
            wait_for_page(self.userInfoScraper,'note-item')
            soup = bs(self.userInfoScraper.page_source,'html.parser')
            userInfo = getUser(soup)
            if userlink not in self.userLog and ('W' in userInfo['follow'] or '万' in userInfo['follow']):
                self.userLog.append(userlink)
                self.userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
            else:
                self.userInfoPipline.put({'userInfo':userInfo,'links':[]})

    def getPostData(self,responseParent):
        self.responseParent = responseParent
        while not self.stop:
            if self.userInfoPipline.empty():
                time.sleep(3)
                continue
            userInfo,links = self.userInfoPipline.get().values()
            if links == []:
                 self.responseParent.send([])
            idx = 0
            posts = []
            for link in links:
                self.postScraper.get(link)
                wait_for_page(self.postScraper,'note-content')
                soup = bs(self.postScraper.page_source,'html.parser')
                idx,post= grabing(soup,userInfo,idx)
                posts.append(post)
            self.responseParent.send(posts)
    
    def maintainPipline(self,stateChild):
        self.stateChild = stateChild
        while not self.stop:
            if self.userInfoPipline.qsize()>10:
                self.stateChild.send('full')
            else:
                self.stateChild.send('ready')

app = Flask(__name__)

@app.route('/start')
def start():
    global scraper
    scraper = Scraper()
    Process(target=scraper.getUserInfo,args=[scraper.requestChild]).start()
    Process(target=scraper.getPostData,args=[scraper.responseParent]).start()
    Process(target=scraper.maintainPipline,args=[scraper.stateChild]).start()

@app.route('/state')
def fetchState():
    if scraper.stateParent.poll(timeout=3):
        scraper.state = scraper.stateParent.recv()
    return scraper.state

@app.route('/processJob')
def processJob():
    scraper.requestParent.send(request.data)
    while True:
        posts = scraper.responseChild.recv()
        if posts:
            break
        time.sleep(3)
    return posts

@app.route('/stop')
def stop():
    scraper.stop = True
    return 'stopped'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)