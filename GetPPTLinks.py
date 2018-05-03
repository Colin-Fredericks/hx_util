import sys
import os
import zipfile
import argparse
from glob import glob
from bs4 import BeautifulSoup
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1


instructions = """
Usage:

python3 GetPPTLinks.py path/to/file/ (options)

Extract all hyperlinks from a .pptx file,
including link location, destination, and linked text/formula,
and store them in a .csv file.
If you feed it a folder, it includes all the files in the folder.
Excel mangles UTF-8, so you will need to open the csv in Google Drive.

Options:
  -h  Print this message and quit.
  -r  Recursive - includes nested folders.
  -o  Set an output filename as the next argument.
  -l  Returns a Python list. Used when called by other scripts.

Last update: March 23rd 2018
"""

# Returns a dictionary of all the slides.
# Form: {'filename1':'rIdN', 'filename2':'rIdM'}
def getSlides(soup):

    slides = {}

    for index, tag in enumerate(soup.find_all('p:sldId')):
        if tag.parent.name == 'sldIdLst':
            filename = 'slide' + str(index+1)
            slides[filename] = tag['r:id']

    return slides

# Returns a list of hyperlinks.
def getHyperlinks(soup):

    links = []
    lastParent = None

    for tag in soup.find_all('a:hlinkClick'):
        groupTag = tag.parent.parent.parent

        # Sometimes text gets split up over multiple subtags,
        # especially with unicode for some reason. Don't double-count.
        if groupTag == lastParent:
            continue
        else:
            lastParent = groupTag

        text = type = ''
        # Linked text
        if groupTag.name == 'p':
            # try/except because some hyperlinks have no id
            try:
                text = groupTag.get_text()
                links.append({
                    'id': tag['r:id'],
                    'type': 'text',
                    'text': text
                })
            except:
                pass
        # Linked images
        elif groupTag.name == 'pic':
            try:
                links.append({
                    'id': tag['r:id'],
                    'type': 'image',
                    'text': '(image link)'
                })
            except:
                pass
        # Linked ...something?
        else:
            try:
                if tag['action']:
                    links.append({
                        'id': '',
                        'type': 'PPT Action',
                        'text': groupTag.get_text()
                    })
                else:
                    try: id = tag['r:id']
                    except: id = ''
                    links.append({
                        'id': id,
                        'type': 'unknown',
                        'text': groupTag.get_text()
                    })
            except:
                links.append({
                    'id': '',
                    'type': 'unknown',
                    'text': groupTag.get_text()
                })
    return links

# Add URLs for .pptx hyperlinks
def getURLs(soup, links):

    # Find every link by id and get its url.
    for link in links:
        for rel in soup.find_all('Relationship'):
            if rel['Id'] == link['id']:
                try:
                    # Not every link has a Target
                    if rel['Target'][0:4] == 'http' or 'mail':
                        link['href'] = rel['Target']
                    else:
                        link['href'] = 'Another slide'
                except:
                    link['href'] = 'Probably another slide'
            if link['type'] == 'PPT Action':
                link['href'] = 'unknown'

    return links

# Assembles the list of links from multiple data sources.
# Returns a list of dicts.
def getLinks(filename, args, dirpath):

    # Open the .pptx file as if it were a zip (because it is)
    fullname = os.path.join(dirpath or '', filename)
    archive = zipfile.ZipFile(fullname, 'r')

    # Read bytes from archive for the workbook to get the sheets.
    presentation_data = archive.read('ppt/presentation.xml')
    presentation_soup = BeautifulSoup(presentation_data, 'xml')
    slides = getSlides(presentation_soup)

    complete_links = []

    for index, slide in enumerate(slides):
        # Open each slide and get the hyperlinks.
        slide_data = archive.read('ppt/slides/' + slide + '.xml')
        slide_soup = BeautifulSoup(slide_data, 'xml')
        links = getHyperlinks(slide_soup)

        # URLs are stored in a different file. Cross-reference for each slide.
        url_data = archive.read('ppt/slides/_rels/' + slide + '.xml.rels')
        url_soup = BeautifulSoup(url_data, 'xml')
        links_with_urls = getURLs(url_soup, links)

        for link in links_with_urls:
            link['slide'] = (index + 1)

        complete_links.extend(links_with_urls)

    # Mark each line with the filename in case we're processing more than one.
    for link in complete_links:
        link['filename'] = os.path.basename(filename)

    # Return a list of dicts full of link info
    return complete_links

# Output a file and print some info.
def writeFile(linklist, filecount, outFileName, outFilePath, args):
    print( '\nChecked '
        + str(filecount)
        + ' .pptx file'
        + ('s' if filecount > 1 else '')
        +  ' for links.' )

    with open(outFilePath,'wb') as outputFile:
        # Note that we're printing formulae rather than their values.
        # To include values, add 'value' to the list below.
        fieldnames = ['filename','slide','type','href','text']

        writer = csv.DictWriter(outputFile,
            fieldnames=fieldnames,
            extrasaction='ignore')
        writer.writeheader()

        for row in linklist:
            writer.writerow(row)

    print('Spreadsheet created: ' + outFileName)
    print('Location: ' + outFilePath)


def getPPTLinks(args):

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
            # Make sure this is a PowerPoint file (just check extension)
            if name.lower().endswith('.pptx'):
                # Get the links from that file.
                linklist.extend(getLinks(name, args, False))
                filecount += 1

        # If it's a directory:
        if os.path.isdir(name):
            target_is_folder = True
            # Recursive version using os.walk for all levels.
            if args.r:
                for dirpath, dirnames, files in os.walk(name):
                    for eachfile in files:
                        # Get the links from every file in that directory
                        if eachfile.lower().endswith('.pptx'):
                            linklist.extend(getLinks(eachfile, args, dirpath))
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.pptx'):
                        linklist.extend(getLinks(eachfile, args, dirpath))
                        filecount += 1

    if args.l:
        # When asked to return a list, quietly return one and stop.
        return linklist
    else:
        # Otherwise, create output file as sibling to the original target of the script.
        outFileName = args.o if args.o else 'PPT_Doc_Links.csv'
        if target_is_folder:
            outFileFolder = os.path.abspath(os.path.join(file_names[0], os.pardir))
            outFilePath = os.path.join(outFileFolder, outFileName)
        else:
            outFilePath = os.path.join(os.path.dirname(file_names[0]), outFileName)

        writeFile(linklist, filecount, outFileName, outFilePath, args)

if __name__ == "__main__":
    # this won't be run when imported
    getPPTLinks(sys.argv)
