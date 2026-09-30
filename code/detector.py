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

    def create_proxy_request_items(self):
        """Function to create the pieces of the URL that will be used for the
        proxy request"""

        proxy_entry_base = f"http://customer-{self.proxy_username}:{self.proxy_pass}@pr.oxylabs.io:7777"
        proxies = {'http' :  proxy_entry_base,
                   'https' : proxy_entry_base}

        return proxies

    def send_request_via_proxy(self, URL):
        """Takes in a URL and sends an http request to the URL via residential
        proxy"""

        proxy_urls = self.create_proxy_request_items()
        response = requests.get(URL, proxies=proxy_urls)

        return response
        
    
        
        
            
