import sys
if sys.version_info <= (3, 0):
    sys.exit('I am a Python 3 script. Run me with python3.')

import os
import Make_Course_Sheet
import json2srt
import SrtRename

######################################
# HarvardX Live Tools
#
# Usage: python3 HXLiveTools.py path/to/course/folder
# Calls multiple scripts to help with the archive process for HarvardX courses.
# Passes all arguments through to the scripts, but you probably don't want to.
#
# Last update: March 15th 2018
######################################

def runLiveTools(args):
    # Make the video spreadsheet
    Make_Course_Sheet.Make_Course_Sheet(args + ['-o', 'Course_Video_Sheet.tsv'])
    # Transform all the .sjson files to .srt
    json2srt.json2srt(args + ['-r'])
    # Rename (copy) the SRT files to match our upload names and make a zip file.
    # Put this in the course folder.
    SrtRename.SrtRename(args + ['-n', '-z', '-i', 'Course_Video_Sheet.tsv', '-o', 'Course_SRT_Files.zip'])
    # Make the link spreadsheet.
    Make_Course_Sheet.Make_Course_Sheet(args + ['-links', '-o', 'Course_Link_Sheet.tsv'])
    # Make the link spreadsheet.
    Make_Course_Sheet.Make_Course_Sheet(args + ['-all', '-o', 'Course_Full_Sheet.tsv'])
    #Done!
    print('SRT archive prep complete.')
    print('Your renamed SRT files are a zip file, in the same directory as your course folder.')

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
            runLiveTools(sys.argv)
        else:
            if 'course.xml' in [os.path.basename(f) for f in os.listdir(directory)]:
                print('found course folder: ' + directory)
                runLiveTools(sys.argv)
            else:
                print('No course.xml file found in ' + directory)
