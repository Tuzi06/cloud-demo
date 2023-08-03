import pexpect
from selenium.webdriver import Chrome,ChromeOptions
from urllib.parse import urlencode
import pickle,queue,os,time,requests,json,hashlib
from utls import GCloudConnection

from lowlevel.main import prepare_driver,Producer

url = 'https://www.xiaohongshu.com/explore'
class Master(GCloudConnection):
    def __init__(self,URL):
        GCloudConnection.__init__(self,URL,LOG_NAME='master-scrapper')
        self.URL = URL
        self.userQueue = queue.Queue()
        self.producer = prepare_driver(pickle.load(open('lowlevel/ins_cookies.pkl','rb')),1,False)[0]
        self.producer.get('https://www.instagram.com/explore/search/keyword/?q=%s'%('tech'))
        self.userlog = []
        self.restarting = False

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
            response = requests.get(url,timeout=10)
            print(response.content)
    
    def restartNode(self):
        try:
            print("request a new ip for instance")
            deploy = pexpect.spawn('gcloud app deploy orchestra.yaml --version v1')
            deploy.expect('Do you want to continue (Y/n)?')
            deploy.sendline('Y')
            deploy.expect("Deployed service", timeout=100)
            self.restarting =True
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
                    Producer(self.producer,self.userQueue)
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
        url = "http://scraper-394300.uc.r.appspot.com" #local mode
    master = Master(url)
    master.process()