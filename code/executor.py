from detector import *
import argparse

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
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    """This is really just a wrapper to allow for easy execution"""

    args = runParser()

    if args.domain_update:
        c = Classifier()
        c.build_malicious_domain_list()
    
