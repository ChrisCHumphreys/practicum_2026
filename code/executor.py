from detector import *

# I needed to set up a few different command line options
# https://docs.python.org/3/library/argparse.html

if __name__ == "__main__":
    """This is really just a wrapper to allow for easy execution"""

def args():
    """Temp holder 
    parser = argparse.ArgumentParser(
        prog = 'executor',
        description = '''This script will allow for a user to execute x number
            of google search engine requests and then will gather all of the
            ad urls generated. These URLS are then resolved using the playwright
            library and assesed for maliciousness against 3 Oracles. Final
            counts of malicious and non-malicious ads are then returned.'''
        
