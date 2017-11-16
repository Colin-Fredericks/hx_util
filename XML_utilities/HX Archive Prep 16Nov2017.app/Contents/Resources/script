import sys
import os
import Make_Course_Sheet
import json2srt
import SrtRename

filenames = [os.path.basename(word) for word in sys.argv]

# Make sure we're running on the course folder, not something else.
if 'course.xml' in filenames:
    sys.exit('Please run me on a course folder, not the course.xml file.')
if 'course' not in filenames:
    sys.exit('Please run me on a course folder.')

# Make the video spreadsheet
Make_Course_Sheet.Make_Course_Sheet(sys.argv)
# Transform all the .sjson files to .srt
json2srt.json2srt(sys.argv + ['-r'])
# Rename (copy) the SRT files to match our upload names
SrtRename.SrtRename(sys.argv + ['-c'])
#Done!
print 'SRT archive prep complete.'
print 'Your renamed SRT files are in the static/ folder.'
