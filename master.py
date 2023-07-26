from selenium.webdriver import Chrome,ChromeOptions
from urllib.parse import urlencode
# from main import prepare_driver,Producer
import pickle,queue,os,time,requests,json,hashlib

url = 'https://www.xiaohongshu.com/explore'
class Master:
    def __init__(self,URL,require_num,finderNum):
    #    self.linkqueue = []
    #    self.users = []
    #    self.posts = []
    #    self.require_num = require_num
    #    self.data ={'url':'https://www.xiaohongshu.com/explore'}
    #    self.userQueue = queue.Queue()
    #    self.finderNum = finderNum
    #    self.current_job = None
    #    self.restarting = False
        self.URL = URL
        self.userQueue = queue.Queue()


    def start(self):
        try:
            requests.get(f"{self.URL}/start", timeout=3)
        except Exception:
            print("Scraper not running")

    def checkState(self):
        try:
            response = requests.get(f"{self.URL}/state", timeout=10)
            state = response.content.decode("utf-8")
        except Exception:
            state = "no-answer"
        return state
    
    def sendJob(self):
        # job = self.current_job
        job = self.userQueue.get()
        url = self.URL + "/job?" + hashlib.sha256(job.encode('utf-8')).hexdigest()
        response = requests.get(url,timeout=10).text
        print(response)
        # print(f"Sending job = {job} to {url}")
        # time.sleep(60)
    
    def restartNode(self):
        try:
            print("request a new ip for instance")
            deploy = requests.get(f'{self.URL}/restart',timeout=10)
        except  Exception as  e:
            self.is_restarting = False
            print(f"Problem re-deploying: {e}")

    def process(self):
        # while self.userQueue.qsize()> 0:
        #     self.sendJob()
        while self.userQueue.qsize() > 0:
            state = self.checkState()
            print(f"Current state: {state}")
            next_job_ready = False # wont change if state == "busy" or "no-answer"
            if state == "not-started":
                self.start()
            if state == "scraping-detected" and self.is_restarting == False:  # Error 429 in slave.
                self.userQueue.put(self.current_job)
                self.restartNode()
            elif state == "idle":
                next_job_ready = True
            if next_job_ready:
                self.current_job = self.userQueue.get()
                self.sendJob()
            time.sleep(3)

    def prepare_queue(self):
        jobs = json.load(open('jobs.json','r'))
        for job in jobs:
            self.userQueue.put(job)
        # cookies = pickle.load(open('xhs_cookies.pkl','rb'))
        # master_driver = prepare_driver(cookies,1)[0]
        # Producer(master_driver,self.userQueue,self.posts,self.require_num,self.finderNum)

if __name__ == "__main__":
    url = os.getenv("URL")
    print(url)
    if url is None:
        url = "http://192.168.64.128:8080" #local mode
    master = Master(url,1,1)
    master.prepare_queue()
    master.process()