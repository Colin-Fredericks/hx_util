import sys
import os
import zipfile
import argparse
from glob import glob
from bs4 import BeautifulSoup
import PyPDF2
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1


instructions = """
Usage:

python3 GetPDFLinks.py path/to/file/ (options)

Extract all hyperlinks from a .pdf file,
including link destination and linked text or object,
and store them in a .csv file.
If you feed it a folder, it includes all the files in the folder.
Excel mangles unicode, so you will need to open the csv in Google Drive.

Options:
  -h  Print this message and quit.
  -r  Recursive - includes nested folders.
  -o  Set an output filename as the next argument.
  -l  Returns a Python list. Used when called by other scripts.

Last update: March 30th 2018
"""

def getLinks(filename, args, dirpath):

    links = []
    fullname = os.path.join(dirpath or '', filename)
    PDFFile = open(fullname,'rb')

    try:
        PDF = PyPDF2.PdfFileReader(PDFFile)
        pages = PDF.getNumPages()
    except NotImplementedError:
        print(os.path.basename(filename) + ' uses an unsupported encoding.')
        return [{
            'filename': os.path.basename(filename),
            'href': 'Could not decode - unsupported encoding.',
            'page': "n/a"
        }]
    except PyPDF2.utils.PdfReadError:
        print(os.path.basename(filename) + ' could not be decoded.')
        return [{
            'filename': os.path.basename(filename),
            'href': 'Could not decode - PDF Read Error.',
            'page': "n/a"
        }]

    key = '/Annots'
    uri = '/URI'
    ank = '/A'

    for page in range(pages):

        pageSliced = PDF.getPage(page)
        pageObject = pageSliced.getObject()

        if key in pageObject:
            ann = pageObject[key]
            for a in ann:
                u = a.getObject()
                if ank in u:
                    if uri in u[ank]:
                        links.append({
                            'filename': os.path.basename(filename),
                            'href': u[ank][uri],
                            'page': (page+1)
                        })

    # Return a list of dicts full of link info
    return links

def getPDFLinks(args):

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
            # Make sure this is a pdf file (just check extension)
            if name.lower().endswith('.pdf'):
                # Get the links from this file.
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
                        if eachfile.lower().endswith('.pdf'):
                            linklist.extend(getLinks(eachfile, args, dirpath))
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.pdf'):
                        linklist.extend(getLinks(eachfile, args, dirpath))
                        filecount += 1

    # When called by other scripts, quietly return the list and stop.
    if args.l:
        return linklist

    # Otherwise, output a file and print some info.
    print( '\nChecked '
        + str(filecount)
        + ' .docx file'
        + ('s' if filecount > 1 else '')
        +  ' for links.' )

    # Create output file as sibling to the original target of the script.
    outFileName = args.o if args.o else 'PDF_Links.csv'
    if target_is_folder:
        outFileFolder = os.path.abspath(os.path.join(file_names[0], os.pardir))
        outFilePath = os.path.join(outFileFolder, outFileName)
    else:
        outFilePath = os.path.join(os.path.dirname(file_names[0]), outFileName)

    with open(outFilePath,'wb') as outputFile:
        fieldnames = ['filename','page','href']

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
    getPDFLinks(sys.argv)
