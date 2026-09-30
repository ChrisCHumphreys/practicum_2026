from collector import Collector
from dotenv import dotenv_values

class Detector:
    """Detector Class is used to determine if Found URLS are malicious"""
    def __init__(self):
        """Sets up class vars"""
        self.ads_list = []
        self.creds = dotenv_values('.env')
        self.proxy_username = self.creds['OXY_PROXY_USERNAME']
        self.proxy_pass = self.creds['OXY_PROXY_PASS']
        
    def get_ads_list(self, query, results_count):
        """This will create a Collector object and pull grab the returned ads"""
        c = Collector()
        c.pull_ads_in_bulk(query, results_count)
        self.ads_list = c.ads_list
        print(f"self.ads_list: {self.ads_list}")

    def create_proxy_request_base(self, URL):
        """Function to create the URL that will be used for the proxy request"""
        
        
        
            
