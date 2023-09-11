import json
import time
from bs4 import BeautifulSoup as bs

from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
from selenium. webdriver.common.by import By
from contextlib import contextmanager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located,visibility_of_element_located
import pickle

posts = json.load(open('result.json','r'))
posts = [post['url'] for post in posts if post['post']['tag'] == []]
print(len(posts))
@contextmanager
def wait_for_page(driver,element,mode = 'show',timeout = 5):
    try:
        if mode == 'show':
            WebDriverWait(driver, timeout).until(visibility_of_element_located((By.CLASS_NAME,element)))
        else:
            WebDriverWait(driver, timeout).until(presence_of_element_located((By.CLASS_NAME,element)))
    except:
        return
    
def progressBar(iterable, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iterable    - Required  : iterable object (Iterable)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function
    def printProgressBar (iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()

service = Service(executable_path='xhs/lowlevel/chromedriver-mac-arm64/chromedriver')
options =ChromeOptions()
options.add_argument('disable-blink-features=AutomationControlled')
driver = Chrome(options = options,service=service)
count = 0 
problem = []
for post in progressBar(posts, prefix = 'Progress:', suffix = 'Complete', length = 50):
    driver.get(post)
    wait_for_page(driver,'tag-search')
    soup = bs(driver.page_source,'html.parser')
    if  [tag.text[1:] for tag in soup.findAll('a',class_='tag-search tag')] != []:
       problem.append(post)
       count+=1
    

print(f"\n{count}")
print(len(problem))
open('problem.json','w').write(json.dumps(problem,indent=4))

driver.quit()