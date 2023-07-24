from flask import Flask,request
import os,logging,time
from multiprocessing import Process,Pipe

class Scraper:
    def __init__(self,url) -> None:
        self.state = 'idle'
        self.url = url
        self.parent, self.child = Pipe()

    def store(self, df, filename):
        bucket = self.URL  #define url to bucket where results are stored
        url = f"gs://{bucket}/csv/{filename}" if "CLOUD" in os.environ else f"./csv/{filename}"
        df.to_csv(url)
        logging.info(f"{filename} stored succesfully")

    def scrape(self, job):
        # self.child.send("busy") #updates state to stop receiving more jobs
        # try:
        #     df = self.scraper.scrape(job)
        #     self.child.send("idle")
        # except Exception as ex:
        #     self.child.send("scraping-detected")
        #     logging.error(f"Job {job} failed with an error: {ex}")
        #     df = "Failed"
        # return df  # returns the job output, or "Failed" if an error arised
        return 'Failed'


    def run(self, pipe):
        self.child = pipe
        while True:
            job = self.child.recv()
            if job != None:
                logging.info(f"Running job: {job}")
                df = self.scrape(job)
                if str(df) != "Failed":
                    self.store(df, self.scraper.filename(job))
            else:
                time.sleep(3)


app = Flask(__name__)

@app.route('/start')
def start_child_process(): #Gunicorn does not allow the creation of new processes before the app creation, so we need to define this route
    # url = os.getenv("BUCKET")
    url = '127.0.0.1'
    global scraper
    scraper = Scraper(url)
    p = Process(target=scraper.run, args=[scraper.child])
    p.start()
    # logging.info("Scraper running")
    print('scraper running')
    return "Scraper running"

@app.route('/job')
def process_job():
    print(request.args)
    scraper.parent.send(request.args) #sends a job to the Scraper through the "parent" end of the pipe
    return f"Job {request.args} started"

@app.route('/state')
def current_state():
    try:
        if scraper.parent.poll(timeout=3): #checks if there are new messages from the child process
            scraper.state = scraper.parent.recv() # updates the state in such case
        return scraper.state
    except:
        return "not-started"

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)