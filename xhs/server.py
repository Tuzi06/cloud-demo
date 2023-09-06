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
        self.userInfoBrowsers = [webdriver.Remote(command_executor=f"{url}:4444/wd/hub",options=self.options) for _ in range(5)]
        self.postBrowsers = [webdriver.Remote(command_executor=f"{url}:4444/wd/hub",options=self.options) for _ in range(2)]
        # self.userInfoBrowsers=prepare_driver([],1,False)
        # self.postBrowsers=prepare_driver([],1,False)
        self.stop = False
    

    def userPageScraper(self,browser,userlinkPool,userInfoPipline,userLog):
        while not self.stop:
            if userlinkPool.empty() or userInfoPipline.qsize()>10:
                time.sleep(2)
                continue
            userlink = userlinkPool.get()
            try:
                browser.get(userlink)
                # time.sleep(1)
                # if ' https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(browser.current_url):
                #     browser.get(userlink)
                wait_for_page(browser,'note-item')
                soup = bs(browser.page_source,'html.parser')
                userInfo = getUser(soup)
            except:
                # print(traceback.print_exc())
                print('fail on users')
                continue
            if userlink not in userLog:
                userLog.append(userlink)
            
                if 'W' in userInfo['follow'] or '万' in userInfo['follow']:
                    userInfoPipline.put({'userInfo':userInfo,'links':[link['href'] for link in soup.findAll('a','cover ld mask')]})
                else:
                    userInfoPipline.put({'userInfo':userInfo,'links':[]})

    def postPageScrapers(self,browser,userInfoPipline,posts):
        while not self.stop:
            if userInfoPipline.empty():
                time.sleep(2)
                continue
            userInfo,links = userInfoPipline.get().values()
            idx = 0
            for link in links:
                if self.stop:
                    break
                try:
                    browser.get('https://www.xiaohongshu.com'+link) 
                    # time.sleep(1)
                    # if 'https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(browser.current_url):
                    #     browser.get('https://www.xiaohongshu.com'+link)
                    wait_for_page(browser,'comment-item')
                    soup = bs(browser.page_source,'html.parser')
                    idx,post= grabing(soup,userInfo,idx)
                except:
                    # print(traceback.print_exc())
                    print('fail on post')
                    continue
                post['url'] = 'https://www.xiaohongshu.com'+link
                posts.append(post)

app = Flask(__name__)

@app.route('/start')
def start():
    global userInfoPipline,userlinkPool,posts,userLog,scraper,processes
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
    processes.append(Process(target=scraper.maintainPipline,args=[scraper.state,scraper.stateChild,userlinkPool]))
    for process in processes:
        process.start()
    return 'finish starting'

@app.route('/state')
def fetchState():
    try:
        if userlinkPool.qsize()>30:
            return 'full'
        else:
            return 'ready'
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

@app.route('/poolState')
def poolState():
    return str(f"userInfoQueue:{userlinkPool.qsize()}, postQueue:{userInfoPipline.qsize()}")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)

    # docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=10 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true selenium/standalone-chrome
    # docker kill $(docker ps -q)
    # docker buildx build --platform linux/amd64 -t tuzi06/xhs-scraper:latest --push .