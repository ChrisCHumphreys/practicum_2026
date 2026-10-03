from collector import Collector
from dotenv import dotenv_values
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import re
import pickle

# Used the requests library docs a lot for this
# https://docs.python-requests.org/en/latest/user/advanced/
# Learned aobut the url requests unqute option on stack overflow
# https://stackoverflow.com/questions/16566069/url-decode-utf-8-in-python
# Most of the threading stuff I am copying from the work I did in the
# collector modules, so most of that research and sources applies here as well
# used the python3 docs to help with writing the regular expression to pull
# the domains
# https://docs.python.org/3/library/re.html

class Detector:
    """Detector Class is used to detect the actual ad pages after the collector
    collects the ads"""
    def __init__(self):
        """Sets up class vars"""
        self.ads_list = []
        self.creds = dotenv_values('.env')
        self.proxy_username = self.creds['OXY_PROXY_USERNAME']
        self.proxy_pass = self.creds['OXY_PROXY_PASS']
        self.final_ad_pages = []
        self.lock = threading.Lock()
        self.max_thread_count = 50
        
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

        with ThreadPoolExecutor(self.max_thread_count) as executor:
            # Ok, so the real only limit is gonna be what my computer can handle
            # so I think Im gonna leave max_thread_count at 50 and use that
            # as the number of threads to fire.

            futures = []
            for ad in self.ads_list:
                futures.append(executor.submit(
                    self.get_data_from_url_response, ad))

            # below taken largely from python docs
            # https://docs.python.org/3/library/concurrent.futures.html
            for thread in futures:
                try:
                    thread.result()
                except Exception as e:
                    print(f"Exception {e}")
                          
        # Everything Below here was working before making multi threaded
        # for ad in self.ads_list: 
        #     if (ad != "No Ads Returned"):
        #         response = self.get_data_from_url_response(ad)
        #         with self.lock:
        #             self.final_ad_pages.append(
        #                 response
        #            )

    def get_data_from_url_response(self, URL):
        """Appends a dict with useful items from the proxy response to the
           final_ad_pages list"""
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
        ad_response_info["Domain"] = re.findall(r'^http[s]?://([^/\s]*)', response.url)[0]
        ad_response_info["DomainIsMalicious"] = False

        # note if the urls match - Need to URL decode the original
        if ad_response_info["FinalURL"] not in requests.utils.unquote(ad_response_info["OriginalURL"]):
            ad_response_info["URLSMatch"] = False
        else:
            ad_response_info["URLSMatch"] = True        

        with self.lock:
            self.final_ad_pages.append(ad_response_info)
        # return ad_response_info
   
    def test_function(self):
        """Just a function to save time for myself in testing"""

        # URL1 = "https://ip.oxylabs.io/location"
        # URL2 = "https://www.showmyip.com"
        
        # ad_page = self.get_data_from_url_response(URL2)

        # for key, value in ad_page.items():
        #     print(f"Key: {key}\t\t\tValue: {value}")

        # first I need to build the list
        self.get_ads_list("2026 Best SUV", 10)
        # then I need to pull a response from each item
        self.grab_content_from_ads_list()
        # then print the results
        for item in self.final_ad_pages:
            print(f"\tOriginal: {item['FinalURL']}")
            print(f"\tDomain: {item['Domain']}")

        # Creating a file so I can test the Classifier wihtout using up all my
        # api calls, since I am saving objects, looks like I need to 'pickle'.
        # Going to use that, got info from python docs
        # https://docs.python.org/3/library/pickle.html#examples
        with open("./output/sample_final_ad_list.pickle", "wb") as sample_file:
            pickle.dump(self.final_ad_pages, sample_file, pickle.HIGHEST_PROTOCOL)


class Classifier:
    """Takes over the attempted classification of ads once they have been
    detected by the Detector class"""

    def __init__(self):
        self.sample_final_ad_pages = []

    def build_final_page_list_from_pickle(self):
        """For testing I am pickling the ad list so I dont have to re-run it
        each time. This is how I rebuild the list from that pickle"""

        with open("./output/sample_final_ad_list.pickle", "rb") as pickle_file:
            self.sample_final_ad_pages = pickle.load(pickle_file)
        

    def build_malicious_domain_list(self):
        """Makes a copy of the malicious domain list from github so that I don't
        have to re-pull all the time. This writes a file to disk that I can
        compare against and then only occassionally update"""

        # Malicious Domains below from https://github.com/romainmarcoux/malicious-domains
        url1 = "https://raw.githubusercontent.com/romainmarcoux/malicious-domains/refs/heads/main/full-domains-aa.txt"
        url2 = "https://raw.githubusercontent.com/romainmarcoux/malicious-domains/refs/heads/main/full-domains-ab.txt"
        url3 = "https://raw.githubusercontent.com/romainmarcoux/malicious-domains/refs/heads/main/full-domains-ac.txt"
        with open("./indicators/domains.txt", 'w') as domain_file:
            domain_file.write(requests.get(url1).text)
            domain_file.write(requests.get(url2).text)
            domain_file.write(requests.get(url3).text)

    def mark_malicious_domains_in_ads_list(self, detector_ad_list):
        """Accepts a 'final_ad_pages' list from a detector object and searches
        the known malicious domains list to identify any matches"""

        # open the domain list - Remember to create it!
        with open("./indicators/domains.txt", "r") as domain_file:
            malicious_domains = domain_file.read()
        
        for ad in detector_ad_list:
            if ad["Domain"] in malicious_domains:
                ad["DomainIsMalicious"] = True

        # for testing gonna just print them out
        for ad in detector_ad_list:
            print(f"ad['Domain']: {ad['Domain']}")
            print(f"ad['DomainIsMalicious']: {ad['DomainIsMalicious']}")
                
        
