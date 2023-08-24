import json
import os
import pickle
import time
import requests
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from lowlevel.xhs2 import prepare_driver

class Master():
    def __init__(self,url):
        self.url = url
        self.browser = prepare_driver(pickle.load(open('lowlevel/xhs_cookies.pkl','rb')),1,False)[0]
        self.posts = []

    def sendJobs(self,userlink):
        posts = requests.get(f"{self.url}/processJob",data={'userlink':userlink},timeout = 1000)
        self.posts += posts

    def checkState(self):
        try:
            response = requests.get(f"{self.url}/state", timeout=10000)
            state = response.content.decode("utf-8")
        except Exception:
            state = 'cold'
        return state
    
    def process(self):
        while len(self.posts)<100000:
            time.sleep(5)
            if self.checkState() == 'full':
                continue
            elif self.checkState() == 'cold':
                requests.get("{self.url}/start")
            else:
                wrappers = self.browser.find_elements(By.CLASS_NAME,'author-wrapper')
                userlinks = [wrapper.find_element(By.TAG_NAME,'a').get_attribute('href') for wrapper in wrappers]
                for userlink in userlinks:
                    self.sendJobs(userlink)
                
                self.browser.execute_script("arguments[0].scrollIntoView();",wrappers[-1])
        
        open('resust.json','w').write(json.dumps(self.posts,ensure_ascii=False,indent=4))

def init():
    soption = ChromeOptions()
    soption.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path= 'lowlevel/chromedriver-mac-arm64/chromedriver')
    driver = Chrome(options = soption,service=service)
    driver.get('https://wwww.xiaohongshu.com/explore')
    input('pause for login ... press enter when finished')
    cookies = driver.get_cookies()
    driver.quit()
    pickle.dump(cookies,open('lowlevel/xhs_cookies.pkl','wb'))

if __name__ == '__main__':
    init()
    url = os.getenv("URL")
    print(url)
    if url is None:
        url = 'http://192.168.1.67:5000'
        # url = "https://scraper-394300.uc.r.appspot.com" #local mode
    master = Master(url)
    master.process()