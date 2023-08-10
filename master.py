from selenium.webdriver.common.by import By
from urllib.parse import urlencode
import pickle,queue,os,time,requests,json

from threading import Thread

from lowlevel.main import prepare_driver,Producer

url = 'https://www.xiaohongshu.com/explore'
producer = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]
finder = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]
class Master():
    def __init__(self,URL):
        self.URL = URL
        self.userQueue = queue.Queue()
        self.linkQueue = queue.Queue()
        self.codeQueue = queue.Queue()
        self.userlog = []
        self.count = 0
        self.stop = False

    def start(self):
        try:
            requests.get(f"{self.URL}/start", timeout=300)
        except Exception:
            print("Scraper not running")

    def checkState(self,process):
        try:
            response = requests.get(f"{self.URL}/state?{urlencode({'process':process,'aaa':''})}", timeout=10000)
            state = response.content.decode("utf-8")
            print(state)
        except Exception:
            state = "no-answer"
        return state
    
    def sendShortCodeJob(self):
        job = self.linkQueue.get()
        if job not in self.userlog:
            url = self.URL + "/userJob?" +urlencode({'url':job,'aaa':''})
            self.userlog.append(job)
            print(f"starting scraping job {job} at {self.URL}")
            response = requests.get(url,timeout=1000)
            print(json.load(response.content))
            self.codeQueue.put(json.load(response.content))
    
    def sendPostJob(self):
        shortCodes= self.codeQueue.get()
        url = self.URL+'/userJob?'+urlencode({'shortCodes':shortCodes,'aaa':''})
        self.count= requests.get(url,timeout=1000)
        
    
    def processShortCode(self):
        state = ''
        while not self.stop:
            state = self.checkState('user')
            if state =='idle':
                self.sendShortCodeJob()
            else:
                time.sleep(3)
                

def maintain_queue(master):
    time.sleep(5)
    keywords = json.load(open('keywords.json','r'))
    lengthPerKeyword = 5000//len(keywords)
    for keyword in keywords:
        print(keyword)
        master.count =0
        producer.get(f"https://www.instagram.com/explore/search/keyword/?q={keyword}")
        while master.count<=lengthPerKeyword:
            if master.linkQueue.qsize()>10:
                continue
            Producer(producer,master.userQueue)
            while not master.userQueue.empty():
                    link =master.userQueue.get()['link']
                    finder.get(link)
                    time.sleep(2)
                    container = finder.find_element(By.CLASS_NAME,'_aaqt')
                    url = container.find_element(By.TAG_NAME,'a')
                    master.linkQueue.put(url.get_attribute('href'))
    master.stop = True
    master.producer.quit()
    master.finder.quit()


if __name__ == "__main__":
    url = os.getenv("URL")
    print(url)
    if url is None:
        url = 'http://192.168.1.67:5000'
        # url = "https://scraper-394300.uc.r.appspot.com" #local mode
    master = Master(url)
    print('started')
    threads = []
    threads.append(Thread(target = maintain_queue, args = {master}))
    threads.append(Thread(target = master.processShortCode,args = {}))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    master.download()
    