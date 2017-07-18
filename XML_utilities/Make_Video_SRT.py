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

# Open course xml file
try:
    coursefile = sys.argv[1]
except IndexError:
    # If run without argument, show instructions.
    sys.exit(instructions)

# Make the file's header row

# Walk the XML structure to get all the display names.

# Make a row of the file:
# Section - Subsection - Unit - Video Component - SRT Filename
