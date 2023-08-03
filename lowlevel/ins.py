from selenium.webdriver.common.by import By
from contextlib import contextmanager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located,visibility_of_element_located
import time,traceback,json,random

init_url = 'https://www.instagram.com/explore'
cn = 5 #每条帖子所抓取的评论量
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

def getUser(driver):
    wait_for_page(driver,'x1qjc9v5')
    user = dict() #用于存储信息的组建，使用dict以便后续写入json文档中
    try:
        user['id'] = driver.find_element(By.TAG_NAME,'h2').text
    except:
        user['id'] = driver.find_element(By.TAG_NAME,'h1').text
    userBlock = driver.find_element(By.CLASS_NAME,'x7a106z')
    user['user-name'] = userBlock.find_element(By.XPATH,'div[1]/span').text
    user['follow'] = driver.find_elements(By.CLASS_NAME,'_ac2a')[1].text.lower()
    try:
        user['user-info'] =userBlock.find_element(By.TAG_NAME,'h1').text
    except:
        user['user-info'] = ''
    try:
        user['user-sex'] = driver.find_element(By.CLASS_NAME,'gender').find_element(By.TAG_NAME,'use').get_attribute('xlink:href')[1:]
    except:
        user['user-sex'] = ''
    try:
        user['user-tag'] = userBlock.find_element(By.XPATH,'div[2]/div').text
    except:
        user['user-tag'] = []
    user['user-link'] = driver.current_url
    return user

def getLinks(driver):
    chartoken = ['%0d','%2e','%09','%20',' ']
    wait_for_page(driver,'_aabd')
    contentBlock = driver.find_element(By.CLASS_NAME,'x9f619')
    contents = contentBlock.find_elements(By.CLASS_NAME,'_aabd')
    links = [content.find_element(By.TAG_NAME,'a').get_attribute('href') + random.choice(chartoken) for content in contents]
    return links

def findPostContent(driver,content):
    try:
        wait_for_page(driver,'x4h1yfo')
        block = driver.find_element(By.CLASS_NAME,'x4h1yfo')
        nr = block.find_element(By.TAG_NAME,'h1')
        text = nr.text
        tags = nr.find_elements(By.TAG_NAME,'a')
        tags = [tag.text for tag in tags]
        tags = list(filter(lambda tag: tag[0] == '#',tags))
        text = text.split(' ')
        text = ' '.join(filter(lambda word: word not in tags, text))
        content['text'] = text
        content['tags'] = tags
    except:
        # print(traceback.print_exc())
        content['text'] = ''


def findComment(driver,content): 
    comments = []
    try:
        container = dict()
        temps = driver.find_elements(By.CLASS_NAME,'_a9ym')
        comment = []
        for temp in temps[:5]:
            com = dict()
            spans = temp.find_elements(By.TAG_NAME,'span')
            if spans[0].text != '':
                com['comment'] = spans[0].text
            else:
                com['comment'] = spans[1].text
            try:
                temp.find_element(By.CLASS_NAME,'_a9yo').click()
                time.sleep(1)
                reply = temp.find_elements(By.CLASS_NAME,'_a9zs')[:cn]
                reply = [r.find_element(By.TAG_NAME,'span').text for r in reply]
                com['reply'] = reply
                comment.append(com)
            except:
                comment.append(com)

        container['comments'] = comment
        # print(container['comments'])
        comments.append(container)
    except:
        print(traceback.print_exc())
        # input('f')
    # print(comments)
    content['comments'] = comments

def findPicture(driver,content = {},idx = 0,user = {'id':''}):
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
        content['picture'] = pic
        return idx

    except:
        # print('has only video')
        content['picture'] = {}
        return idx
    
def grabing(driver,link,user,detail_text,catigory,idx):
    driver.get(link)
    wait_for_page(driver,'_aagv')
    #包装帖子内容，为后续写入json做准备
    postInfo = dict()
    postInfo['user-id'] = user['id']
    postInfo['user-name'] = user['user-name']
    postInfo['user-info'] = user['user-info']
    postInfo['user-sex'] = user['user-sex']
    postInfo['user-tag'] = user['user-tag']
    postInfo['user-link'] = user['user-link']

    post = dict()
    post['catigory'] = catigory
    idx= findPicture(driver,post,idx,user)
    if len(post['picture']) ==0:
        return idx
    findPostContent(driver,post)
    findComment(driver,post)
    postInfo['post'] = post

    if len(post['picture']) ==0:
        return idx
    detail_text.append(postInfo)
    postInfo['link'] = link
    return idx

def run(driver,links,detail_text,user,catigory,average):
    idx = 0
    random.shuffle(links)
    for link in links:
        try:
            grabing(driver,link,user,detail_text,catigory,idx)
            # average = 2
        except:
            print('fail grabing @ ',link)
        time.sleep(random.uniform(0,average))

    # savePicture(driver,user,photos,'ins')