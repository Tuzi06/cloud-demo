import pickle
import lowlevel.ins as ins  
from selenium import webdriver
from selenium. webdriver.common.by import By
import sys,time,random
from selenium.webdriver.chrome.service import Service


url = 'https://www.instagram.com/'

def init():
    soption = webdriver.ChromeOptions()
    soption.add_argument('disable-blink-features=AutomationControlled')
    service = Service(executable_path='lowlevel/chromedriver-mac-arm64/chromedriver')
    driver = webdriver.Chrome(options = soption,service=service)
    driver.get(url)
    input('pause for login ... press enter when finished')
    cookies = driver.get_cookies()
    driver.quit()
    pickle.dump(cookies, open('lowlevel/ins_cookies_p.pkl','wb'))
    
def prepare_driver(cookies,workers,headless = True,proxy = ''):
    drivers = []
    options = webdriver.ChromeOptions()
    # options.add_argument('disable-blink-features=AutomationControlled')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    options.add_argument("--disable-extensions")

    if proxy != '':
        print(proxy)
        options.add_argument('--proxy-server={}'.format(proxy))
    if sys.platform == 'linux':
        service = Service(executable_path= '/usr/bin/chromedriver.exe')
    elif sys.platform == 'darwin':
        service = Service(executable_path='lowlevel/chromedriver-mac-arm64/chromedriver')
    if headless:
        options.add_argument('headless')
    
    for _ in range(workers):
        driver = webdriver.Chrome(options = options,service=service)
        driver.get(url)
        time.sleep(1)
        driver.get(url)
        for cookie in cookies: 
            if isinstance(cookie.get('expiry'), float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        # driver.refresh()
        drivers.append(driver)
    return drivers

def Producer(driver,userQueue):
    # print('https://www.instagram.com/explore/search/keyword/?q=%s%s'%(tag,random.choice(chartoken)))
    ins.wait_for_page(driver,'x1gryazu')
    containers = driver.find_element(By.CLASS_NAME,'x1gryazu')
    containers = containers.find_element(By.TAG_NAME,'section')
    containers = containers.find_elements(By.TAG_NAME,'a')
    links = [link.get_attribute('href') for link in containers]
    links = [link for link in links if 'https://www.instagram.com/p/' in link ]
    random.shuffle(links)
 
    for link in links:
        userQueue.put({'link':link,'catigory':''})
    driver.execute_script("arguments[0].scrollIntoView();",containers[-1])
        # print( '\n now has %i posts \n'%(len(posts)))

    