from collector import Collector
from dotenv import dotenv_values
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
import re
import pickle
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from datetime import datetime
import time

# Used the requests library docs a lot for this
# https://docs.python-requests.org/en/latest/user/advanced/
# Learned aobut the url requests unqute option on stack overflow
# https://stackoverflow.com/questions/16566069/url-decode-utf-8-in-python
# Most of the threading stuff I am copying from the work I did in the
# collector modules, so most of that research and sources applies here as well
# used the python3 docs to help with writing the regular expression to pull
# the domains
# https://docs.python.org/3/library/re.html
# Playwright tutorail from oxylabs
# https://oxylabs.io/blog/playwright-web-scraping
# becuase I only want like 10 or so of these to run concurrently, I think I
# need to use a semaphore
# https://docs.python.org/3/library/asyncio-sync.html#asyncio.Semaphore

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
        self.semaphore = asyncio.Semaphore(50)

    def load_sample_ad_list(self, ad_list_file):
        """Just a way to load a saved ad list so I dont burn out my api"""
        with open("./output/" + ad_list_file, "r") as ad_file:
            self.ads_list = ad_file.read().strip().split("', '")
        
    def get_ads_list(self, query, results_count):
        """This will create a Collector object and pull grab the returned ads"""
        c = Collector()
        c.pull_ads_in_bulk(query, results_count)

        # for debugging only
        # print(c.ads_list)

        for item in c.ads_list:
            if item != "No Ads Returned":
                for ad in item:
                    self.ads_list.append(ad["data_rw"])

    def de_google_urls(self):
        """Goes through final ad list and makes a CleanURL field that holds the URL without the google params"""
        for ad in self.final_ad_pages:
             ad["CleanURL"] = re.findall(r'(^http[s]?:\/\/[^\s\?]*)', ad["FinalURL"])[0]
         
        
    async def send_request_via_proxy(self, browser, URL):
        """Takes in a URL and sends an http request to the URL via residential
        proxy"""
        
        # I got the user-agent from https://www.whatismybrowser.com/guides/the-latest-user-agent/chrome

        # this may be dumb, but I am gonna try to switch in playwright here
        # oxylabs suggests using the async version, but that could break my
        # threads. Im gonna try the async here first and get rid of the
        # threading.  Fortunatley, I am in new branch, so if I break everything
        # I will just abandon this branch and make a new one.
        # https://oxylabs.io/blog/playwright-web-scraping -> demo
        # OK, this blog is basically exactly what I need
        # https://jonathansoma.com/everything/scraping/parallel-playwright/
        # this site was useful as well
        # https://scrapingant.com/blog/block-requests-playwright

        async with self.semaphore:
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/154.0.0.0 Safari/537.36",
                extra_http_headers={
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate, br, zstd',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Connection': 'keep-alive'}
            )
            async with await context.new_page() as page:
                # Here we want to remove images and video and things that use a
                # lot of bandwidth
                # https://playwright.dev/python/docs/api/class-page#page-route
                # https://playwright.dev/python/docs/network
                # Abort based on the request type
                await page.route(
                    "**/*",
                    lambda route: route.abort()
                    if route.request.resource_type in ["image", "stylesheet", "media", "font"]
                    else route.continue_())
                response = await page.goto(
                    URL,
                    timeout=60000, # Initially was using 30k, but dropped a lot
                    wait_until="domcontentloaded")
                title = await page.title()
                OriginalURL = URL
                ResponseHeaders = await response.all_headers()
                RequestHeaders = response.request.headers
                FinalURL = response.url
                if (await response.security_details())["validFrom"]:
                    SSLValidFrom = (await response.security_details())["validFrom"]
                else:
                    SSLValidFrom = "unknown"
                text = await response.text()

                return {"OriginalURL" : OriginalURL,
                        "ResponseHeaders" : ResponseHeaders,
                        "RequestHeaders" : RequestHeaders,
                        "FinalURL" : FinalURL,
                        "Text" : text,
                        "URLIsMalicious" : "Unknown",
                        "SSLValidFrom" : SSLValidFrom,
                        "ClickFixStrings" : False
                        }
                
    async def grab_content_from_ads_list(self):
        """Loops through the ads_list and pulls the resulting webpage from
        each ad item, then updates the final_ad_pages list. Remember that the
        Domain and URL fields are not added unless those functions are explcitly
        called."""
               
        # Much of the below develop with assistance from
        # https://jonathansoma.com/everything/scraping/parallel-playwright/
        # Stealth additions from
        # https://pypi.org/project/playwright-stealth/
        # playwright = await async_playwright().start()
        # Stealth didn't fix, but will be useful so Im gonna keep it.
        # I found this and think it may be my issue
        # https://dev.to/roamproxy/playwright-an-authenticated-proxy-pagegotohttpswwwgooglecom-hangs-and-its-an-http2-24f9#:~:text=In%20the%20run%20that%20hangs%2C%20the%20order,with%20net%20error%20%2D3%20%2C%20ERR_ABORTED%20.
        async with Stealth().use_async(async_playwright()) as p:
            browser = await p.chromium.launch(
                headless = True,
                proxy = {
                    "server": "http://pr.oxylabs.io:7777",
                    "username": f"customer-{self.proxy_username}-cc-US-st-us_california",
                    # "username": f"customer-{self.proxy_username}-cc-IN",
                    "password": self.proxy_pass
                },
                args=["--disable-features=AcceptCHFrame"],
            )

            tasks = [self.send_request_via_proxy(browser, url) for url in self.ads_list]

            for task in asyncio.as_completed(tasks):
                try:
                    result = await task
                    self.final_ad_pages.append(result)
                except Exception as e:
                    print(f"Exception -> {e}")

            await browser.close()

    def pull_domains_from_final_ad_list(self):
        """Converts the final url to domain only and adds to final_ad_list"""

        for ad in self.final_ad_pages:
             ad["Domain"] = re.findall(r'^http[s]?://([^/\s]*)', ad["FinalURL"])[0]
             ad["DomainIsMalicious"] = "unknown"
        
        
    def test_function(self):
        """Just a function to save time for myself in testing"""

        # self.load_sample_ad_list()
        # self.ads_list = ['https://ip.oxylabs.io']
        # self.ads_list = ['https://www.msn.com', 'https://www.yahoo.com', 'https://www.reddit.com']
        # asyncio.run(self.grab_content_from_ads_list())
        # URL1 = "https://ip.oxylabs.io/location"
        # URL2 = "https://www.showmyip.com"
        
        # ad_page = self.get_data_from_url_response(URL2)

        # for key, value in ad_page.items():
        #     print(f"Key: {key}\t\t\tValue: {value}")

        # first I need to build the list
        # self.get_ads_list("2026 Best SUV", 10)
        # then I need to pull a response from each item
        # self.grab_content_from_ads_list()
        # then print the results
        # for item in self.final_ad_pages:
            # print(f"\tOriginal: {item['FinalURL']}")
            # print(f"\tDomain: {item['Domain']}")

        # Creating a file so I can test the Classifier wihtout using up all my
        # api calls, since I am saving objects, looks like I need to 'pickle'.
        # Going to use that, got info from python docs
        # https://docs.python.org/3/library/pickle.html#examples
        # with open("./output/2026_suv_ad_list.pickle", "wb") as sample_file:
        #     pickle.dump(self.final_ad_pages, sample_file, pickle.HIGHEST_PROTOCOL)

        with open("./output/2026_suv_ad_list.pickle", "rb") as pickle_file:
            d.ads_list = pickle.load(pickle_file)

class Classifier:
    """Takes over the attempted classification of ads once they have been
    detected by the Detector class"""
    # https://pythonguides.com/find-duplicates-in-a-python-list/
    # Above is a good link for removing duplicates from a list which I will be
    # doing to remove duplicate ad entries.
    
    def __init__(self):
        self.sample_final_ad_pages = []
        self.creds = dotenv_values('.env')
        self.vt_api_key = self.creds["VT_API_KEY"]

    def build_final_page_list_from_pickle(self, pickle_file):
        """For testing I am pickling the ad list so I dont have to re-run it
        each time. This is how I rebuild the list from that pickle"""

        with open("./output/" + pickle_file, "rb") as pickle_file:
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

    def build_malicious_url_list(self):
        """Like the domian list, this will pull from URLHaus the "malicious url" list which I will compare against."""

        # URLHaus malicious URL list
        url = ("https://urlhaus-api.abuse.ch/v2/files/exports/" 
        + self.creds["URL_HAUS_API_KEY"] 
        + "/urls_full.txt")

        with open("./indicators/urls.txt", 'w') as url_file:
            url_file.write(requests.get(url).text)
        
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

    def mark_malicious_urls_in_ads_list(self, detector_ad_list):
        """Accepts a 'final_ad_pages' list from a detector object and searches
        the known malicious urls list to identify any matches"""

        # Open the url list - Remember it needs to be created first
        with open("./indicators/urls.txt", "r") as url_file:
            malicious_urls = url_file.read()

        for ad in detector_ad_list:
            if ad["CleanURL"] in malicious_urls:
                ad["URLIsMalicious"] = True

        # like above, printing for testing
        for ad in detector_ad_list:
            print(f"ad['CleanURL']: {ad['CleanURL']}")
            print(f"ad['URLIsMalicious']: {ad['URLIsMalicious']}")

    def mark_malicious_ssl_times_in_ads_list(self, detector_ad_list):
        """Accepts a 'final_ad_pages' list from a detector object and calculates
        how long the ssl cert has been active.  Any < 24 hours will mark."""

        now = time.time()
        
        for ad in detector_ad_list:
            if (ad["SSLValidFrom"] != "unknown"):
                # 24 hours is 86,400 seconds
                if (now - ad["SSLValidFrom"]) < 86400:
                    ad["SSLShortDuration"] = True
                else:
                    ad["SSLShortDuration"] = False

    def mark_potential_clickfix(self, detector_ad_list):
        """Looks for signs of clickfix related strings and updates list if found"""
        # https://stackoverflow.com/questions/400212/how-do-i-copy-to-the-clipboard-in-javascript
        # Site above is where I found the clipboard strings.

        for ad in detector_ad_list:
            if (("document.execCommand('copy')" in detector_ad_list["text"]) or
                ("navigator.clipboard.writeText" in detector_ad_list["text"])):
                detector_ad_list["ClickFixString"] = True

    def virus_total_assesment(self):
        """This will define how I submit URLS to the VT Oracle"""
        # Holding here pending approval to use the work VT API for this. I think
        # it will be fine but want to get permission first.

    def test_classifier(self):
        """Just like my other test function.  Saves time as I debug"""
        
        c.build_final_page_list_from_pickle("2026_suv_final_ad_list.pickle")
        
        
        
        
                
        
