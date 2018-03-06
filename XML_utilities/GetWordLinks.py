import sys
import io
import os
import re
import zipfile
import argparse
from glob import glob
from lxml import etree as ET
from lxml import objectify
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1


instructions = """
Usage:

python GetWordLinks.py path/to/file/ (options)

Extract all hyperlinks from a .docx file,
including link destination and linked text,
and store them in a .csv file.
If you feed it a folder, it includes all the files in the folder.

Options:
  -h Print this message and quit.
  -r Recursive - includes nested folders.

Last update: February 28th, 2018
"""

# Word documents have namespaces on their XML.
# This is very unhelpful for us. Strip them all.
def strip_ns_prefix(tree):
    #xpath query for selecting all element nodes in namespace
    query = "descendant-or-self::*[namespace-uri()!='']"
    #for each element returned by the above xpath query...
    for element in tree.xpath(query):
        #replace element name with its local name
        element.tag = ET.QName(element).localname
        for attr in element.attrib:
            a = ET.QName(attr).localname
            element.attrib[a] = element.attrib[attr]
    return tree

# Get the text that is the source for the hyperlink.
# Not sure what this will do with image links.
def getLinkedText(root_node):

    links = []

    # xpath for recursive search
    for tag in root_node.xpath('.//hyperlink'):
        # try/except because some hyperlinks have no id.
        try:
            links.append({
                'id': tag.attrib['id'],
                'linktext': ET.tostring(tag, method='text')
            })
        except:
            pass

    return links

# URLs for .docx hyperlinks are stored in a different file.
def getURLs(root_node, links):

    # Find every link by id and get its url.
    for link in links:
        for rel in root_node.xpath('.//Relationship'):
            if rel.attrib['Id'] == link['id']:
                link['url'] = rel.attrib['Target']

    return links

def getLinks(filename, optionlist, dirpath):

    # Open the .docx file as if it were a zip (because it is)
    fullname = os.path.join(dirpath or '', filename)
    archive = zipfile.ZipFile(fullname, 'r')

    # read bytes from archive for the file text and get link text
    file_data = archive.read('word/document.xml')
    doc_root = strip_ns_prefix(ET.fromstring(file_data))
    linked_text = getLinkedText(doc_root)

    # URLs are stored in a different file. Cross-reference.
    url_data = archive.read('word/_rels/document.xml.rels')
    url_root = strip_ns_prefix(ET.fromstring(url_data))
    links_with_urls = getURLs(url_root, linked_text)

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
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args(args)

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob(arg)

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    optionlist = []
    if args.help: sys.exit(instructions)
    if args.r: optionlist.append('r')

    filecount = 0
    linklist = []

    for name in file_names:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found."

        # If it's just a file...
        if os.path.isfile(name):
            # Make sure this is an sjson file (just check extension)
            if name.lower().endswith('.docx'):
                # Convert it to an SRT file
                linklist.extend(getLinks(name, optionlist, False))
                filecount += 1

        # If it's a directory:
        if os.path.isdir(name):
            # Recursive version using os.walk for all levels.
            if 'r' in optionlist:
                for dirpath, dirnames, files in os.walk(name):
                    for eachfile in files:
                        # Convert every file in that directory.
                        if eachfile.lower().endswith('.docx'):
                            linklist.extend(getLinks(eachfile, optionlist, dirpath))
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.docx'):
                        linklist.extend(getLinks(eachfile, optionlist, dirpath))
                        filecount += 1

    print ( 'Checked '
        + str(filecount)
        + ' .docx file'
        + ('s' if filecount > 1 else '')
        +  ' for links.' )

    # For right now, create a csv file with the links
    # Later, should be an option to do this or return list of dicts.
    # Might need to fix location of resulting file - right now it just
    # shows up in the first folder to be scanned.
    with open('Word_Doc_Links.csv','wb') as outputfile:
        fieldnames = ['filename','url','linktext']

        writer = csv.DictWriter(outputfile,
            fieldnames=fieldnames,
            extrasaction='ignore')
        writer.writeheader()

        for row in linklist:
            writer.writerow(row)

    print 'Spreadsheet created: Word_Doc_Links.csv'

if __name__ == "__main__":
    # this won't be run when imported
    getWordLinks(sys.argv)
