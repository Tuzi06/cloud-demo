import copy
from selenium.webdriver.common.by import By
from contextlib import contextmanager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located,visibility_of_element_located
from bs4 import BeautifulSoup

init_url = 'https://www.instagram.com/explore'
@contextmanager
def wait_for_page(driver,element,mode = 'show',timeout = 10):
    try:
        if mode == 'show':
            WebDriverWait(driver, timeout).until(visibility_of_element_located((By.CLASS_NAME,element)))
        else:
            WebDriverWait(driver, timeout).until(presence_of_element_located((By.CLASS_NAME,element)))
    except:
        # print('not %s  @ '%mode, element,'  ',driver.current_url)
        return

def findPostContent(soup,content):
    post = soup.find_all('span',class_='x193iq5w xeuugli x1fj9vlw x13faqbe x1vvkbs xt0psk2 x1i0vuye xvs91rp xo1l8bm x5n08af x10wh9bi x1wdrske x8viiok x18hxmgj')
    print(type(post))
    content['text'] = post[0].get_text()

def findComment(soup,content): 
    container = soup.find('div',class_='x78zum5 xdt5ytf x1iyjqo2')
    comments = container.find_all('div',recursive=False)
    res = []
    for comment in comments[1:]:
        if comment.find_all('div',class_='x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh xwib8y2 x1y1aw1k x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s x1q0g3np xqjyukv x6s0dn4 x1oa3qoh x1nhvcw1')!= []:
            replys = comment.find_all('div',class_='x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh xsag5q8 xz9dl7a x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s x1q0g3np xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1')
            res[-1]['reply'] = [{reply.find('div',class_='xt0psk2').get_text():reply.find('div',class_='x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1cy8zhl x1oa3qoh x1nhvcw1').get_text()}for reply in replys]
        else:
            res.append({'comment': {comment.find('div',class_='xt0psk2').get_text():comment.find('div',class_='x9f619 xjbqb8w x78zum5 x168nmei x13lgxp2 x5pf9jr xo71vjh x1uhb9sk x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1cy8zhl x1oa3qoh x1nhvcw1').get_text()},'reply':[]})

    content['comments'] = comments

def findPicture(driver,idx = 0,user = {'id':''}):
    #抓取所有帖子里的图片的链接
    pic = dict()
    try:
        try:
            wait_for_page(driver,'_aao_',2)
            container = driver.find_element(By.CLASS_NAME,'_aao_')#找到图片所在的元素位置
            button = container.find_elements(By.TAG_NAME,'button')
            # print(len(button))
            pictures = []
            while True:
                try:
                    imgs = container.find_elements(By.TAG_NAME,'img')
                    pictures+= [img.get_attribute('src')for img in imgs]
                    button[-1].click()
                except:
                    try:
                        container.find_element(By.TAG_NAME,'video').click()
                        button[-1].click()
                    except:
                        break
            pictures = list(set(pictures))
            # print(pictures)
            for picture in pictures:
                pic['%s-%i.png'%(user['id'],idx)] = picture
                idx += 1 
        except:
            try:
                container.find_element(By.TAG_NAME,'video').click()
            except:
                container = driver.find_element(By.CLASS_NAME,'_aagv')
                temp = container.find_element(By.TAG_NAME,'img')
                pic['%s-%i.png'%(user['id'],idx)] = temp.get_attribute('src')
                idx += 1
        return pic[:5]
       

    except:
        # print('has only video')
        return []
    
    
def run(htmlText,user,pictures):
    soup = BeautifulSoup(htmlText,'html.parser')

    posts=copy.deepcopy(user)
    findPostContent(soup,posts)
    findComment(soup,posts)
    posts['pic'] = pictures
    return posts