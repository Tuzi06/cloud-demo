import copy,json,requests,traceback,random

def getUser(soup):
    user = dict() #用于存储信息的组建，使用dict以便后续写入json文档中
    user['id'] = soup.find('span',class_='user-redId').text.split('：')[1]
    user['name'] = soup.find('div',class_ = 'user-name').text
    user['follow'] = soup.findAll('span',class_='count')[1].text
    user['like'] = soup.findAll('span',class_='count')[2].text
    user['info'] = soup.find('div',class_='user-desc').text if soup.find('div',class_='user-desc')!=None else ''
    try: user['sex'] = str(soup.find('div',class_='gender').find('use')['xlink:href'][1:])
    except: user['sex'] = ''
    user['tag'] = [tag.text for tag in soup.findAll('div',class_='tag-item')]
    return user

def findNoteContent(soup,content):
    content['title'] = soup.find('div',{'id':'detail-title'}).text if soup.find('div',{'id':'detail-title'})!= None else ''
    text = soup.find('div',{'id':'detail-desc'})
    content['text'] = text.find('span').text
    content['tag'] = [tag.text[1:] for tag in soup.findAll('a',class_='tag tag-search')]

def findComment(data,content):
    comments = []
    for d in data:
        comment = {d['user_info']['nickname']:d['content']}
        if d['sub_comment_count'] != '0':
            r = dict()
            replys = d['sub_comments']
            for reply in replys:
                r[reply['user_info']['nickname']] = reply['content']
            comment['replys'] = r
        comments.append(comment)
    
    content['comments'] = comments 
    
def findPicture(soup,content,idx,id):
    try:
        data = json.loads(soup.findAll('script')[-1].text.split('=')[1].replace('undefined','null')) 
        picUrls = data['note']['noteDetailMap'][data['note']['firstNoteId']]['note']['imageList']
       
        content['pictures'] = {}
        for url in picUrls:
            content['pictures'][f"{id}-{idx}"] = url['infoList'][1]['url']
            idx+=1
    except:
        url = soup.find('div',class_='render-ssr-image player-container')['style'].split('(')[1][:-1]
        content['pictures'] = {f"{id}-{idx}":url}
    return idx


def grabing(soup,self,user,idx):
    post = dict()
    findNoteContent(soup,post)
    noteId = soup.find('meta',{'name':'og:url'})['content'].split('/')[-1]
    url = 'https://edith.xiaohongshu.com/api/sns/web/v2/comment/page?note_id='+noteId+'&cursor=&top_comment_id=&image_formats=jpg,webp,avif'
    header = copy.deepcopy(self.headers['htmlHeaders'])
    header['Cookie'] = random.choice(self.cookies)
    response= requests.get(url,headers = header)
    # print(response.json())
    try:
        commentData = response.json()['data']['comments']
    except:
        commentData = []
    findComment(commentData,post)
    idx = findPicture(soup,post,idx,user['id'])
    return idx,post