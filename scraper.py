from flask import Flask,request,jsonify
import os,logging,time,pickle,queue,requests,json 
from multiprocessing import Process,Pipe
from lowlevel import main
class Scraper:
    def __init__(self,url,reqNum) -> None:
        self.state = 'idle'
        self.url = url
        self.parent, self.child = Pipe()
        self.posts = []
        self.reqNum = reqNum
        try:
            self.cookies = pickle.load(open('./lowlevel/xhs_cookies.pkl','rb'))
        except:
            self.cookies = main.init()
            pickle.dump(self.cookies,open('./lowlevel/xhs_cookies.pkl','wb'))
        self.finders = main.prepare_driver(self.cookies,1)
        self.workers = main.prepare_driver([],1)
    
    def store(self, df, filename):
        bucket = self.URL  #define url to bucket where results are stored
        url = f"gs://{bucket}/csv/{filename}" if "CLOUD" in os.environ else f"./csv/{filename}"
        df.to_csv(url)
        logging.info(f"{filename} stored succesfully")

    def run(self, pipe):
        self.child = pipe
        while len(self.posts)<self.reqNum:
            job = self.child.recv()
            if job != None:
                self.child.send('busy')
                link,_ = job.values()
                if requests.get(link).status_code == 200:
                    # self.child.send("scraping-detected")
                    # print('scraper detected by the server needs restart')
                    # for driver in self.finders + self.workers:
                    #     driver.quit()
                    postInfos = main.Finder(self.finders[0],link) #{userinfo, list of post links}
                    if postInfos:
                        main.Worker(self.workers[0],postInfos,self.posts)
            
            self.child.send('idle')    
        
        self.child.send('done')
        open('res.json','w').write(json.dumps(self.posts,ensure_ascii= False,indent=4))

app = Flask(__name__)

@app.route('/start')
def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route
    url = os.getenv("BUCKET")
    # url = '192.168.64.128'
    global scraper
    scraper = Scraper(url,100)
    p = Process(target=scraper.run, args=[scraper.child])
    p.start()
    # logging.info("Scraper running")
    print('scraper running')
    return "Scraper running"

@app.route('/job')
def process_job():
    scraper.parent.send('scraping-detected') #sends a job to the Scraper through the "parent" end of the pipe
    
@app.route('/download')
def store_posts():
    
    return jsonify(result = scraper.posts)

@app.route('/reset')
def reset_post():
    scraper.posts = []

@app.route('/state')
def current_state():
    try:
        if scraper.parent.poll(timeout=3): #checks if there are new messages from the child process
            scraper.state = scraper.parent.recv() # updates the state in such case
        return scraper.state
    except:
        return "not-started"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)