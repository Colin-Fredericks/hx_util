import sys
import os
import csv
import shutil
import argparse
from glob import glob

instructions = """
To use:
python SrtRename.py course_folder (options)

Renames the .srt files in a course's /static/ folder to match
our original uploaded filenames, as described in a CourseName.tsv file.
Make sure there's one and only one tsv file in this course folder.

Valid options:
  -h Help. Print this message.
  -c Copy. Makes new copy of file with new name. Old one will still be there.

Last updated: October 5th, 2017
"""

# Make a dictionary that shows which srt files match which original upload names
def getOriginalNames(course_folder, options):

    nameDict = {}

    # Find our course tsv file. There's probably only one.
    for name in glob(os.path.join(course_folder, '*.tsv')):
        tsv_file = name

    course_tsv_path = os.path.join(course_folder, tsv_file)

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

    return nameDict


# Set all the srt filenames to be
def setNewNames(course_folder, nameDict, options):
    static_folder = os.path.join(os.path.abspath(course_folder), 'static')
    filecount = 0

    for srt in nameDict:
        # Strip off the .sjson extension since we're renaming only SRTs.
        oldname = os.path.join(static_folder, srt.replace('.sjson',''))
        # Add .mp4 to the upload filenames because they're videos
        newname = os.path.join(static_folder, nameDict[srt] + '.srt')

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
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-c', action='store_true')
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args()

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

    for name in file_names:

        # If it's just a file...
        if os.path.isfile(name):
            # We dont' run on files, we run on course folders.
            sys.exit(instructions)

        # If it's a directory...
        if os.path.isdir(name):
            # Get the concordance for this course.
            nameDict = getOriginalNames(os.path.abspath(name), optionlist)

            # Go into the static folder and rename the files.
            assert os.path.exists(os.path.join(name, 'static')), 'No static folder found.'
            setNewNames(name, nameDict, optionlist)

if __name__ == "__main__":
    # this won't be run when imported
    SrtRename(sys.argv)
