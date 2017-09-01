import sys
import Make_Course_Sheet
import json2srt
import SrtRename

# Make the video spreadsheet
Make_Course_Sheet.Make_Course_Sheet(sys.argv)
# Transform all the .sjson files to .srt
json2srt.json2srt(sys.argv + ['-r'])
# Rename (copy) the SRT files to match our upload names
SrtRename.SrtRename(sys.argv + ['-c'])
#Done!
print 'SRT archive prep complete.'
print 'Your renamed SRT files are in the static/ folder.'
