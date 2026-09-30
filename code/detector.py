from collector import Collector
from dotenv import dotenv_values

# Used the requests library docs a lot for this
# https://docs.python-requests.org/en/latest/user/advanced/
# Learned aobut the url requests unqute option on stack overflow
# https://stackoverflow.com/questions/16566069/url-decode-utf-8-in-python

class Detector:
    """Detector Class is used to determine if Found URLS are malicious"""
    def __init__(self):
        """Sets up class vars"""
        self.ads_list = []
        self.creds = dotenv_values('.env')
        self.proxy_username = self.creds['OXY_PROXY_USERNAME']
        self.proxy_pass = self.creds['OXY_PROXY_PASS']
        self.final_ad_pages = []
        
    def get_ads_list(self, query, results_count):
        """This will create a Collector object and pull grab the returned ads"""
        c = Collector()
        c.pull_ads_in_bulk(query, results_count)

        # print(c.ads_list)
        
        for item in c.ads_list:
            if item != "No Ads Returned":
                for ad in item:
                    self.ads_list.append(ad["data_rw"])
        
        # self.ads_list = c.ads_list
        # print(f"self.ads_list: {self.ads_list}")

    def create_proxy_request_items(self):
        """Function to create the pieces of the URL that will be used for the
        proxy request"""

        proxy_entry_base = f"http://customer-{self.proxy_username}-cc-US-city-miami:{self.proxy_pass}@pr.oxylabs.io:7777"
        proxies = {'http' :  proxy_entry_base,
                   'https' : proxy_entry_base}

        return proxies

    def send_request_via_proxy(self, URL):
        """Takes in a URL and sends an http request to the URL via residential
        proxy"""

        # I am trying here to match the headers of a normal browser
        # these were mostly just copy and pasted from my firefox browser
        # I got the user-agent from https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36'
        }

        proxy_urls = self.create_proxy_request_items()
        response = requests.get(URL, headers=headers, proxies=proxy_urls, timeout=5)

        return response

    def grab_content_from_ads_list(self):
        """Loops through the ads_list and pulls the resulting webpage from
        each, then updates the final_ad_pages list"""
        
        for ad in self.ads_list:
            if (ad != "No Ads Returned"):
                self.final_ad_pages.append(
                    self.get_data_from_url_response(ad)
                )

    def get_data_from_url_response(self, URL):
        """Returns a dict with useful items from the proxy response"""
        # For reference if I need to add fields later
        # https://docs.python-requests.org/en/latest/api/#requests.Response

        response = self.send_request_via_proxy(URL)

        ad_response_info = {}

        ad_response_info["OriginalURL"] = URL
        ad_response_info["ResponseHeaders"] = response.headers
        ad_response_info["RequestHeaders"] = response.request.headers
        ad_response_info["RedirectURL"] = response.history[-1].url
        ad_response_info["FinalURL"] = response.url
        ad_response_info["Text"] = response.text

        # note if the urls match - Need to URL decode the original
        if ad_response_info["FinalURL"] not in requests.utils.unquote(ad_response_info["OriginalURL"]):
            ad_response_info["URLSMatch"] = False
        else:
            ad_response_info["URLSMatch"] = True        

        return ad_response_info
   
    def test_function(self):
        """Just a function to save time for myself in testing"""

        # URL1 = "https://ip.oxylabs.io/location"
        # URL2 = "https://www.showmyip.com"
        
        # ad_page = self.get_data_from_url_response(URL2)

        # for key, value in ad_page.items():
        #     print(f"Key: {key}\t\t\tValue: {value}")

        # first I need to build the list
        self.get_ads_list("Samsung Galaxy S24 specs", 10)
        # then I need to pull a response from each item
        self.grab_content_from_ads_list()
        # then print the results
        for item in self.final_ad_pages:
            print(f"Match: {item['URLSMatch']}")
            print(f"\tOriginal: {item['OriginalURL']}")
            print(f"\tFinal: {item['FinalURL']}")
