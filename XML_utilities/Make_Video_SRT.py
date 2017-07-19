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
skip_tags = ['wiki']

# Always gets the display name.
# For video files, gets other info too
def getComponentInfo(folder, filename, depth):
    tempOD = collections.OrderedDict()
    tree = ET.parse(folder + '/' + filename + '.xml')
    root = tree.getroot()

    tempOD['type'] = root.tag

    # get display_name or use placeholder
    if 'display_name' in root.attrib:
        tempOD['name'] = root.attrib['display_name']
    else:
        tempOD['name'] = root.tag

    # get other video information
    if root.tag == 'video':
        if 'sub' in root.attrib:
            tempOD['sub'] = root.attrib['sub']
        else:
            tempOD['sub'] = 'No sub found.'

        if 'youtube_id_1_0' in root.attrib:
            tempOD['youtube'] = root.attrib['youtube_id_1_0']
        elif 'youtube' in root.attrib:
            # slice to remove the '1.00:' from the start of the ID
            tempOD['youtube'] = root.attrib['youtube'][5:]
        else:
            tempOD['youtube'] = 'No YouTube ID found.'

        if 'edx_video_id' in root.attrib:
            tempOD['edx_video_id'] = root.attrib['edx_video_id']

    return {'tree': tempOD, 'parent_name': root.attrib['display_name']}

# Recursion function for outline-declared xml files
# (doesn't actually recurse yet)
def drillDown(folder, filename, depth):
    tempOD = collections.OrderedDict()
    tempOD['contents'] = collections.OrderedDict()

    tree = ET.parse(folder + '/' + filename + '.xml')
    root = tree.getroot()

    for index, child in enumerate(root):

        tempOD['index'] = index
        tempOD['tag'] = child.tag

        # get display_name or use placeholder
        if 'display_name' in child.attrib:
            tempOD['name'] = child.attrib['display_name']
        else:
            tempOD['name'] = child.tag + str(index)
            tempOD['tempname'] = True

        # get url_name but there are no placeholders
        if 'url_name' in child.attrib:
            tempOD['url'] = child.attrib['url_name']
        else:
            tempOD['url'] = None

        if child.tag in branch_nodes:
            child_info = drillDown(child.tag, tempOD['url'], depth+1)
        elif child.tag in leaf_nodes:
            child_info = getComponentInfo(child.tag, tempOD['url'], depth+1)
        elif child.tag in skip_tags:
            child_info = {'tree': collections.OrderedDict(), 'parent_name': child.tag}
        else:
            sys.exit('New tag type found:' + child.tag)

        tempOD['contents'].update(child_info['tree'])
        # If the display name was temporary, replace it.
        if 'tempname' in tempOD:
            tempOD['name'] = child_info['parent_name']
            del tempOD['tempname']

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

course_dict['url'] = root_root.attrib['url_name']
course_info = drillDown('course',course_dict['url'], 0)
course_dict['contents'] = course_info['tree']
course_dict['name'] = course_info['parent_name']


print course_dict

# Create a "csv" file with tabs as delimiters

# Make the file's header row

# For each video component display name, make a row of the file:
# Section - Subsection - Unit - Video Component - SRT Filename

# Save the file
