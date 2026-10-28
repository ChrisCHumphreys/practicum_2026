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

def format_results(classified_ad_page_list):
    """Takes in a fully evaluated ad list and outputs results in a readable useful format"""

    totalAds = len(classified_ad_page_list)
    totalNonMaliciousAds = 0
    totalMaliciousAds = 0

    for ad in classified_ad_page_list:
        if ad["DomainIsMalicious"] == True:
            totalMaliciousAds += 1
            print(f"Malicious Domain: {ad['FinalURL']}")
        elif ad["URLIsMalicious"] == True:
            totalMaliciousAds += 1
            print(f"Malicious URL: {ad['FinalURL']}")
        elif ad["SSLShortDuration"] == True:
            totalMaliciousAds += 1
            print(f"Short SSL Duration: {ad['FinalURL']}")
        else:
            totalNonMaliciousAds += 1

    # Formatting line
    print("")

    # Print total from run
    print(f"Total Ad Count: {totalAds}")
    print(f"Non-Malicious Ad Count: {totalNonMaliciousAds}")
    print(f"Malicious Ad Count: {totalMaliciousAds}")

def run_assesment(query, count):
    """this function is for running an assesment via the interpreter rather than via the command line. For my acutal usage I plan on running the assements in this manner."""

    format_results(execute_query(query, count))
        
def run_queries_from_earlier_work():
    """This automates running all the queries from the paper 'Automated
    Collection an dAnalysis of Malware Disseminated via online Advertising'"""

    # qualifiers = ["Free", "Download", "Watch", "Stream", "Hack"]
    # content = ["Movies", "Ebook", "Pdf", "Music", "Mp3", "Wallpaper", "Fonts",
    #            "News", "Sports", "Highlights", "Software", "Freeware",
    #            "Cracks", "Password"]
    
    # combo_list = []
    
    combo_list = ["nft", "cloud computing services", "malware",  "app development", "cryptocurrency", "web design", "web development", "resume building", "infographic maker", "job search sites", "job search", "internship search", "online news", "academic poster template", "video editing software", "photo editing software", "color correction software", "photoshop software", "augmented reality software", "artificial intelligence software", "adobe software"]
    
    # for term in qualifiers:
    #     for item in content:
    #         combo_list.append(term + " " + item)

    for item in combo_list:
        print(f"Running Query: {item} - 150x")
        format_results(execute_query(item, 150))
        print("---------------------------------------\n")

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
