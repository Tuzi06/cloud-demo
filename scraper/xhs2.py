from selenium. webdriver.common.by import By
from contextlib import contextmanager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import presence_of_element_located,visibility_of_element_located
import traceback,time,random,json

init_url = 'https://www.xiaohongshu.com/explore'
cn = 5 #每条帖子所抓取的评论量

@contextmanager
def wait_for_page(driver,element,mode = 'show',timeout = 5):
    try:
        if mode == 'show':
            WebDriverWait(driver, timeout).until(visibility_of_element_located((By.CLASS_NAME,element)))
        else:
            WebDriverWait(driver, timeout).until(presence_of_element_located((By.CLASS_NAME,element)))
    except:
        # print('not %s  @ '%mode, element,'  ',driver.current_url)
        return

def getUser(driver,usertag = []):
    wait_for_page(driver,'user-info')
    user = dict() #用于存储信息的组建，使用dict以便后续写入json文档中
    user['user-id'] = driver.find_element(By.CLASS_NAME,'user-redId').text.split('：')[1]
    user['user-name'] = driver.find_element(By.CLASS_NAME,'user-name').text
    user['follow'] = (driver.find_element(By.CLASS_NAME,'user-interactions').find_elements(By.CLASS_NAME,'count')[1]).text
    try:
        user['user-info'] = driver.find_element(By.CLASS_NAME,'user-desc').text
    except:
        user['user-info'] = ''
    try:
        user['user-sex'] = driver.find_element(By.CLASS_NAME,'gender').find_element(By.TAG_NAME,'use').get_attribute('xlink:href')[1:]
    except:
        user['user-sex'] = ''
    try:
        user['user-tag'] = [e.text for e in driver.find_elements(By.CLASS_NAME,'tag-item') if e.text != '']
    except:
        user['user-tag'] = []
    usertag += user['user-tag']
    return user

def getLinks(driver):
    #因为小红书的所有帖子都是网页链接的形式存储在相应组建的style属性中，所以这里通过提取style属性中的信息的方式得到所需的网页链接
    try:
        a = driver.find_element(By.CLASS_NAME,'feeds-container')
        sections = a.find_elements(By.TAG_NAME,'section')
    except:
        print('!!!')
    links = [] #用于存储网页链接的数组
    for section in sections:
        l = section.find_elements(By.TAG_NAME,'a')
        links.append(l[1].get_attribute('href'))
    # print([link if 'expolore' in link else '' for link in links])
    return links

def findNoteContent(driver,content,tagCollector = []):
    note_content = driver.find_element(By.CLASS_NAME,'note-content')#找到存储帖子信息的元素
    try:
        content['title'] = note_content.find_element(By.CLASS_NAME,'title').text
    except:
        content['title'] =''
    desc = note_content.find_elements(By.CLASS_NAME,'desc')
    content['text'] = desc[0].text
    # tags = desc[1].find_elements(By.TAG_NAME,'span')
    # content['tag'] = [tag.text for tag in tags]
    try:
        tags = desc[1].text.split('#')
        content['tag'] = [tag for tag in tags if tag]
        tagCollector += content['tag']
        # print(content['tag'])
    except:
        content['tag'] = []

def findComment(driver,content): 
    #如果没有加载出来则刷新页面
    wait_for_page(driver,'count')
    comments = []
    try:
        if driver.find_elements(By.CLASS_NAME,'count')[-1].text == '0':
            driver.find_element(By.CLASS_NAME,'no-comments')
        else:
            raise ValueError('post has comment')
    except:   
        if len(driver.find_elements(By.CLASS_NAME,'comment-item'))<1:
            driver.refresh()
        wait_for_page(driver,'list-container')             
        #抓取评论及回复
        comment_container = driver.find_element(By.CLASS_NAME,'list-container')
        for i in range(cn):
            comment = dict()
            try:
                #单个评论及其所有的回复
                comment_item = comment_container.find_element(By.XPATH,'div[%i]'%i)
                                                          
            except:
                # print('wrong when find comment')
                # print(traceback.print_exc())
                # input('pause')
                continue
            #因为只有每个评论是由一条评论及n条回复组成，所以我们这里评论选取数组的第一项
            contents= comment_item.find_elements(By.CLASS_NAME,'content')
            comment['comment'] = contents[0].text
            replys = contents[1:] #分离回复
            #提取回复（如果有）
            if len(replys)>0:
                replys = [reply.text for reply in replys]
                for j in range(len(replys)):
                    #清理回复（如果有回复特定评论的话，回复语句会为（回复xxxx：balabala））
                    if '回复' in replys[j]:
                        temp = replys[j].split(':')
                        replys[j] = ''.join(temp[1:])

                comment['reply'] = replys
            comments.append(comment)

    content['comments'] = comments
    
def findPicture(driver,content,photos,idx,user):
    #抓取所有帖子里的图片的链接
    # wait_for_page(driver,'swiper-wrapper')
    container = driver.find_element(By.CLASS_NAME,'swiper-wrapper')#找到图片所在的元素位置
    buffers = container.find_elements(By.TAG_NAME,'div')[1:8]#找到所有有图片的元素
    pic = []
    #提取图片链接
    for buffer in buffers:
        picture = buffer.get_attribute('style')
        picture = picture.split('"')[1]
        photos.append(picture)
        pic.append('%s-%i.png'%(user['user-id'],idx))
        idx+=1
    content['picture'] =pic
    return idx

def grabing(driver,link,user,idx,photos,detail_text):
    driver.get(link)
    if ' https://www.xiaohongshu.com/website-login/error?redirectPath=' in str(driver.current_url):
        driver.get(link)

    postInfo = dict()
    post = dict()

    #检查网页是否有视频
    wait_for_page(driver,'media-container')

    if len(driver.find_elements(By.CLASS_NAME,'swiper-wrapper')) == 0:
        return idx

    # if len(driver.find_elements(By.CLASS_NAME,'swiper-wrapper')) == 0:
    #     postInfo['video'] = True
    #     # return idx
    # else:
    #     postInfo['video'] = False
    #     idx= findPicture(driver,post,photos,idx,user)

    #包装帖子内容，为后续写入json做准备
    postInfo['user-id'] = user['user-id']
    content = dict()
    content['user-name'] = user['user-name']
    content['user-info'] = user['user-info']
    content['user-sex'] = user['user-sex']
    content['user-tag'] = user['user-tag']

    idx= findPicture(driver,post,photos,idx,user)
    findNoteContent(driver,post)
    findComment(driver,post)
    content['post'] = post

    postInfo['content'] = content
    detail_text.append(postInfo)

    content['link'] = link
    return idx

# def savePicture(driver,user,photos,ds):
#     # 保存所有图片
#     for i in range(len(photos)):
#         url = photos[i]
#         driver.get(url)
#         time.sleep(1)
#         # driver.save_screenshot('out/%s/photo/%s-%i.png'%(ds,user['id'],i))

# def saveContent(detail_text,mode,filename = 'out/text_data.json'):
#     #将帖子及博主信息等文本写入json
#     with open(filename,mode) as file:
#         data = dict()
#         data['data'] = detail_text
#         Data = json.dumps(data,ensure_ascii=False,indent = 4)
#         file.write(Data)

def run(driver,links,detail_text,user):
    photos = []
    try:
        idx =0 # 图片的计数器
        for link in links:
            try:
                # input('pause')
                idx = grabing(driver,link,user,idx,photos,detail_text)
            except:
                print('fail to grab @',driver.current_url)
                # print(traceback.print_exc())
                continue
        # time.sleep(30)
        # savePicture(driver,user,photos,'xhs')
    except:
        print('fail to run @ ', user)
        # print(traceback.print_exc())