import json
import pickle
import time
from selenium.webdriver import Chrome,ChromeOptions,Remote
from multiprocessing import Process,Manager,Queue
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

service = Service(executable_path='lowlevel/chromedriver-linux64/chromedriver')
cookies = pickle.load(open('lowlevel/cookies_linux.pkl','rb'))
options = ChromeOptions()
options.add_argument('disable-blink-features=AutomationControlled')
options.add_argument('headless')
options.add_argument("--disable-dev-shm-usage")

browser1 = Chrome(service=service,options=options)
browser1.get('https://www.xiaohongshu.com/explore')
for cookie in cookies: 
    if isinstance(cookie.get('expiry'),float):
        cookie['expiry'] = int(cookie['expiry'])
    browser1.add_cookie(cookie)

browser2 = [Remote(command_executor=f"http://127.0.0.1:4444/wd/hub",options=options) for _ in range(10)]

total =  Manager().Value(int,0)
sucess = Manager().Value(int,0)
users = Manager().list()
queue = Queue()

# input('pause')
# pickle.dump(browser1.get_cookies(),open('lowlevel/cookies_arm.pkl','wb'))
browser1.get('https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend')
time.sleep(5)
def process(browser,total,sucess,users,queue):
    while total <10000:
        if queue.empty():
            time.sleep(1)
            continue
        user = queue.get()
        try:
            browser.get(user)
            time.sleep(2)
            soup = bs(browser.page_source,'html.parser')
            follow = soup.findAll('span',class_='count')[1].text
        except:
            continue
        total += 1
        if 'W' in follow or '万' in follow:
            sucess+=1
            users.append(user)
    browser.quit()

for browser in browser2:
    Process(target=process,args= [browser,total,sucess,users,queue]).start()
while total<10000:
    wrappers = browser1.find_elements(By.CLASS_NAME,'author-wrapper')
    userlinks = [wrapper.find_element(By.TAG_NAME,'a').get_attribute('href') for wrapper in wrappers]
    browser1.execute_script("arguments[0].scrollIntoView();",wrappers[-1])
    for user in userlinks:
        queue.put(user)
        p1 = ("{0:." + str(3) + "f}").format(100 * (sucess/total))
        print(f"  {p1}% of user has follow greater than 10000, and {total} users checked",end="\r")
browser1.quit()

print(f"\n total has {sucess} users has more than 10000 follows")
open('users.json','w').write(json.dumps(users,ensure_ascii=False,indent=4))