import pexpect
import pickle,queue,os,time,requests,json,hashlib
from utls import GCloudConnection


url = 'https://www.xiaohongshu.com/explore'
class Master(GCloudConnection):
    def __init__(self,URL):
        GCloudConnection.__init__(self,URL,LOG_NAME='master-scrapper')
        self.URL = URL
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
        url = self.URL + "/job" 
        print(f"starting scraping job at {self.URL}")
        requests.get(url,timeout=10)
    
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
            if next_job_ready:
                self.sendJob()
            time.sleep(1)

if __name__ == "__main__":
    url = os.getenv("URL")
    if url is None:
        url = "http://0.0.0.0:8081" #local mode
    print(url)
    master = Master(url)
    master.process()