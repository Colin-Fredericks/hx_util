import sys
import os
import csv
import glob
import shutil

instructions = """
To use:
python SrtRename.py course_folder (options)

Renames the .srt files in a course's /static/ folder to match
our original uploaded filenames, as described in a CourseName.tsv file.
Make sure there's one and only one tsv file in this course folder.

Valid options:
  -h Help. Print this message.
  -c Copy. Makes new copy of file with new name. Old one will still be there.
"""

# Make a dictionary that shows which srt files match which original upload names
def getOriginalNames(course_folder, options):

    nameDict = {}

    # Find our course tsv file. There's probably only one.
    for name in glob.glob(os.path.join(course_folder, '*.tsv')):
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

    print 'Renamed ' + str(filecount) + ' files.'


########
# MAIN #
########

if len(sys.argv) < 2:
    # Wrong number of arguments, probably
    sys.exit(instructions)

# Get file or directory from command line argument.
# With wildcards we might get passed a lot of them.
filenames = sys.argv[1:]
# Get the options and make a list of them for easy reference.
options = sys.argv[-1]

# If the "options" match a file or folder name, those aren't options.
if os.path.exists(options):
    options = ''
# If they don't, that last filename isn't a filename.
else:
    del filenames[-1]

optionlist = []
if 'h' in options: sys.exit(instructions)
if 'c' in options: optionlist.append('c')

for name in filenames:
    # Make sure single files exist.
    assert os.path.exists(name), 'File or directory not found.'

    # If it's just a file...
    if os.path.isfile(name):
        # We dont' run on files, we run on course folders.
        sys.exit(instructions)

    # If it's a directory...
    if os.path.isdir(name):
        # Get the concordance for this course.
        nameDict = getOriginalNames(os.path.abspath(name), options)

        # Go into the static folder and rename the files.
        assert os.path.exists(os.path.join(name, 'static')), 'No static folder found.'
        setNewNames(name, nameDict, options)
