from collector import Collector

class Detector:
    """Detector Class is used to determine if Found URLS are malicious"""
    def __init__(self):
        """Sets up class vars"""
        self.ads_list = []

    def get_ads_list(self, query, results_count):
        """This will create a list"""
        c = Collector()
        print(f"c.ads_list: {c.ads_list}")
    
