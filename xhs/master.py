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
        self.browser = prepare_driver(pickle.load(open('lowlevel/xhs_cookies.pkl','rb')),1)[0]

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
        
        requestnum = 10000 # the num of post we need 

        if self.checkState() == 'cold':
                requests.get(f"{self.url}/start",json= {'url':self.url[:-5],'userScraper':5,'postScraper':40},timeout=1000)
                time.sleep(5)
        while int(requests.get(f"{self.url}/progress").content.decode("utf-8"))<requestnum:
            wait_for_page(self.browser,'author-wrapper')
            wrappers = self.browser.find_elements(By.CLASS_NAME,'author-wrapper')
            userlinks = [wrapper.find_element(By.TAG_NAME,'a').get_attribute('href') for wrapper in wrappers]
            if self.checkState() == 'full':
                time.sleep(2)
                continue
            for userlink in userlinks:
                time.sleep(0)
                try:
                    self.sendJobs(userlink)
                except:
                    continue
                
            self.browser.execute_script("arguments[0].scrollIntoView();",wrappers[-1])
            print(int(requests.get(f"{self.url}/progress").content.decode("utf-8"))/requestnum)
        posts = requests.get(f"{self.url}/download").json()
        print(type(posts))
        
        open('resust.json','w').write(json.dumps(posts,ensure_ascii=False,indent=4))

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

    # url = 'http://192.168.1.67:8080'
    url = 'http://35.208.201.235:8080'

    master = Master(url)
    time.sleep(5)
    print(datetime.datetime.now(),'\n')
    start = time.perf_counter()
    master.process()
    end = time.perf_counter()
    print('time is %4f hours'%((end - start)/3600)) 