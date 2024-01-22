from lowlevel.scraper import prepare_driver
import time
from selenium.webdriver.common.by import By
import multiprocessing as mp
mp.set_start_method('spawn')

def linkProcess(d1,postPool):
    while True:
        try:
            time.sleep(1)
            continue
            if postPool.qsize()>=5:
                time.sleep(10)
                continue
            joblist = d1.find_elements(By.CLASS_NAME,'jobTitle')
            for job in joblist:
                low = job.text.lower()
                title = low.split(' ')
                if 'developer'in title:
                    url = job.find_element(By.TAG_NAME,'a')
                    postPool.put(url.get_attribute('href'))
            nextPage = d1.find_elements(By.CLASS_NAME,'css-227srf')
            nextPage = nextPage[-1].find_element(By.TAG_NAME,'a')
            link = nextPage.get_attribute('href')
    
            d1.get(link)
        except:
            continue

def postProcess(d2,postPool):
    aws = 0
    azure = 0
    gcd =0 
    cloud =0
    total = 0
    while True:
        try:
            if postPool.empty():
                time.sleep(2)
                continue
            post,dump = postPool.get().values()
            d2.get(post)
            time.sleep(2)

            text = d2.find_element(By.CLASS_NAME,'jobsearch-jobDescriptionText').text.lower()
            text = text.replace('\n',' ').split(' ')
            if 'aws' in text or 'amazon' in text:
                aws += 1
            if 'azure' in text:
                azure += 1
            if 'google' in text or 'gcd' in text:
                gcd +=1
            if 'cloud' in text:
                cloud += 1 

            print(f"\r aws:{aws} ,azure:{azure} ,google cloud:{gcd}, cloud:{cloud}, total: {total}", end = '\r')
        except:
            continue

if __name__ == '__main__':
    d1 = prepare_driver([],1,False)[0]
    d2 = prepare_driver([],1,False)[0]

    d1.get('https://ca.indeed.com/jobs?q=software+developer&l=Burnaby%2C+BC&radius=50&vjk=e762bd931b70c7e8')
    time.sleep(2)
    postPool = mp.Queue()

    a = mp.Process(target=linkProcess,args = [d1,postPool])
    a.start()
    b = mp.Process(target=postProcess,args = [d2,postPool])
    b.start()