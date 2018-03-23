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

python3 GetExcelLinks.py path/to/file/ (options)

Extract all hyperlinks from an .xlsx file,
including link location, destination, and linked text/formula,
and store them in a .csv file.
If you feed it a folder, it includes all the files in the folder.
Excel mangles unicode, so you will need to open the csv in Google Drive.

Options:
  -h  Print this message and quit.
  -r  Recursive - includes nested folders.
  -o  Set an output filename as the next argument.
  -l  Returns a Python list. Used when called by other scripts.

Last update: March 21st 2018
"""

# Returns a dictionary of all the sheets.
# Form: {'filename1':'name1', 'filename2':'name2'}
def getSheets(soup):

    sheets = {}

    for tag in soup.find_all('sheet'):
        if tag.parent.name == 'sheets':
            filename = 'sheet' + tag['sheetId']
            sheets[filename] = tag['name']

    return sheets

# Returns a list of hyperlinks.
def getHyperlinks(soup):

    links = []

    for tag in soup.find_all('hyperlink'):
        text = value = source = ''
        if tag.parent.name == 'hyperlinks':
            # try/except because some hyperlinks have no id.
            try:
                # Need the source text reference number
                cell = soup.find_all('c', r=tag['ref'])[0]
                # Formulae and numbers are stored here too.
                # We're calling it all "text" for this purpose.
                try:
                    if cell['t'] == 's':
                        source = cell.find('v').get_text()
                except:
                    # If there's no 't' attribute,
                    # then this is a number or formula.
                    source = False
                    text = cell.find('f').get_text()
                    value = cell.find('v').get_text()
                links.append({
                    'id': tag['r:id'],
                    'location': tag['ref'],
                    's': source,
                    'value': value,
                    'text': text
                })
            except:
                pass

    return links

# Add URLs for .xlsx hyperlinks
def getURLs(soup, links):

    # Find every link by id and get its url.
    for link in links:
        for rel in soup.find_all('Relationship'):
            if rel['Id'] == link['id']:
                link['href'] = rel['Target']

    return links

# Add text for .xlsx hyperlinks, if we haven't already found it.
def getLinkText(soup, links):

    # Find every link by reference number (s) and get its url.
    for link in links:
        if link['s']:
            sourceTag = soup.find_all('si')[int(link['s'])]
            sourceText = sourceTag.find('t').get_text()
            link['text'] = sourceText
            link['value'] = sourceText

    return links

def getLinks(filename, args, dirpath):

    # Open the .xlsx file as if it were a zip (because it is)
    fullname = os.path.join(dirpath or '', filename)
    archive = zipfile.ZipFile(fullname, 'r')

    # Read bytes from archive for the workbook to get the sheets.
    workbook_data = archive.read('xl/workbook.xml')
    workbook_soup = BeautifulSoup(workbook_data, 'xml')
    sheets = getSheets(workbook_soup)

    complete_links = []

    for sheet in sheets:
        # Open each sheet and get the hyperlinks.
        sheet_data = archive.read('xl/worksheets/' + sheet + '.xml')
        sheet_soup = BeautifulSoup(sheet_data, 'xml')
        links = getHyperlinks(sheet_soup)

        # URLs are stored in a different file. Cross-reference for each sheet.
        url_data = archive.read('xl/worksheets/_rels/' + sheet + '.xml.rels')
        url_soup = BeautifulSoup(url_data, 'xml')
        links_with_urls = getURLs(url_soup, links)

        # Mark each line with the sheet's name.
        for link in links_with_urls:
            link['sheet_name'] = sheets[sheet]

        complete_links.extend(links_with_urls)

    # Text is ALSO stored in a different file, but it's the same one for every sheet.
    string_data = archive.read('xl/sharedStrings.xml')
    string_soup = BeautifulSoup(string_data, 'xml')
    complete_links = getLinkText(string_soup, complete_links)


    # Mark each line with the filename in case we're processing more than one.
    for link in complete_links:
        link['filename'] = os.path.basename(filename)

    # Return a list of dicts full of link info
    return complete_links

def getWordLinks(args):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-r', action='store_true')
    parser.add_argument('-l', action='store_true')
    parser.add_argument('-o', action='store')
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args(args)

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
            if name.lower().endswith('.xlsx'):
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
                        if eachfile.lower().endswith('.xlsx'):
                            linklist.extend(getLinks(eachfile, args, dirpath))
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.xlsx'):
                        linklist.extend(getLinks(eachfile, args, dirpath))
                        filecount += 1

    # When called by other scripts, quietly return the list and stop.
    if args.l:
        return linklist

    # Otherwise, output a file and print some info.
    print( '\nChecked '
        + str(filecount)
        + ' .xlsx file'
        + ('s' if filecount > 1 else '')
        +  ' for links.' )

    # Create output file as sibling to the original target of the script.
    outFileName = args.o if args.o else 'Excel_Doc_Links.csv'
    if target_is_folder:
        outFileFolder = os.path.abspath(os.path.join(file_names[0], os.pardir))
        outFilePath = os.path.join(outFileFolder, outFileName)
    else:
        outFilePath = os.path.join(os.path.dirname(file_names[0]), outFileName)

    with open(outFilePath,'wb') as outputFile:
        # Note that we're printing formulae rather than their values.
        # To include values, add 'value' to the list below.
        fieldnames = ['filename','sheet_name','location','href','text']

        writer = csv.DictWriter(outputFile,
            fieldnames=fieldnames,
            extrasaction='ignore')
        writer.writeheader()

        for row in linklist:
            writer.writerow(row)

    print('Spreadsheet created: ' + outFileName)
    print('Location: ' + outFilePath)

if __name__ == "__main__":
    # this won't be run when imported
    getWordLinks(sys.argv)
