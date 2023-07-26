from selenium.webdriver import Chrome,ChromeOptions
from urllib.parse import urlencode
import pickle,queue,os,time,requests,json,hashlib

from sympy import false
from lowlevel.main import prepare_driver,Producer

url = 'https://www.xiaohongshu.com/explore'
class Master:
    def __init__(self,URL):
        self.URL = URL
        self.userQueue = queue.Queue()
        self.producer = prepare_driver(pickle.load(open('lowlevel/xhs_cookies.pkl','rb')),1,False)
        self.userlog = []

    def start(self):
        try:
            requests.get(f"{self.URL}/start", timeout=300)
        except Exception:
            print("Scraper not running")

    def checkState(self):
        try:
            response = requests.get(f"{self.URL}/state", timeout=10000)
            # print(f"{self.URL}")
            state = response.content.decode("utf-8")
        except Exception:
            state = "no-answer"
        return state
    
    def sendJob(self):
        # job = self.current_job
        job = self.userQueue.get()
        if job not in self.userlog:
            url = self.URL + "/job?" +urlencode({'url':job,'aaa':''})
            self.userlog.append(job)
            print(f"starting scraping job {job} at {self.URL}")
            requests.get(url,timeout=10)
    
    def restartNode(self):
        try:
            print("request a new ip for instance")
            deploy = requests.get(f'{self.URL}/restart',timeout=10)
        except  Exception as  e:
            self.is_restarting = False
            print(f"Problem re-deploying: {e}")

    def process(self):
        state = ''
        while state != 'done':
            state = self.checkState()
            next_job_ready = False # wont change if state == "busy" or "no-answer"
            if state == "not-started":
                self.start()
            if state == 'starting':
                continue
            if state == "scraping-detected" and self.is_restarting == False:  # Error 429 in slave.
                self.restartNode()
            # elif state == 'busy':
            #     time.sleep(5)
            #     continue
            elif state == "idle":
                next_job_ready = True
                if self.userQueue.empty():
                    Producer(self.producer[0],self.userQueue)
            if next_job_ready:
                self.sendJob()
            time.sleep(1)
        self.producer[0].quit()
        posts = requests.get(f"{self.URL}/download").content.decode("utf-8")
        open('testres.json','w').write(json.dumps(posts,ensure_ascii=False,indent=4))
        

    def prepare_queue(self):
        jobs = json.load(open('jobs.json','r'))
        for job in jobs:
            self.userQueue.put(job)

if __name__ == "__main__":
    url = os.getenv("URL")
    print(url)
    if url is None:
        url = "http://192.168.1.67:5000" #local mode
    master = Master(url)
    master.process()