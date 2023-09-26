import json
import pickle
import time
from selenium.webdriver import Chrome,ChromeOptions,Remote
from multiprocess import Process,Manager
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

def process(browser,users,queue):
    while True:
        if queue.empty():
            time.sleep(1)
            continue

        user = queue.get()
        try:
            browser.get(user)
            time.sleep(2)
            soup = bs(browser.page_source,'html.parser')
            follow = soup.findAll('span',class_='count')[1].text
            # like = soup.findAll('span',class_='count')[2].text
        except:
            continue

        if  'W'in follow: # users has more than 1k follows but less than 10k
            users.append(user)
            # while True:
            #     oldnum = len(posts)
            #     notes = browser.find_elements(By.CLASS_NAME,'note-item')
            #     items = [item.find_element(By.TAG_NAME,'a')for item in notes]
            #     posts += [item.get_attribute('href') for item in items]
            #     posts = list(set(posts))
            #     if len(posts) == oldnum or len(posts)>= 100:
            #         break
            #     browser.execute_script("arguments[0].scrollIntoView();",notes[-1])
            #     time.sleep(1)
            
            # if str(len(posts)) in users:
            #     users[str(len(posts))] +=1
            # else:
            #     users[str(len(posts))] =1
        
        # docker run -d -p 4444:4444 -e SE_NODE_MAX_SESSIONS=40 -e SE_NODE_OVERRIDE_MAX_SESSIONS=true -e SE_NODE_SESSION_TIMEOUT=86400 seleniarm/standalone-chromium

def init():
    soption = ChromeOptions()
    soption.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path= 'lowlevel/chromedriver-mac-arm64/chromedriver')
    driver = Chrome(options = soption,service=service)
    driver.get('https://www.xiaohongshu.com/explore')
    input('pause for login ... press enter when finished')
    cookies = driver.get_cookies()
    driver.quit()
    pickle.dump(cookies,open('lowlevel/cookies_arm.pkl','wb'))

def main():
    # init()
    service = Service(executable_path='lowlevel/chromedriver-mac-arm64/chromedriver')
    cookies = pickle.load(open('lowlevel/cookies_arm.pkl','rb'))
    options = ChromeOptions()
    options.add_argument('disable-blink-features=AutomationControlled')
    options.add_argument("--disable-dev-shm-usage")

    browsers = [Chrome(service=service,options=options)]
    # browsers += [Chrome(service=service,options=options)]
    options.add_argument('headless')
    # browsers += [Remote(command_executor=f"http://127.0.0.1:4444/wd/hub",options=options) for _ in range(15)]
    for browser in browsers:
        browser.get('https://www.xiaohongshu.com/explore')
        for cookie in cookies: 
            if isinstance(cookie.get('expiry'),float):
                cookie['expiry'] = int(cookie['expiry'])
            browser.add_cookie(cookie)

    browsers += [Remote(command_executor=f"http://127.0.0.1:4444/wd/hub",options=options) for _ in range(15)]

    log  = []
    users = Manager().list()
    queue = Manager().Queue()

    # input('pause')
    # pickle.dump(browser1.get_cookies(),open('lowlevel/cookies_arm.pkl','wb'))

    browsers[0].get('https://www.xiaohongshu.com/explore?channel_id=homefeed_recommend')
    time.sleep(3)
    ps = []
    browser1 = browsers[0]
    for browser in browsers[1:]:
        p = Process(target=process,args= [browser,users,queue])
        p.daemon=True
        ps.append(p)
        p.start()
    
    while len(users)<100:
        try:
            wrappers = browser1.find_elements(By.CLASS_NAME,'author-wrapper')
            userlinks = [wrapper.find_element(By.TAG_NAME,'a').get_attribute('href') for wrapper in wrappers]
        except:
            continue
        print(f" {len(users)} users has meet requirement, and {len(log)} users has been checked",end = '\r')
        if queue.qsize()>10:
            time.sleep(2)
            continue

        browser1.execute_script("arguments[0].scrollIntoView();",wrappers[-1])
        for user in userlinks:
            if user not in log:
                queue.put(user)
                log.append(user)
            
            # p1 = ("{0:." + str(3) + "f}").format(100 * (len(users)/len(total)))
            print(f" {len(users)} users has meet requirement, and {len(log)} users has been checked",end = '\r')
            # if len(users.keys()) != 0:
            #     print(f"median post num that users(>1000 follow ) has is {users.keys()[0]}",end = '\r')
            time.sleep(1)
    # for p in ps:
    #     p.join()
    for browser in browsers:
        browser.quit()

    # while not queue.empty():
    #     time.sleep(1)
    #     continue
    # # p1 = ("{0:." + str(3) + "f}").format(100 * (len(users)/len(total)))
    open('10k_follow.json','w').write(json.dumps(list(users),ensure_ascii=False,indent=4))

if __name__ == '__main__':
    main()