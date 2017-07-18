import xml.etree.ElementTree as ET
import csv
import sys
import os

instructions = """
To use:
python Make_Video_SRT.py path/to/course.xml

Run this on a course.xml file inside an edX course folder (from export).
You will get a coursename.tsv file that shows the
location of each video, and the srt filename for that video.

(TSV = tab-separated value. Open with Excel.)
"""

# Get the filename
try:
    coursefile = sys.argv[1]
except IndexError:
    # If run without argument, show instructions.
    sys.exit(instructions)

# Open course's root xml file
with open (coursefile, 'rb') as courseroot:
    # Get the current course run filename
    # Open the course run file

# Chapter file

# Sequential file

# Vertical file

# Video file or inline video declaration in vertical

# Make the file's header row

# Walk the XML structure to get all the display names.

# For each video component display name, make a row of the file:
# Section - Subsection - Unit - Video Component - SRT Filename

# Save the file
