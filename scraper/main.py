import scraper.xhs2 as xhs
from selenium import webdriver
from selenium. webdriver.common.by import By
from threading import Thread
from queue import Queue
import sys,pickle,time,datetime,json
from selenium.webdriver.chrome.service import Service

url = 'https://www.xiaohongshu.com/explore'

def init():
    soption = webdriver.ChromeOptions()
    soption.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path= 'chromedriver_mac_arm64/chromedriver')
    driver = webdriver.Chrome(options = soption,service=service)
    driver.get(url)
    input('pause for login ... press enter when finished')
    cookies = driver.get_cookies()
    driver.quit()
    return cookies

def prepare_driver(cookies,workers,headless = True):
    drivers = []
    options = webdriver.ChromeOptions()
    options.add_argument('disable-blink-features=AutomationControlled')
    
    service = Service(executable_path= '../chromedriver_mac_arm64/chromedriver')

    if headless:
        options.add_argument('headless')
    for _ in range(workers):
        driver = webdriver.Chrome(options = options,service=service)
        driver.get(url)
        for cookie in cookies: 
            if isinstance(cookie.get('expiry'), float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        driver.refresh()
        drivers.append(driver)
    return drivers

# single producer multi consumer version of main function
def Producer(driver,userQueue,posts,postnum,finderNum):
    firstround = True
    while len(posts)<=postnum:
        if userQueue.qsize() < finderNum:
            xhs.wait_for_page(driver,'note-item')
            if 'https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(driver.current_url):
                driver.get(url)
            elements= driver.find_elements(By.CLASS_NAME,'author-wrapper')
            try:
                linklist=[(element.find_element(By.TAG_NAME,'a')).get_attribute('href') for element in elements]
            except:
                driver.refresh()
                continue
            lastelement = elements[-1]
            linklist = list(set(linklist))
            if not firstround:
                linklist = linklist[1:]
            for link in linklist:
                userQueue.put(link)
            driver.execute_script("arguments[0].scrollIntoView();",lastelement)

            print( '\n now has %i posts\n'%(len(posts)))
            firstround = False
        else:
            continue
    while not userQueue.empty():
        userQueue.get()
    driver.quit()
    print('producer end now has posts: ', len(posts))

def Finder(driver,userQueue,infoQueue,workerNum,users):
    # time.sleep(5)
    full = False
    while not userQueue.empty():
        if infoQueue.qsize() >= 2 * workerNum:
            if not full:
                # print('info queue is full')
                full = True
            continue
        full = False
        
        try:
            userlink = userQueue.get()
            driver.get(userlink)
            if ' https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(driver.current_url):
                driver.get(userlink)
            xhs.wait_for_page(driver,'user-interactions')
            user = xhs.getUser(driver)
            user['userLink'] = userlink 
            if userlink not in users and ('W' in user['follow'] or '万' in user['follow']):
                infoQueue.put({'info':user,'post':xhs.getLinks(driver)}) 
                users.append(userlink)
        except:
            # userQueue.put(userlink) 
            continue
    while not infoQueue.empty():
        infoQueue.get()
    driver.quit()
    print('finder end')

def Worker(driver,userQueue,infoQueue,posts):
    while not userQueue.empty():
        if infoQueue.empty():
            continue
        try:
            info = infoQueue.get()
            # print(info['info'])
            xhs.run(driver,info['post'],posts,info['info'])
        except:
            continue
    driver.quit()
    print('worker end')
       

def main(postnum,finderNum = 1):
    # cookies = init()
    # pickle.dump(cookies, open('cookies/xhs_cookies.pkl','wb'))

    cookies = pickle.load(open("../cookies/xhs_cookies.pkl", "rb"))

    posts = []
    users = [] #users is a list that collects viewed users

    userQueue = Queue()
    infoQueue = Queue()

    threads = []
    producer = prepare_driver(cookies,1)[0]

    # preparer finders and workers
    finderNum = min(finderNum,5)
    finders = prepare_driver(cookies,finderNum)
    
    # number of workers 
    num = finderNum + 1 
    workers = prepare_driver([],num)

    # start producer for finding user candidates
    threads.append(Thread(target = Producer, args = (producer,userQueue,posts,postnum,finderNum)))
    threads[-1].start()
    while userQueue.qsize() <= 0:
        continue
    # finders to find users
    for finder in finders:
        threads.append(Thread(target = Finder, args =(finder,userQueue,infoQueue,num,users)))
        threads[-1].start()
    while infoQueue.qsize() <= num:
        continue
    print(datetime.datetime.now(),'\n')
    # workers to crawl posts
    for worker in workers:
        threads.append(Thread(target = Worker, args = (worker,userQueue,infoQueue,posts)))
        threads[-1].start()
    for thread in threads:
        thread.join()
    open('out/xhs_demo.json','w').write(json.dumps(posts,ensure_ascii=False,indent=4))
   
if __name__ == '__main__':
    postnum = int(sys.argv[1]) # number of post that want to crawl
    finderNum = int(sys.argv[2]) # thread number(recommed less than 5 or depends on network bandwidth)
    begin = time.perf_counter()
    main(postnum,finderNum)
    end = time.perf_counter()

    print('time is %4f hours'%((end - begin)/3600))