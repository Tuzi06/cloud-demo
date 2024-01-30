# The main file that cloud server part code will interact with

from flask import Flask,request
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pymongo

app = Flask(__name__)
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(logging.ERROR)

@app.route('/start')
def init():
    global db,users,posts,pics
    uri = "mongodb+srv://tuzi06:00000000@mydb.uwwvnwd.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri,server_api=ServerApi('1'))
    db = client.data
    users = db['users']
    posts = db['posts']
    pics = db['pics']

    users.drop();posts.drop();pics.drop()
    return 'started'
    

@app.route('/count')
def count():
    return str(len(list(posts.find())))

@app.route('/insert')
def insert():
    data = request.get_json()
    try:
        if data['id'] == 'pics':
            for d in data['data']:
                 db[data['id']].insert_one({'url':d})
            return 'inserted'
        else:
            _id = db[data['id']].insert_one(data['data'])
            return str(_id.inserted_id)
    except pymongo.errors.OperationFailure:
        return 'something in insert is wrong'

@app.route('/download')
def download():
    pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3001)