import xml.etree.ElementTree as ET
import collections
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

# We need lists of container nodes and leaf nodes so we can tell
# whether we have to do more recursion.
leaf_nodes = ['html','problem','video','poll']
branch_nodes = ['course','chapter','sequential','vertical','split_test']

# Recursion function for outline-declared xml files
# (doesn't actually recurse yet)
def drillDown(folder, filename, depth):
    tempOD = collections.OrderedDict()

    tree = ET.parse(folder + '/' + filename + '.xml')
    root = tree.getroot()

    for index, child in enumerate(root):
        tempOD[index] = collections.OrderedDict()

        # get display_name or use placeholder
        if 'display_name' in child.attrib:
            tempOD[index]['name'] = child.attrib['display_name']
        else:
            tempOD[index]['name'] = child.tag + str(index)

        # get url_name but there are no placeholders
        if 'url_name' in child.attrib:
            tempOD[index]['url'] = child.attrib['url_name']
        else:
            tempOD[index]['url'] = None

        if child.tag in branch_nodes and depth < 1:
            getDown = drillDown(child.tag, tempOD[index]['url'], depth+1)
            tempOD[index]['contents'] = getDown['tree']
            tempOD[index]['name'] = getDown['parent_name']

        print tempOD[index]

    return {'tree': tempOD, 'parent_name': root.attrib['display_name']}


# Recursion function for inline-declared XML.
# This is a placeholder.

#########
# MAIN
#########

# Get the filename
try:
    coursefile = sys.argv[1]
except IndexError:
    # If run without argument, show instructions.
    sys.exit(instructions)

# This is the ordered dict where we're storing the course structure.
# Later we'll dump it out to the tab-separated file.
course_dict = collections.OrderedDict()

# Open course's root xml file
# Get the current course run filename
root_tree = ET.parse(coursefile)
root_root = root_tree.getroot()

course_dict['name'] = root_root.attrib['course']
course_dict['url'] = root_root.attrib['url_name']
course_dict['contents'] = drillDown('course',course_dict['url'], 0)

# Create a "csv" file with tabs as delimiters

# Make the file's header row

# For each video component display name, make a row of the file:
# Section - Subsection - Unit - Video Component - SRT Filename

# Save the file
