import json
import pickle
import time
from selenium import webdriver
from bs4 import BeautifulSoup as bs
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from multiprocessing import Process,Manager,Queue

def process(browser,userlinks,userPass,userFail,log):
    while not userlinks.empty():
        user = userlinks.get()
        browser.get(user)
        links = []
        fail = False
        while len(links)<100:
            time.sleep(2)
            oldlength = len(links)
            sections = browser.find_elements(By.CLASS_NAME,'note-item')
            links+=[section.find_elements(By.TAG_NAME,'a')[1] for section in sections]
            links = list(set(links))

            if len(links) == oldlength:
                userFail.append(user)
                fail = True
                break

            browser.execute_script("arguments[0].scrollIntoView();",sections[-1])
        if not fail:
            userPass.append(user)
        if str(len(links)) not in log:
            log[str(len(links))] = 1
        else:
            log[str(len(links))] += 1


def main():
    users = json.load(open('users.json','r'))

    log = Manager().dict()
    options = webdriver.ChromeOptions()
    options.add_argument('disable-blink-features=AutomationControlled')
    options.add_argument('headless')
    options.add_argument("--disable-dev-shm-usage")
    browsers = [webdriver.Remote(command_executor=f"http://127.0.0.1:4444/wd/hub",options=options) for _ in range(10)]

    # browsers = [webdriver.Chrome(options=options, service=Service(executable_path='lowlevel/chromedriver-linux64/chromedriver'))]

    cookies = pickle.load(open('lowlevel/cookies_linux.pkl','rb'))
    for browser in browsers:
        browser.get('https://www.xiaohongshu.com/explore')
        for cookie in cookies: 
            if isinstance(cookie.get('expiry'),float):
                cookie['expiry'] = int(cookie['expiry'])
            browser.add_cookie(cookie)
        browser.refresh()
    userlinks = Queue()
    for user in users:
        userlinks.put(user)

    userPass = Manager().list()
    userFail = Manager().list()
    processes = []
    for browser in browsers:
        processes.append(Process(target=process, args=[browser,userlinks,userPass,userFail,log]))
    for p in processes:
        p.start()

    total = len(users)
    length = 50
    while not userlinks.empty():
        percent = ("{0:." + str(2) + "f}").format(100 * ((total-userlinks.qsize()) / float(total)))
        filledLength = int(length * (total-userlinks.qsize()) // total)
        bar = '█' * filledLength + '-' * (length - filledLength)
        print(f'\r{bar}| {percent}% finished', end = '\r')
    for p in processes:
        p.join()
    print(f"\n\n{len(userPass)} users has more than 100 posts, {len(userFail)} users has less than 100 posts")
    # open('log.json','w').write(json.dumps(log,indent=4))
    print(log)

    for browser in browsers:
        browser.quit()
if __name__ =='__main__':
    main()