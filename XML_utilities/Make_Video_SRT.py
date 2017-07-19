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
    tree = ET.parse(folder + '/' + filename + '.xml')
    root = tree.getroot()

    temp = {
        'type': root.tag,
        'name': '',
        # space for other info
    }

    # get display_name or use placeholder
    if 'display_name' in root.attrib:
        temp['name'] = root.attrib['display_name']
    else:
        temp['name'] = root.tag

    # get other video information
    if root.tag == 'video':
        if 'sub' in root.attrib:
            temp['sub'] = root.attrib['sub']
        else:
            temp['sub'] = 'No sub found.'

        if 'youtube_id_1_0' in root.attrib:
            temp['youtube'] = root.attrib['youtube_id_1_0']
        elif 'youtube' in root.attrib:
            # slice to remove the '1.00:' from the start of the ID
            temp['youtube'] = root.attrib['youtube'][5:]
        else:
            temp['youtube'] = 'No YouTube ID found.'

        if 'edx_video_id' in root.attrib:
            temp['edx_video_id'] = root.attrib['edx_video_id']

    if root.tag == 'problem':
        if 'rerandomize' in root.attrib:
            temp['rerandomize'] = root.attrib['rerandomize']
        if 'show_reset_button' in root.attrib:
            temp['show_reset_button'] = root.attrib['show_reset_button']

    return {'contents': temp, 'parent_name': root.attrib['display_name']}

# Recursion function for outline-declared xml files
# (doesn't actually recurse yet)
def drillDown(folder, filename, depth):
    contents = []

    tree = ET.parse(folder + '/' + filename + '.xml')
    root = tree.getroot()
    display_name = root.attrib['display_name']

    for index, child in enumerate(root):
        temp = {
            'index': index,
            'type': child.tag,
            'name': '',
            'url': '',
            'contents': []
        }

        # get display_name or use placeholder
        if 'display_name' in child.attrib:
            temp['name'] = child.attrib['display_name']
        else:
            temp['name'] = child.tag + str(index)
            temp['tempname'] = True

        # get url_name but there are no placeholders
        if 'url_name' in child.attrib:
            temp['url'] = child.attrib['url_name']
        else:
            temp['url'] = None

        if child.tag in branch_nodes:
            child_info = drillDown(child.tag, temp['url'], depth+1)
            temp['contents']=child_info['contents']
        elif child.tag in leaf_nodes:
            child_info = getComponentInfo(child.tag, temp['url'], depth+1)
            # For leaf nodes, add item info directly to the dict.
            temp.update(child_info['contents'])
            del temp['contents']
        elif child.tag in skip_tags:
            child_info = {'contents': False, 'parent_name': child.tag}
        else:
            sys.exit('New tag type found: ' + child.tag)

        # If the display name was temporary, replace it.
        if 'tempname' in temp:
            temp['name'] = child_info['parent_name']
            del temp['tempname']

        contents.append(temp)

    return {'contents': contents, 'parent_name': display_name}

# Recursion function for inline-declared XML.
# def drillDownInline(arguments, and, stuff):
    # This is a placeholder.

# Ensure that all dicts have the same entries, adding blanks if needed.
def fillInRows(flat_course):

    # Get a list of all dict keys and store it in a set.
    key_set = set()
    [[key_set.update(k) for k in row] for row in flat_course]

    # Iterate through the list and add blank entries for any keys in the set that aren't present.
    for row in flat_course:
        for key in key_set:
            if key not in row:
                row[key]=''

    return flat_course


def courseFlattener(course_dict):

    # Each component will be a dict in this list.
    flat_course = []
    current_row = {}

    # Start at top level of dict. Add all the keys to the current row except contents.
    for key in course_dict:
        if key is not 'contents':
            current_row[key] = course_dict[key]

    # If the current structure has "contents", we're not at the bottom of the hierarchy.
    if 'contents' in course_dict:
        # A. Go down into "contents". until we're at the bottom, collecting dict entries from each parent.
        for entry in course_dict['contents']:
            courseFlattener(course_dict['contents'])


    # Add that dict to the list.
    # B. Go up a level and look for the next item in "contents".
        # If there is no next item, go back to B.
    # Go back to A, updating dict entries if they're new.
        # Go back to B.

    return flat_course

#########
# MAIN
#########

# Get the filename
try:
    coursefile = sys.argv[1]
except IndexError:
    # If run without argument, show instructions.
    sys.exit(instructions)

# Open course's root xml file
# Get the current course run filename
course_tree = ET.parse(coursefile)
course_root = course_tree.getroot()

# This is the ordered dict where we're storing the course structure.
# Later we'll dump it out to the tab-separated file.
course_dict = {
    'type': 'course',
    'name': '',
    'url': course_root.attrib['url_name'],
    'contents': []
}

course_info = drillDown('course', course_dict['url'], 0)
course_dict['name'] = course_info['parent_name']
course_dict['contents'] = course_info['contents']


# print course_dict


# Create a "csv" file with tabs as delimiters
with open('videolinker.csv','wb') as outputfile:
    fieldnames = ['name','type','url']
    writer = csv.DictWriter(outputfile,
        delimiter='\t',
        fieldnames=fieldnames,
        extrasaction='ignore')
    writer.writeheader()
    for row in fillInRows(courseFlattener(course_dict)):
        writer.writerow(row)
