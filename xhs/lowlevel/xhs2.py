import copy,time,sys
from selenium. webdriver.common.by import By
from selenium.webdriver import Chrome,ChromeOptions
from selenium.webdriver.chrome.service import Service
from contextlib import contextmanager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located,visibility_of_element_located

url = 'https://www.xiaohongshu.com/explore'
def prepare_driver(cookies,workers,headless = True):
    drivers = []
    options =ChromeOptions()
    options.add_argument('disable-blink-features=AutomationControlled')
    
    if sys.platform == 'linux':
        service = Service(executable_path= '/usr/bin/chromedriver.exe')
    elif sys.platform == 'darwin':
        service = Service(executable_path='lowlevel/chromedriver-mac-arm64/chromedriver')
    if headless:
        options.add_argument('headless')
    for _ in range(workers):
        driver = Chrome(options = options,service=service)
        driver.get('https://www.xiaohongshu.com/explore')
        for cookie in cookies: 
            if isinstance(cookie.get('expiry'),float):
                cookie['expiry'] = int(cookie['expiry'])
            driver.add_cookie(cookie)
        driver.refresh()
        drivers.append(driver)
    return drivers

@contextmanager
def wait_for_page(driver,element,mode = 'show',timeout = 5):
    try:
        if mode == 'show':
            WebDriverWait(driver, timeout).until(visibility_of_element_located((By.CLASS_NAME,element)))
        else:
            WebDriverWait(driver, timeout).until(presence_of_element_located((By.CLASS_NAME,element)))
    except:
        return

def getUser(soup):
    user = dict() #用于存储信息的组建，使用dict以便后续写入json文档中
    user['user-id'] = soup.find('span',class_='user-redId').text.split('：')[1]
    user['user-name'] = soup.find('div',class_ = 'user-name').text
    user['follow'] = soup.findAll('span',class_='count')[1].text
    user['user-info'] = soup.find('div',class_='user-desc').text or ''
    user['user-sex'] = str(soup.find('div',class_='gender').find('use')['xlink:href'][1:]) or ''
    user['user-tag'] = [tag.text for tag in soup.findAll('div',class_='tag_item')]
    return user

def findNoteContent(soup,content):
    content['title'] = soup.find('div',{'id':'detail-title'}).text or ''
    content['text'] = soup.find('div',{'id':'detail-desc'}).text 
    content['tag'] = [tag.text for tag in soup.findAll('span',class_='tag')]

def findComment(soup,content):
    if soup.find('span','chat-wrapper').text == '0':
        content['comments'] = []
        return
    container = soup.find('div',class_='list-container')
    commentList = container.findAll('div',class_='comment-item',recursive=False) 
    comments = []
    for commentItem in commentList:
        comment = dict()
        comment['comment'] = {commentItem.find('div',class_='author').text : commentItem.find('div',class_='content').text}
        if commentItem.find('div',class_='reply-container'):
            comment['replys'] = [{replyItem.find('div',class_='author').text : replyItem.find('div',class_='content').text} for replyItem in commentItem.find('div',class_='reply-container').findAll('div',class_='comment-item')]
        comments.append(comment)
    content['comments'] = comments[:5]
    
def findPicture(soup,content,idx):
    try:
        pics = soup.find('div',class_='swiper-wrapper').findAll('div')
    except:
        pics = [soup.find('xg-poster')]
    photoUrls = []
    for pic in pics:
        photoUrls.append({f"{content['user-id']}-{idx}":pic['style'].split('"')[1].replace('&quot','')})
        idx += 1
    content['post']['pictures'] = photoUrls
    return idx
        
def grabing(soup,user,idx):
    post = copy.deepcopy(user)
    post['post'] = dict()
    findNoteContent(soup,post['post'])
    findComment(soup,post['post'])
    idx = findPicture(soup,post,idx)
    return idx,post