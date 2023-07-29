from google.cloud import logging as gc_logging
import pandas as pd
from googlesearch import search, get_tbs
import os, logging

class GCloudConnection:

    def __init__(self, URL, LOG_NAME):
        # env variable declared only for gcloud authentication during local tests. Not necessary at deployed instances
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = './credentials.json'
        logging.getLogger().setLevel(logging.INFO)
        self.connect_cloud_services(LOG_NAME)
        self.URL = URL

    def connect_cloud_services(self, LOG_NAME):
            # connect gcloud logger to default logging.
            logging_client = gc_logging.Client()
            logging_client.get_default_handler()
            logging_client.setup_logging()
            logging_client.logger(LOG_NAME)