from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import json,time

def main():
    uri = "mongodb+srv://tuzi06:00000000@mydb.uwwvnwd.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri,server_api=ServerApi('1'))
    db = client.data
    users = db['users']
    posts = db['posts']

    data = []
    ids = users.find({'posts':{'$exists':1}}).distinct('_id')
    print(ids)
    start = time.perf_counter()
    for id in ids:
        user = users.find_one({'_id':id},{'_id':0})
        postIds = user.pop('posts')

        user['posts'] = list(posts.find({'_id':{'$in':postIds}},{'_id':0}))
        data.append(user)
    print(time.perf_counter()-start)

    open('../data/xhs_posts_new.json','w').write(json.dumps(data,ensure_ascii=False,indent=4))

if __name__ == '__main__':
    main()