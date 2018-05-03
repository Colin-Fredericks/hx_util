import sys
import io
import os
import re
import zipfile
import argparse
from glob import glob
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1


instructions = """
Usage:

python GetWordLinks.py path/to/file/ (options)

Extract all hyperlinks from a .docx file,
including link destination and linked text,
and store them in a .csv file.
If you feed it a folder, it includes all the files in the folder.

Options:
  -h  Print this message and quit.
  -r  Recursive - includes nested folders.
  -o  Set an output filename as the next argument.
  -l  Returns a Python list. Used when called by other scripts.

Last update: March 12th, 2018
"""

# Word documents have namespaces on their XML.
# This is very unhelpful for us. Strip them all.
def strip_ns_prefix(tree):
    return tree.prettify()

# Get the text that is the source for the hyperlink.
# Not sure what this will do with image links.
def getLinkedText(soup):

    links = []

    for tag in soup.findAll('hyperlink'):
        # try/except because some hyperlinks have no id.
        try:
            links.append({
                'id': tag['r:id'],
                'linktext': tag.text
            })
        except:
            pass

    return links

# URLs for .docx hyperlinks are stored in a different file.
def getURLs(soup, links):

    # Find every link by id and get its url.
    for link in links:
        for rel in soup.findAll('Relationship'):
            if rel['Id'] == link['id']:
                link['url'] = rel['Target']

    return links

def getLinks(filename, args, dirpath):

    # Open the .docx file as if it were a zip (because it is)
    fullname = os.path.join(dirpath or '', filename)
    archive = zipfile.ZipFile(fullname, 'r')

    # read bytes from archive for the file text and get link text
    file_data = archive.read('word/document.xml')
    doc_soup = BeautifulSoup(file_data, 'xml')
    linked_text = getLinkedText(doc_soup)

    # URLs are stored in a different file. Cross-reference.
    url_data = archive.read('word/_rels/document.xml.rels')
    url_soup = BeautifulSoup(url_data, 'xml')
    links_with_urls = getURLs(url_soup, linked_text)

    # Mark each line with the filename in case we're processing more than one.
    for link in links_with_urls:
        link['filename'] = os.path.basename(filename)

    # Return a list of dicts full of link info
    return links_with_urls

def getWordLinks(args):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-r', action='store_true')
    parser.add_argument('-l', action='store_true')
    parser.add_argument('-o', action='store')
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args()

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()

    for name in args.file_names:
        file_names += glob(name)

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    # Don't run the script on itself.
    if sys.argv[0] in file_names:
        file_names.remove(sys.argv[0])

    if args.help: sys.exit(instructions)

    filecount = 0
    linklist = []
    target_is_folder = False

    for name in file_names:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found."

        # If it's just a file...
        if os.path.isfile(name):
            # Make sure this is an sjson file (just check extension)
            if name.lower().endswith('.docx'):
                # Convert it to an SRT file
                linklist.extend(getLinks(name, args, False))
                filecount += 1

        # If it's a directory:
        if os.path.isdir(name):
            target_is_folder = True
            # Recursive version using os.walk for all levels.
            if args.r:
                for dirpath, dirnames, files in os.walk(name):
                    for eachfile in files:
                        # Convert every file in that directory.
                        if eachfile.lower().endswith('.docx'):
                            linklist.extend(getLinks(eachfile, args, dirpath))
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.docx'):
                        linklist.extend(getLinks(eachfile, args, dirpath))
                        filecount += 1

    # When called by other scripts, quietly return the list and stop.
    if args.l:
        return linklist

    # Otherwise, output a file and print some info.
    print ( '\nChecked '
        + str(filecount)
        + ' .docx file'
        + ('s' if filecount > 1 else '')
        +  ' for links.' )

    # Create output file as sibling to the original target of the script.
    outFileName = args.o if args.o else 'Word_Doc_Links.csv'
    if target_is_folder:
        outFileFolder = os.path.abspath(os.path.join(file_names[0], os.pardir))
        outFilePath = os.path.join(outFileFolder, outFileName)
    else:
        outFilePath = os.path.join(os.path.dirname(file_names[0]), outFileName)

    with open(outFilePath,'wb') as outputFile:
        fieldnames = ['filename','url','linktext']

        writer = csv.DictWriter(outputFile,
            fieldnames=fieldnames,
            extrasaction='ignore')
        writer.writeheader()

        for row in linklist:
            writer.writerow(row)

    print 'Spreadsheet created: ' + outFileName
    print 'Location: ' + outFilePath

if __name__ == "__main__":
    # this won't be run when imported
    getWordLinks(sys.argv)
