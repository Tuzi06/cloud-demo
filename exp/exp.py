from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pickle,requests,time,json,traceback


url = 'https://www.instagram.com/explore/search/keyword/?q=tech'

options = ChromeOptions()
options.add_argument('disable-blink-features=AutomationControlled')
options.add_argument('— disk-cache-size=0')
# options.add_experimental_option("excludeSwitches", ["enable-automation"])
# options.add_experimental_option('useAutomationExtension', False)
# options.add_argument('--blink-settings=imagesEnabled=false')
# options.page_load_strategy = 'none'
# # options.add_argument('no-sandbox')
# options.add_argument('--disable-features=MediaRouter')
# options.add_experimental_option("prefs", {"profile.managed_default_content_settings.stylesheet":2})
# options.add_argument('headless')
service = Service(executable_path= '../chromedriver_mac_arm64/chromedriver')
driver = Chrome(options = options, service=service)
driver.get(url)

scraper = Chrome(options=options,service=service)
scraper.get(url)

cookies = pickle.load(open('../cookies/ins_cookies.pkl','rb'))

for cookie in cookies: 
    if isinstance(cookie.get('expiry'), float):
        cookie['expiry'] = int(cookie['expiry'])
    driver.add_cookie(cookie)
    scraper.add_cookie(cookie)
driver.refresh()
temp = []
time.sleep(10)
while requests.get(url).status_code == 200 and len(temp) <= 1000:
# while True:
    try:
        container = driver.find_elements(By.TAG_NAME,'a')
        links = [c.get_attribute('href') for c in container]
        postlinks = [link for link in links if 'instagram.com/p/' in link]
        # break
        for link in postlinks:
            # for cookie in cookies: 
            #     if isinstance(cookie.get('expiry'), float):
            #         cookie['expiry'] = int(cookie['expiry'])
            #     scraper.add_cookie(cookie)
            scraper.get(link)
            time.sleep(2)
            try:
                userlink =scraper.find_element(By.CLASS_NAME,'_aaqt')
                userlink = userlink.find_element(By.TAG_NAME,'a').get_attribute('href')
                # userlink = userlink.split('/')
                # userlink = f'https://www.instagram.com/{userlink[-2]}/?__a=1&d=1'
                print(userlink)
                # response = requests.get(userlink)
                temp.append(userlink)
            except:
                # open('errorlog.txt','w').write(traceback.print_exc())
                continue
            # scraper.execute_cdp_cmd('Storage.clearDataForOrigin', {
            #     "origin": '*',
            #     "storageTypes": 'all',
            # })

            # scraper.delete_all_cookies()
            time.sleep(2)
        
        driver.execute_script("arguments[0].scrollIntoView();",container[-1])
        print(len(temp))
    except:
        # print(traceback.print_exc())
        # input('pause')
        open('crashlog.text','w').write(requests.get(url).text)
        # break
    response = requests.get(url)
open('job.json','w').write(json.dumps(temp,indent=4))
print('crashed')
driver.quit()
scraper.quit()