import sys
import os
import csv
import shutil
import argparse
import xml.etree.ElementTree as ET
from glob import glob

instructions = """
To use:
python SrtRename.py course_folder (options)

Renames the .srt files in a course's /static/ folder to match
our original uploaded filenames, as described in a CourseName.tsv file.

Valid options:
  -h Help. Print this message.
  -c Copy. Makes new copy of file with new name. Old one will still be there.
  -n New folder. Puts SRTs in a new folder that's a sibling of the course folder.

Last updated: November 16th, 2017
"""

# Make a dictionary that shows which srt files match which original upload names
def getOriginalNames(course_folder, options):

    nameDict = {}

    # Find our course tsv file. It's based on the course's display_name.
    tree = ET.parse(os.path.join(course_folder, 'course/course.xml'))
    root = tree.getroot()
    course_title = root.attrib['display_name']
    course_tsv_path = os.path.join(course_folder, course_title + '.tsv')

    # Open the tsv file.
    with open(course_tsv_path,'rb') as tsvfile:
        reader = csv.reader(tsvfile, delimiter='\t')

        # Get the right columns
        headers = next(reader)
        upload_column = headers.index('upload_name')
        srt_column = headers.index('sub')

        # Make a dictionary that gives us srt files and original video filenames.
        for row in reader:
            nameDict[row[srt_column]] = row[upload_column]

    return nameDict, course_title


# Set all the srt filenames to be
def setNewNames(course_folder, nameDict, options, course_title):
    static_folder = os.path.join(os.path.abspath(course_folder), 'static')

    if 'n' in options:
        # If we're putting it in a new folder, make it as a child of the course folder.
        target_folder = os.path.join(os.path.abspath(course_folder), os.pardir, course_title + '_SRTs')
        if not os.path.exists(target_folder):
            os.mkdir(target_folder)
    else:
        # Otherwise, put them in the static folder.
        target_folder = static_folder


    filecount = 0

    for srt in nameDict:
        # Strip off the .sjson extension since we're renaming only SRTs.
        oldname = os.path.join(static_folder, srt.replace('.sjson',''))
        # Add .mp4 to the upload filenames because they're videos
        newname = os.path.join(target_folder, nameDict[srt] + '.srt')

        # Rename the files.
        if os.path.exists(oldname):
            if 'c' in options:
                shutil.copyfile(oldname, newname)
            else:
                os.rename(oldname, newname)
            filecount += 1

    print 'Renamed ' + str(filecount) + ' SRT files' + (', kept originals.' if 'c' in options else '.')


# Main function.
def SrtRename(args):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-c', action='store_true')
    parser.add_argument('-n', action='store_true')
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
    if args.c: optionlist.append('c')
    if args.n: optionlist.append('n')

    # Our script might be in the arguments. Don't run on it.
    for i, f in enumerate(file_names):
        if sys.argv[0] in f:
            file_names.remove(f)
            break

    for name in file_names:

        # If it's just a file...
        if os.path.isfile(name):
            # We dont' run on files, we run on course folders.
            sys.exit(instructions)

        # If it's a directory...
        if os.path.isdir(name):
            # Get the concordance for this course.
            nameDict, course_title = getOriginalNames(os.path.abspath(name), optionlist)

            # Go into the static folder and rename the files.
            assert os.path.exists(os.path.join(name, 'static')), 'No static folder found.'
            setNewNames(name, nameDict, optionlist, course_title)

if __name__ == "__main__":
    # this won't be run when imported
    SrtRename(sys.argv)
