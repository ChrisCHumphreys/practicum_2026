import requests
from pprint import pprint
from dotenv import dotenv_values
import json
import threading
from concurrent.futures import ThreadPoolExecutor

# Note that much of the threading code was borrowed/inspried from the
# tutorials at
# https://reintech.io/blog/how-to-create-a-multi-threaded-application-with-python
# Much of the info on stopping threads from 
# https://www.stratascratch.com/blog/python-threading-like-a-pro
# Thread pool executor docs
# https://docs.python.org/3/library/concurrent.futures.html
# https://superfastpython.com/threadpoolexecutor-in-python/


# Saving this for reference while I work, but its just a copy and paste of a search URL I ran manually
test_URL = """https://www.google.com/search?q=Free Streaming&sca_esv=6a464870af6be845&sxsrf=APpeQntsmLYZR-H8-LTAO5HVJjzhOz7sTg:1789164589470&ei=LXykauiwHKvKp84PzZS3oQ8&biw=2493&bih=623&ved=2ahUKEwio-7K-xeeWAxUr5ckDHU3KLfQQ4dUDegQIBhAM&oq=Free Streaming&gs_lp=Egxnd3Mtd2l6LXNlcnAiDkZyZWUgU3RyZWFtaW5nMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBATIXEC4Y3AYYuAYY2gYY2AIYyAMYsAPYAQEyFxAuGNwGGLgGGNoGGNgCGMgDGLAD2AEBMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBATIXEC4Y3AYYuAYY2gYY2AIYyAMYsAPYAQEyFxAuGNwGGLgGGNoGGNgCGMgDGLAD2AEBMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBAUjnFFAAWABwAXgBkAEAmAEAoAEAqgEAuAEMyAEAmAIBoAIKmAMAiAYBkAYTugYGCAEQARgZkgcBMaAHALIHALgHAMIHAzItMcgHB4AIAQ&sclient=gws-wiz-serp"""

class Collector:
    """Class to contain collecter functions, Oxylabs has a max concurrent pull
       of 10 items so leaving that here for now"""
    def __init__(self, max_thread_count=10):
        self.creds = dotenv_values('.env')
        self.username = self.creds['OXY_USERNAME']
        self.password = self.creds['OXY_PASS']
        self.ads_list = []
        self.max_thread_count = max_thread_count
        self.failed_queries = 0
        self._stop_event = threading.Event()
    
    def get_raw_url_content(self, URL):
        """This is a first function to just pull in a single URL"""
    
        content = requests.get(URL)
        return content
    
    def output_requests_response(self, URL):
        """Prings out the Headers, response code, and text of a website"""
    
        content = get_raw_url_content(URL)
    
        print(f"Headers: {content.headers}")
        print(f"Response Code: {content.status_code}")
        print(f"Website Text: {content.text}")

    def get_normalized_google_serp(self, query):
        """This will pull back and return a single nomralized page of google
        results"""

        payload = {
            'source' : 'google_ads',
            'query' : query,
            'geo_location' : 'Boston,United States',
            'parse' : True,
            'user_agent_type' : 'desktop'
        }

        response = requests.request(
            'POST', 'https://realtime.oxylabs.io/v1/queries',
            auth=(self.username, self.password), json=payload)
        return response

    def extract_ads_from_json_response(self, serp_response):
        """This function will return just the ads from a raw
        JSON return from the SERP"""

        try:
            ads = serp_response.json()['results'][0]['content']['results']['paid']
            if (ads == []):
                return "No Ads Returned"
            else:
                return ads
        except:
            return "Query Failed"

    def get_ads_from_query(self, query):
        """Funciton that wraps together smaller functions to take in a
        query and return just the ad section of the url"""

        
        response = self.get_normalized_google_serp(query)
        ads = self.extract_ads_from_json_response(response)
        if (ads != "Query Failed"):
            self.ads_list.append(ads)
        else:
            self.failed_queries += 1

    def pull_ads_in_bulk(self, query, count):
        """This is to allow for multiple threads to run at once
           Code here was adapted and borrowed from
           https://reintech.io/blog/how-to-create-a-multi-threaded-application-with-python
           and https://docs.python.org/3/library/threading.html
        """ 
        
        threads = []
    
        with ThreadPoolExecutor(self.max_thread_count) as executor:
            _ = [executor.submit(self.get_ads_from_query, query) for i in range(count)]
       

            
