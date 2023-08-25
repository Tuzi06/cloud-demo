import time
from flask import Flask,request
from multiprocessing import Process,Pipe,Queue
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from lowlevel.xhs2 import prepare_driver, wait_for_page,getUser,grabing

class Scraper():
    def __init__(self):
        self.state = 'ready'
        self.options = webdriver.ChromeOptions()
        # self.options.add_argument('disable-blink-features=AutomationControlled')
        # self.options.add_argument('headless')
        # self.userInfoScraper = webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options)
        # self.postScraper = webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options)
        self.userInfoScraper=prepare_driver([],1)[0]
        self.postScraper=prepare_driver([],1,False)[0]
        self.stateParent,self.stateChild = Pipe()
        self.requestParent,self.requestChild = Pipe()
        self.responseParent,self.responseChild = Pipe()
        self.userLog = []
        self.stop = False

    def getUserInfo(self,requestChild,userInfoPipline):
        self.requestChild = requestChild
        while not self.stop:
            job = self.requestChild.recv()
            if not job:
                time.sleep(3)
                continue
            userlink,_ = job.values()
            print(userlink)
            self.userInfoScraper.get(userlink)
            wait_for_page(self.userInfoScraper,'note-item')
            soup = bs(self.userInfoScraper.page_source,'html.parser')
            userInfo = getUser(soup)
            print(userInfo)
            if userlink not in self.userLog and ('W' in userInfo['follow'] or '万' in userInfo['follow']):
                self.userLog.append(userlink)
                userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
            else:
                userInfoPipline.put({'userInfo':userInfo,'links':[]})

    def getPostData(self,responseParent,userInfoPipline):
        self.responseParent = responseParent

        while not self.stop:
            print(userInfoPipline.qsize())
            if userInfoPipline.empty():
                time.sleep(3)
                continue
            userInfo,links = userInfoPipline.get().values()
            print(userInfo,links)
            idx = 0
            posts = []
            for link in links:
                self.postScraper.get('https://www.xiaohongshu.com'+link)
                wait_for_page(self.postScraper,'comment-item')
                soup = bs(self.postScraper.page_source,'html.parser')
                idx,post= grabing(soup,userInfo,idx)
                posts.append(post)
            print(posts)
            self.responseParent.send(posts)
    
    def maintainPipline(self,stateChild,userInfoPipline):
        self.stateChild = stateChild
        while not self.stop:
            if userInfoPipline.qsize()>10:
                self.stateChild.send('full')
            else:
                self.stateChild.send('ready')

app = Flask(__name__)

@app.route('/start')
def start():
    userInfoPipline = Queue()
    global scraper
    scraper = Scraper()
    Process(target=scraper.getUserInfo,args=[scraper.requestChild,userInfoPipline]).start()
    Process(target=scraper.getPostData,args=[scraper.responseParent,userInfoPipline]).start()
    Process(target=scraper.maintainPipline,args=[scraper.stateChild,userInfoPipline]).start()
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
    scraper.requestParent.send(request.get_json())
    while True:
        posts = scraper.responseChild.recv()
        if posts != None:
            break
        time.sleep(3)
    print('post',posts)
    return posts

@app.route('/stop')
def stop():
    scraper.stop = True
    scraper.postScraper.quit()
    scraper.userInfoScraper.quit()
    return 'stopped'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)



    #docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=5 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true selenium/standalone-chrome