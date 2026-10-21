from detector import *
import argparse
import asyncio

# I needed to set up a few different command line options
# https://docs.python.org/3/library/argparse.html

    
def runParser():
    """Makes setting up command line options easy for execution"""
    parser = argparse.ArgumentParser(
    prog = 'executor',
    description = '''This script will allow for a user to execute x number
            of google search engine requests and then will gather all of the
            ad urls generated. These URLS are then resolved using the playwright
            library and assesed for maliciousness against 3 Oracles. Final
            counts of malicious and non-malicious ads are then returned.''')
    parser.add_argument('-d', '--domain-update', action='store_true', help='Rebuild the malicious domain file')
    parser.add_argument('-u', '--url-update', action='store_true', help='Rebuild the malicious url file')
    parser.add_argument('-x', '--execute-query', nargs=2, metavar=('QUERY', 'COUNT'), help='Execute the Query')
    args = parser.parse_args()
    return args

def execute_query(query, count):
    """Wrapper to run all the items associated with pulling and checkign ad urls
    for malicious indicators"""

    # Use the detector object to pull and resolve the ad urls
    d = Detector()
    d.get_ads_list(query, count)
    asyncio.run(d.grab_content_from_ads_list())
    d.pull_domains_from_final_ad_list()
    d.de_google_urls()

    c = Classifier()
    c.sample_final_ad_pages = d.final_ad_pages
    c.mark_malicious_urls_in_ads_list(c.sample_final_ad_pages)
    c.mark_malicious_domains_in_ads_list(c.sample_final_ad_pages)
    c.mark_malicious_ssl_times_in_ads_list(c.sample_final_ad_pages)

    return c.sample_final_ad_pages

if __name__ == "__main__":
    """This is really just a wrapper to allow for easy execution"""

    args = runParser()
    # this list will hold the final collection of all vetted and ran ads
    final_ad_list = []

    if args.domain_update:
        c = Classifier()
        c.build_malicious_domain_list()
    elif args.url_update:
        c = Classifier()
        c.build_malicious_url_list()
    elif args.execute_query:
        final_ad_list = execute_query(args.execute_query[0], args.execute_query[1])
