# import XML libraries
import xml.etree.ElementTree as ET
import sys
import os
import csv
import argparse
from glob import glob

instructions = """
To use:
python Outline_to_HTML.py course_outline_file.tsv

Takes a tab-separated course outline (as produced by Make_Course_Outline.py)
and creates an HTML snippet that will display a linked outline.

Options:
  -h  Show this message and exit.

Last update: October 16th, 2017
"""

def ConvertToHTML(filename, optionList):
    pass

def Outline_to_HTML(args):
    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args()
    if args.help: sys.exit(instructions)

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob(arg)

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    filecount = 0

    for name in file_names:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found."

        # If it's just a file, convert it.
        if os.path.isfile(name):
            # Make sure this is a TSV file (just check extension)
            if name.lower().endswith('.tsv'):
                # Convert it to an SRT file
                ConvertToHTML(name, optionlist, False)
                filecount += 1

        # If it's a directory, we aren't going recursive.
        if os.path.isdir(name) and len(file_names) == 1:
            topfiles = []
            for (dirpath, dirnames, files) in os.walk(name):
                topfiles.extend(files)
                break
            for eachfile in topfiles:
                if eachfile.lower().endswith('.tsv'):
                    ConvertToHTML(eachfile, optionlist, dirpath)
                    filecount += 1

    print 'Converted ' + str(filecount) + ' SJSON files to SRT.'


if __name__ == "__main__":
    # this won't be run when imported
    Outline_to_HTML(sys.argv)
