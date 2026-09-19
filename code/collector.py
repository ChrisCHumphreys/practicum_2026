import requests
from pprint import pprint
from dotenv import dotenv_values
import json
import threading

# Note that much of the threading code was borrowed/inspried from the
# tutorials at
# https://reintech.io/blog/how-to-create-a-multi-threaded-application-with-python


# Saving this for reference while I work, but its just a copy and paste of a search URL I ran manually
test_URL = """https://www.google.com/search?q=Free Streaming&sca_esv=6a464870af6be845&sxsrf=APpeQntsmLYZR-H8-LTAO5HVJjzhOz7sTg:1789164589470&ei=LXykauiwHKvKp84PzZS3oQ8&biw=2493&bih=623&ved=2ahUKEwio-7K-xeeWAxUr5ckDHU3KLfQQ4dUDegQIBhAM&oq=Free Streaming&gs_lp=Egxnd3Mtd2l6LXNlcnAiDkZyZWUgU3RyZWFtaW5nMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMgoQABhHGNYEGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMg0QABiABBiKBRhDGLADMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBATIXEC4Y3AYYuAYY2gYY2AIYyAMYsAPYAQEyFxAuGNwGGLgGGNoGGNgCGMgDGLAD2AEBMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBATIXEC4Y3AYYuAYY2gYY2AIYyAMYsAPYAQEyFxAuGNwGGLgGGNoGGNgCGMgDGLAD2AEBMhcQLhjcBhi4BhjaBhjYAhjIAxiwA9gBAUjnFFAAWABwAXgBkAEAmAEAoAEAqgEAuAEMyAEAmAIBoAIKmAMAiAYBkAYTugYGCAEQARgZkgcBMaAHALIHALgHAMIHAzItMcgHB4AIAQ&sclient=gws-wiz-serp"""

class Collector:
    """Class to contain collecter functions"""
    def __init__(self):
        self.creds = dotenv_values('.env')
        self.username = self.creds['OXY_USERNAME']
        self.password = self.creds['OXY_PASS']
        self.ads_list = []
    
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
            'geo_location' : 'Chicago,United States',
            'parse' : True,
            'user_agent_type' : 'desktop'
        }

        response = requests.request(
            'POST', 'https://realtime.oxylabs.io/v1/queries',
            auth=(self.username, self.password), json=payload)
        # ads_list = json.dumps(
        #     response.json()['results'][0]['content']['results']['paid'])
        return response

    def extract_ads_from_json_response(self, serp_response):
        """This function will return just the ads from a raw
        JSON return from the SERP"""

        return serp_response.json()['results'][0]['content']['results']['paid']

    def get_adds_from_query(self, query):
        """Funciton that wraps together smaller functions to take in a
        query and return just the ad section of the url"""

        response = self.get_normalized_google_serp(query)
        ads = self.extract_ads_from_json_response(response)

        self.ads_list.append(ads)
        
        return ads

    def pull_ads_with_threading(self, query, count):
        """This is to allow for multiple threads to run at once
           Code here was adapted and borrowed from
           https://reintech.io/blog/how-to-create-a-multi-threaded-application-with-python
           and https://docs.python.org/3/library/threading.html
        """

        # For testing putting this at 3, but likely will go to 10 for real use
        threading.Semaphore(3)

        threads = []
        for i in range(count):
            thread = threading.Thread(
                target=self.get_adds_from_query,
                args=(query,)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print("Testing Ran executed!")

        

    
    
    # for i in range(10):
    #     output_requests_response(test_URL)def get_raw_url_content(URL):

    
