import time
import traceback
from flask import Flask,request
from multiprocessing import Process,Pipe,Manager,Queue
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from lowlevel.xhs2 import prepare_driver, wait_for_page,getUser,grabing

class Scraper():
    def __init__(self,url):
        self.state = 'ready'
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('disable-blink-features=AutomationControlled')
        self.options.add_argument('headless')
        self.options.add_argument("--disable-dev-shm-usage")
        self.userInfoBrowsers = [webdriver.Remote(command_executor=f"localhost:4444/wd/hub",options=self.options) for _ in range(5)]
        self.postBrowsers = [webdriver.Remote(command_executor=f"localhost:4444/wd/hub",options=self.options) for _ in range(3)]
        # self.userInfoBrowsers=prepare_driver([],1,False)
        # self.postBrowsers=prepare_driver([],1,False)
        self.stateParent,self.stateChild = Pipe()
        self.stop = False
    

    def userPageScraper(self,browser,userlinkPool,userInfoPipline,userLog):
        while not self.stop:
            if userlinkPool.empty() or userInfoPipline.qsize()>10:
                time.sleep(3)
                continue
            userlink = userlinkPool.get()
            try:
                browser.get(userlink)
                time.sleep(1)
                if ' https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(browser.current_url):
                    browser.get(userlink)
                wait_for_page(browser,'note-item')
                soup = bs(browser.page_source,'html.parser')
                userInfo = getUser(soup)
            except:
                # print(traceback.print_exc())
                print('fail on users')
                continue
            if userlink not in userLog:
                userLog.append(userlink)
                try: 
                    if int(userInfo['follow'])>=10000:
                        userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
                        continue
                except:
                    if 'W' in userInfo['follow'] or '万' in userInfo['follow']:
                        userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
                        continue
                userInfoPipline.put({'userInfo':userInfo,'links':[]})

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
                try:
                    browser.get('https://www.xiaohongshu.com'+link)

                    if 'https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(browser.current_url):
                        browser.get('https://www.xiaohongshu.com'+link)
                    wait_for_page(browser,'comment-item')
                    soup = bs(browser.page_source,'html.parser')
                    idx,post= grabing(soup,userInfo,idx)
                except:
                    # print(traceback.print_exc())
                    print('fail on post')
                    continue
                post['url'] = link
                posts.append(post)

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
    global userlinkPool,posts,userLog,scraper,processes
    userInfoPipline =Queue()
    userlinkPool = Queue()
    posts = Manager().list()
    userLog = Manager().list()
    url,_ = request.get_json().values()
    scraper = Scraper(url)
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
    for browser in scraper.postBrowsers+scraper.userInfoBrowsers:
        browser.quit()
    return list(posts)
@app.route('/download')
def download():
    return list(posts)

@app.route('/progress')
def checkProgress():
    return str(len(list(posts)))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

    # docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=50 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_SESSION_TIMEOUT=86400 selenium/standalone-chrome
    # docker kill $(docker ps -q)
    # docker buildx build --platform linux/amd64 -t tuzi06/xhs-scraper:latest --push .