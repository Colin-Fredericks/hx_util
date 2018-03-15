import sys
if sys.version_info <= (3, 0):
    sys.exit('I am a Python 3 script. Run me with python3.')

import os
import Make_Course_Sheet
import json2srt
import SrtRename

######################################
# HarvardX Archive Prep Script
#
# Usage: python3 HXArchive.py path/to/course/folder
# Calls multiple scripts to help with the archive process for HarvardX courses.
# Passes all arguments through to the scripts.
#
# Last update: March 15th 2018
######################################

def runArchive(args):
    # Make the video spreadsheet
    Make_Course_Sheet.Make_Course_Sheet(args)
    # Transform all the .sjson files to .srt
    json2srt.json2srt(args + ['-r'])
    # Rename (copy) the SRT files to match our upload names
    SrtRename.SrtRename(args + ['-c','-n'])
    #Done!
    print('SRT archive prep complete.')
    print('Your renamed SRT files are a new folder, in the same directory as your course folder.')

# Make sure we're running on the course folder, not something else.
# Note that the course folder is not always named "course",
# so we need to look for the course.xml file.
if 'course.xml' in [os.path.basename(word) for word in sys.argv]:
    print('Please run me on a course folder, not the course.xml file.')

for directory in sys.argv:
    if not os.path.exists(directory):
        sys.exit('Directory not found.')
    if os.path.isdir(directory):
        if directory == 'course':
            print('found course folder: ' + directory)
            runArchive(sys.argv)
        else:
            if 'course.xml' in [os.path.basename(f) for f in os.listdir(directory)]:
                print('found course folder: ' + directory)
                runArchive(sys.argv)
            else:
                print('No course.xml file found in ' + directory)
