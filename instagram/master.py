import random
from selenium.webdriver.common.by import By
from urllib.parse import urlencode
import pickle,queue,os,time,requests,json
from lowlevel.ins import findPicture

from threading import Thread

from lowlevel.main import prepare_driver,Producer,init

# init()

url = 'https://www.xiaohongshu.com/explore'
cookies = pickle.load(open('lowlevel/ins_cookies_p.pkl','rb'))
producer = prepare_driver(cookies,1)[0]
finder = prepare_driver(cookies,1,False)[0]
worker = prepare_driver(cookies,1,False)[0]
class Master():
    def __init__(self,URL):
        self.URL = URL
        self.userQueue = queue.Queue()
        self.linkQueue = queue.Queue()
        self.codeQueue = queue.Queue()
        self.userlog = []
        self.tempStorage = []
        self.storage = []
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
            # print(process,state)d
        except Exception:
            state = "no-answer"
        return state
    
    def sendShortCodeJob(self):
        job = self.linkQueue.get()
        if job not in self.userlog:
            url = self.URL + "/userJob?" +urlencode({'url':job,'aaa':''})
            self.userlog.append(job)
            # print(f"starting scraping job {job} at {self.URL}")
            response = requests.get(url,timeout=1000).json()
            if response['shortCodes'] != []:
                self.codeQueue.put(response)
    
    def sendPostJob(self):
        userAndCode= self.codeQueue.get()
        # print(userAndCode)
        idx= 0
        for shortCode in userAndCode['shortCodes']:
            worker.get(f"https://www.instagram.com/p/{shortCode}/")
            time.sleep(2)
            buttons = worker.find_elements(By.CLASS_NAME,'x1i10hfl')
            for button in buttons:
                try: 
                    if button.get_attribute('role') == 'button' and button.get_attribute('tabindex') == '0' and 'View all'in button.text:
                        button.click()
                except:
                    continue
            pictures,idx = findPicture(worker,idx,userAndCode['userinfo'])
            post= requests.post(self.URL+'/dataJob',json = {'html':worker.page_source,'user':userAndCode['userinfo'],'pics':pictures},timeout=1000)
            if 'text' in post.json().keys() and 'comments'in post.json().keys():
                self.tempStorage.append(post.json())
            print(f"scrap {len(self.tempStorage)} posts")
    
    def processShortCode(self):
        while not self.stop:
            if self.codeQueue.qsize()>=10:
                print('shortCode queue is full')
                continue
            time.sleep(10)
            state = self.checkState('user')
            if state =='idle':
                self.sendShortCodeJob()
            elif state == 'not-started':
                self.start()

            time.sleep(5)

    def processPost(self):
        while not self.stop:
            state = self.checkState('data')
            if state =='idle':
                self.sendPostJob()
            
            time.sleep(5)
                

def maintain_queue(master):
    time.sleep(5)
    keywords = json.load(open('keywords.json','r'))
    random.shuffle(keywords)
    lengthPerKeyword = 5000//len(keywords)
    for keyword in keywords:
        print(keyword)
        master.count =0
        producer.get(f"https://www.instagram.com/explore/search/keyword/?q={keyword}")
        while len(master.tempStorage)<lengthPerKeyword:
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
        master.storage += master.tempStorage
        print(f"we now scrapped {len(master.storage)} totally")
        master.tempStorage = []
        master.userQueue = queue.Queue()
        master.linkQueue = queue.Queue()
        master.codeQueue = queue.Queue()
    master.stop = True
    master.producer.quit()
    master.finder.quit()
    master.worker.quit()
    open('posts.json','w').write(json.dumps(master.storage,ensure_ascii=False,indent=4))


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
    threads.append(Thread(target= master.processPost, args = {}))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    
    master.download()
    