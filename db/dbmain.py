# The main file that cloud server part code will interact with

from concurrent.futures import thread

from flask import Flask,request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo,time,multiprocessing


app = Flask(__name__)
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

@app.route('/start')
def init():
    global db,posts,users
    uri = "mongodb+srv://tuzi06:00000000@mydb.uwwvnwd.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri,server_api=ServerApi('1'))
    db = client.data
    users = db['users']
    posts = db['posts']

    users.drop();posts.drop()
    return 'started'

@app.route('/state')
def state():
    try:
        posts.find_one()
        return 'started'
    except:
        return 'cold'

@app.route('/count')
def count():
    return str(posts.count_documents({}))

@app.route('/checkExist')
def checkExist():
    ids= request.get_json()['data']
    # res = []
    # for id in ids:
    #     if list(users.find({'longID':id.split('/')[-1]})) == []:
    #         res.append(id)
    # return res
    return [id for id in ids if list(users.aggregate([{'$match':{'longID':id.split('/')[-1]}},{'$project':{'_id':1}}]))==[]]

@app.route('/addlog',methods = ['POST']) 
def add():
    data = request.get_json()['data']
    # with pymongo.timeout(5.0):
    try:
        users.insert_many([{'longID':d} for d in data])
        return ''
    except pymongo.errors.OperationFailure:
        return 'something in insert is wrong'

@app.route('/insert',methods = ['POST']) 
def insert():
    res = request.get_json()
    data = res['data']
    # with pymongo.timeout(5.0):
    try:
        if res['id']=='posts':
            return [str(id) for id in posts.insert_many(data).inserted_ids]
        elif res['id']=='users':
            longID = data.pop('longID')
            users.replace_one({'longID':longID},data)
            return []
    except pymongo.errors.OperationFailure:
        return []

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3001,threaded = True)