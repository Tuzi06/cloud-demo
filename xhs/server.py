import time
from flask import Flask,request
from multiprocessing import Process,Pipe,Manager,Queue
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from lowlevel.xhs2 import prepare_driver, wait_for_page,getUser,grabing

class Scraper():
    def __init__(self):
        self.state = 'ready'
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('disable-blink-features=AutomationControlled')
        self.options.add_argument('headless')
        self.options.add_argument("--disable-dev-shm-usage")
        self.userInfoBrowsers = [webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options) for _ in range(8)]
        self.postBrowsers = [webdriver.Remote(command_executor='http://localhost:4444/wd/hub',options=self.options) for _ in range(6)]
        # self.userInfoBrowsers=prepare_driver([],1,False)
        # self.postBrowsers=prepare_driver([],1,False)
        self.stateParent,self.stateChild = Pipe()
        self.stop = False
        time.sleep(5)
    

    def userPageScraper(self,browser,userlinkPool,userInfoPipline,userLog):
        print('started')
        while not self.stop:
            if userlinkPool.empty():
                time.sleep(3)
                continue
            userlink = userlinkPool.get()
            browser.get(userlink)
            wait_for_page(browser,'note-item')
            soup = bs(browser.page_source,'html.parser')
            try:
                userInfo = getUser(soup)
            except:
                continue
            if userlink not in userLog and ('W' in userInfo['follow'] or '万' in userInfo['follow']):
                userLog.append(userlink)
                print(userInfo)
                userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
            else:
                userInfoPipline.put({'userInfo':userInfo,'links':[]})
        browser.quit()

    def postPageScrapers(self,browser,userInfoPipline,posts):
        while not self.stop:
            if userInfoPipline.empty():
                time.sleep(3)
                continue
            userInfo,links = userInfoPipline.get().values()
            idx = 0
            for link in links:
                if self.stop:
                    break
                browser.get('https://www.xiaohongshu.com'+link)
                wait_for_page(browser,'comment-item')
                soup = bs(browser.page_source,'html.parser')
                try:
                    idx,post= grabing(soup,userInfo,idx)
                except:
                    print('fail on post')
                    continue
                post['url'] = link
                posts.append(post)
        browser.quit()
    

    def maintainPipline(self,stateChild,userlinkPool):
        self.stateChild = stateChild
        while not self.stop:
            time.sleep(2)
            if userlinkPool.qsize()>10 and self.state != 'full':
                self.stateChild.send('full')
            elif self.state != 'ready':
                self.stateChild.send('ready')

app = Flask(__name__)

@app.route('/start')
def start():
    global userInfoPipline
    userInfoPipline =Queue()

    global userlinkPool
    userlinkPool = Queue()

    global posts
    posts = Manager().list()
    global userLog
    userLog = Manager().list()

    global scraper
    scraper = Scraper()
    global processes
    processes = []
    for browser in scraper.userInfoBrowsers:
        processes.append(Process(target=scraper.userPageScraper,args=[browser,userlinkPool,userInfoPipline,userLog]))
    for browser in scraper.postBrowsers:
         processes.append(Process(target=scraper.postPageScrapers,args=[browser,userInfoPipline,posts]))
    processes.append(Process(target=scraper.maintainPipline,args=[scraper.stateChild,userlinkPool]))
    for process in processes:
        process.start()
    return 'finish starting'

@app.route('/state')
def fetchState():
    try:
        if scraper.stateParent.poll(timeout=3):
            scraper.state = scraper.stateParent.recv()
            print(scraper.stateParent.recv())
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
    # for process in processes:
    #     process.kill()
    # for browser in scraper.postBrowsers+scraper.userInfoBrowsers:
    #     browser.quit()
    return list(posts)

@app.route('/progress')
def checkProgress():
    return str(len(list(posts)))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)



    #docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=5 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true selenium/standalone-chrome
    #docker kill $(docker ps -q)