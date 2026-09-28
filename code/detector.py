from collector import Collector

class Detector:
    """Detector Class is used to determine if Found URLS are malicious"""
    def __init__(self):
        """Sets up class vars"""
        self.ads_list = []

    def get_ads_list(self, query, results_count):
        """This will create a Collector object and pull grab the returned ads"""
        c = Collector()
        c.pull_ads_in_bulk(query, results_count)
        self.ads_list = c.ads_list
        print(f"self.ads_list: {self.ads_list}")

    def request_ad_link_via_proxy(self, URL):
        """This will sumbit an ad url via proxy and return the resulting page"""
        
            
