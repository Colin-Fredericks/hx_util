# Link checker for edX archives.
# Requires lxml, BeautifulSoup 4+, and Requests
# Borrows heavily from code on Webucator.
# https://www.webucator.com/blog/2016/05/checking-your-sitemap-for-broken-links-with-python/

from __future__ import print_function
import requests
from requests.packages.urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import sys
import os
from bs4 import BeautifulSoup

# Disables warnings from insecure HTTPS requests.
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

instructions = """
To use:

python linkcheck.py path/to/course/folder/

You will see a list of broken links and redirects that you may want to fix.
Links to password-protected sites (like edX) may appear broken.

You can specify the following options:
    -h  Print this message and exit.

Last update: February 9th, 2018
"""

# Checks to see whether the links are valid.
def Check_File_Links(filename):

    with open(filename) as inputFile:
        if filename.endswith('.html'):
            soup = BeautifulSoup(inputFile, 'html.parser')
        else:
            soup = BeautifulSoup(inputFile, 'lxml')

        links = soup.find_all('a')
        urls = [link.get('href') for link in links
                if link.get('href') and ( link.get('href')[0:4]=='http' or link.get('href')[0:5]=='https' ) ]

        results = []
        for i, url in enumerate(urls,1):
            try:
                s = requests.Session()
                retries = Retry(total=10,
                    backoff_factor=0.1,
                    status_forcelist=[ 500, 502, 503, 504 ])
                if(link.get('href')[0:4]=='http'):
                    s.mount('http://', HTTPAdapter(max_retries=retries))
                else:
                    s.mount('https://', HTTPAdapter(max_retries=retries))
                # Note: This doesn't care if the remote host's SSL certificate is valid or not.
                r = s.get(url, verify=False)
                report = str(r.status_code)
                if r.history:
                    history_status_codes = [str(h.status_code) for h in r.history]
                    report += ' [HISTORY: ' + ', '.join(history_status_codes) + ']'
                    result = (r.status_code, r.history, url, 'No error. Redirect to ' + r.url)
                elif r.status_code == 200:
                    result = (r.status_code, r.history, url, 'No error. No redirect.')
                else:
                    result = (r.status_code, r.history, url, 'Error?')
            except Exception as e:
                result = (0, [], url, e)

            results.append(result)

        #Sort by status and then by history length
        results.sort(key=lambda result:(result[0],len(result[1])))

        # Skip files where we have nothing to say.
        if len(results) == 0:
            return

        print(os.path.basename(filename))

        #301s - may want to clean up 301s if you have multiple redirects
        print('Redirects:')
        i = 0
        for result in results:
            if len(result[1]):
                i += 1
                print(i, end='. ')
                for response in result[1]:
                    print('>>', response.url, end='\n\t')
                print('>>>>',result[3])

        #non-200s
        print('\n==========\nERRORS')
        for result in results:
            if result[0] != 200:
                print(result[0], '-', result[2])
            if result[0] == 0:
                print('Full Result:')
                print(result)

        print('*********')


# Go to just the parts of the course we care about.
def Traverse_Course(directory):
    # These are the folders with things that might have links.
    check_folders = [ 'html', 'problem', 'info', 'tabs' ]
    # We should also check folders that have drafts.

    # Go into all those folders and check the links in every file.
    for folder in check_folders:
        print('Folder: ' + folder)
        if os.path.exists(os.path.join(directory, folder)):
            for f in os.listdir(os.path.join(directory, folder)):
                if f.endswith('.html') or (f.endswith('.xml') and folder != 'html'):
                    Check_File_Links(os.path.join(directory, folder, f))
        else:
            print('(Blank)')


# Main function
def Check_Course_Links(args = ['-h']):

    if len(args) == 1 or '-h' in args or '--h' in args:
        # If run with -h or without argument, show instructions.
        sys.exit(instructions)

    # Make sure we're running on the course folder, not something else.
    # Note that the course folder is not always named "course",
    # so we need to look for the course.xml file.
    if 'course.xml' in [os.path.basename(word) for word in sys.argv]:
        print('Please run me on a course folder, not the course.xml file.')

    for directory in sys.argv:
        if os.path.isdir(directory):
            if 'course.xml' in [os.path.basename(f) for f in os.listdir(directory)]:
                print('found course folder: ' + directory)
                Traverse_Course(directory)
            else:
                sys.exit('No course.xml file found in ' + directory)


if __name__ == "__main__":
    # this won't be run when imported
    Check_Course_Links(sys.argv)
