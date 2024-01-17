# The main file that cloud server part code will interact with

from flask import Flask,request
import pymongo

app = Flask(__name__)

@app.route('/start')
def init():
    global db,users,posts,pics
    client = pymongo.MongoClient('mongodb+srv://tuzi06:tuzi1234@mydb.onb0ne9.mongodb.net/')
    db = client.xhsData
    users = db['users']
    posts = db['posts']
    pics = db['pics']
    

@app.route('/count')
def count():
    return str(len(list(posts.find())))

@app.route('/insert')
def insert():
    data = request.get_json()
    try:
        res = db[data['id']].insert_one(data['data'])
        return res.inserted_id
    except pymongo.errors.OperationFailure:
        return 'something in insert is wrong'

@app.route('/download')
def download():
    pass

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3001)