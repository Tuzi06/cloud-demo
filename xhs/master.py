import datetime
import json
import os
import pickle
import time
import requests
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from lowlevel.xhs2 import prepare_driver,wait_for_page


class Master():
    def __init__(self,url):
        self.url = url
        self.browser = prepare_driver(pickle.load(open('lowlevel/cookies_arm.pkl','rb')),1,False)[0]
        self.browser.get('https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend')

    def sendJobs(self,userlink):
        # print(userlink)
        requests.get(f"{self.url}/processJob",json={'userlink':userlink,'aaa':'aaa'},timeout = 10)

    def checkState(self):
        try:
            response = requests.get(f"{self.url}/state", timeout=5)
            state = response.content.decode("utf-8")
        except Exception:
            state = 'cold'
        return state


    def process(self):
        lastScrape = json.load(open('postFiltered.json','r'))
        # lastScrape = []
        requestnum = 150000 - len(lastScrape) # the num of post we need 
        print(f"{requestnum} post need be scrapped")

        userlog = json.load(open('userlog.json','r'))
        # userlog = []

        if self.checkState() == 'cold':
                requests.get(f"{self.url}/start",json= {'url':self.url[:-5],'userScraper':10,'postScraper':30,'userlog':userlog},timeout=1000)
        while True:
            wait_for_page(self.browser,'author-wrapper')
            wrappers = self.browser.find_elements(By.CLASS_NAME,'author-wrapper')
            userlinks = [wrapper.find_element(By.TAG_NAME,'a').get_attribute('href') for wrapper in wrappers]

            progress= int(requests.get(f"{self.url}/progress").content.decode("utf-8"))
            percent = ("{0:." + str(2) + "f}").format(100 * (progress/ float(requestnum)))
            print(f'\r progress: {percent}% Complete', end = '\r')

            if self.checkState() == 'full':
                time.sleep(2)
                continue
            for userlink in userlinks:
                try:
                    self.sendJobs(userlink)
                except:
                    continue
            self.browser.execute_script("arguments[0].scrollIntoView();",wrappers[-1])

            if progress >= requestnum:
                break
            
            
        posts = requests.get(f"{self.url}/download",timeout=100000).json() + lastScrape
        open('xhs_posts.json','w').write(json.dumps(posts,ensure_ascii=False,indent=4))

def init():
    soption = ChromeOptions()
    soption.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path= 'lowlevel/chromedriver-mac-arm64/chromedriver')
    driver = Chrome(options = soption,service=service)
    driver.get('https://www.xiaohongshu.com/explore')
    input('pause for login ... press enter when finished')
    cookies = driver.get_cookies()
    driver.quit()
    pickle.dump(cookies,open('lowlevel/xhs_cookies.pkl','wb'))

if __name__ == '__main__':
    # init()

    # url = 'http://192.168.1.91:8080'
    url = 'http://35.208.236.78:8080'
    # url = 'http://127.0.0.1:8080'
    master = Master(url)
    time.sleep(5)
    print(datetime.datetime.now(),'\n')
    start = time.perf_counter()
    master.process()
    end = time.perf_counter()
    print('\n Time is %4f hours'%((end - start)/3600)) 

    # 2023-09-11 02:21:48.793720