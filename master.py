import datetime
import time
import requests
from bs4 import BeautifulSoup as bs
headers = {
  'authority': 'www.xiaohongshu.com',
  'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
  'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
  'cache-control': 'max-age=0',
  'cookie': 'abRequestId=6cb1ec56-779e-568e-bdf7-b87037699d68; xsecappid=xhs-pc-web; a1=18cd7fea021brvkco87lhltzh5f8g6cx6bpo22akj30000313848; webId=529f96e525dec4769e99e9f75b35abe0; gid=yYSfWid0WdKiyYSfWid08DJ0JyDFhTSlYW1xUTV19ux2ilq8YkKSCJ888qyqY4Y8WjJqKJjJ; cache_feeds=[]; web_session=0400697918e7f1e4f6f5086a8d374b502cd533; unread={%22ub%22:%2265b7eadc000000000103028f%22%2C%22ue%22:%2265b7626a000000002d00399e%22%2C%22uc%22:29}; webBuild=4.1.5; websectiga=3fff3a6f9f07284b62c0f2ebf91a3b10193175c06e4f71492b60e056edcdebb2',
  'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"',
  'sec-fetch-dest': 'document',
  'sec-fetch-mode': 'navigate',
  'sec-fetch-site': 'same-origin',
  'sec-fetch-user': '?1',
  'upgrade-insecure-requests': '1',
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
}
class Master():
    def __init__(self,url):
        self.url = url

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
        userlog = []
        if self.checkState() == 'cold':
            requests.get(f"{self.url}/start",json= {'userScraper':10,'postScraper':10,'userlog':userlog},timeout=1000)
            requests.get('http://127.0.0.1:3001/start')    
        num = requests.get('http://127.0.0.1:3001/count').content.decode("utf-8")
        requestnum = 100000 - int(num) # the num of post we need 
        print(f"{requestnum} post need be scrapped")
        while True:
            kill = False
            html = bs(requests.get('https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend',headers = headers).content,'html.parser')
            userlinks = ['https://www.xiaohongshu.com'+title['href']for title in html.findAll('a',class_='author')]

            if self.checkState() == 'full':
                time.sleep(2)
                continue
            for userlink in userlinks:
                try:
                    self.sendJobs(userlink)
                except:
                    continue

                progress= int(requests.get('http://127.0.0.1:3001/count').content.decode("utf-8"))
                percent = ("{0:." + str(2) + "f}").format(100 * (progress/ float(requestnum)))
                print(f'\r progress: {percent}% Complete', end = '\r')
                if progress>= requestnum:
                    kill =True
                    break
            if kill:
                return 
            
            
if __name__ == '__main__':
    # init()  # uncomment this line when you run this script for the first time, you need login to your account as usual and the script will store the cookie into a .pkl file

    # url = 'http://35.208.236.78:8080' # import your own ip address for your machine
    url = 'http://127.0.0.1:3000'
    master = Master(url)
    time.sleep(5)
    print(datetime.datetime.now(),'\n')
    start = time.perf_counter()
    master.process()
    end = time.perf_counter()
    print('\n Time is %4f hours'%((end - start)/3600)) 