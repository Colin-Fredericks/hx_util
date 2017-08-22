import xml.etree.ElementTree as ET
import sys
import os
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1

instructions = """
To use:
python Make_Course_Sheet.py path/to/course.xml (options)

Run this on a course.xml file inside an edX course folder (from export).
You will get a Tab-Separated Value file that you should open with Google Drive,
which shows the location of each video and the srt filename for that video.

You can specify the following options:
    -problems (includes problems AND problem XML instead of videos)
    -html (includes just HTML components)
    -video (forces inclusion of video with html or problems)
    -all (includes all components)

This script may fail on courses with empty containers.
"""

# We need lists of container nodes and leaf nodes so we can tell
# whether we have to do more recursion.
leaf_nodes = ['html','problem','video']
branch_nodes = ['course','chapter','sequential','vertical','split_test','conditional']
# Many of these are being skipped because they're currently expressed in inline XML
# rather than having their own unique folder in the course export.
skip_tags = [
    'annotatable',
    'discussion',
    'imageannotation',
    'library_content',
    'lti',
    'lti_consumer',
    'openassessment',
    'poll',
    'recommender',
    'survey',
    'textannotation',
    'ubcpi',
    'videoannotation',
    'wiki',
    'word_cloud'
]
global_options = ['video']

# We're skipping many of the skip_tags because they're inline.
# Need to develop that code to handle them.

# Always gets the display name.
# For video and problem files, gets other info too
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
    if root.tag == 'video' and 'video' in global_options:
        if 'sub' in root.attrib:
            temp['sub'] = 'subs_' + root.attrib['sub'] + '.srt.sjson'
        else:
            temp['sub'] = 'No subtitles found.'

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
        if root.text is not None:
            temp['inner_xml'] = (root.text + ''.join(ET.tostring(e) for e in root)).encode('unicode_escape')
        else:
            temp['inner_xml'] = 'No XML.'

    # Label all of them as components regardless of type.
    temp['component'] = temp['name']

    return {'contents': temp, 'parent_name': temp['name']}

# Recursion function for outline-declared xml files
# (doesn't actually recurse yet)
def drillDown(folder, filename, depth):
    contents = []

    # If there's no file here, just go back.
    try:
        tree = ET.parse(folder + '/' + filename + '.xml')
    except IOError:
        print "Possible missing file: " + folder + '/' + filename + '.xml'
        return {'contents': contents, 'parent_name': ''}

    root = tree.getroot()

    # Some items are created without a display name; use their tag name instead.
    if 'display_name' in root.attrib:
        display_name = root.attrib['display_name']
    else:
        display_name = root.tag

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
        # Note that even some inline XML have url_names.
        if 'url_name' in child.attrib:
            temp['url'] = child.attrib['url_name']
        else:
            temp['url'] = None

        # In the future: check to see whether this child is a pointer tag or inline XML.
        # Perhaps by seeing no text in tag and no child tags? (Update: no, this doesn't work.)
        # For right now: skip all the inline stuff; assume pointer.
        if child.tag in branch_nodes:
            child_info = drillDown(child.tag, temp['url'], depth+1)
            temp['contents'] = child_info['contents']
        elif child.tag in leaf_nodes:
            child_info = getComponentInfo(child.tag, temp['url'], depth+1)
            # For leaf nodes, add item info to the dict
            # instead of adding a new contents entry
            temp.update(child_info['contents'])
            del temp['contents']
        elif child.tag in skip_tags:
            child_info = {'contents': False, 'parent_name': child.tag}
            del temp['contents']
        else:
            sys.exit('New tag type found: ' + child.tag)

        # If the display name was temporary, replace it.
        if 'tempname' in temp:
            temp['name'] = child_info['parent_name']
            del temp['tempname']

        # We need not only a name, but a custom key with that name.
        temp[temp['type']] = temp['name']

        contents.append(temp)

    return {'contents': contents, 'parent_name': display_name}

# Recursion function for inline-declared XML.
def drillDownInline(arguments, stuff):
    pass
    # This is a placeholder.
    # Luckily most inlines right now are leaf nodes,
    # but they don't HAVE to be, so... bah.

# Gets the full set of data headers for the course.
# flat_course is a list of dictionaries.
def getAllKeys(flat_course, key_set=set()):

    for row in flat_course:
        for key in row:
            key_set.add(key)

    return key_set


# Ensure that all dicts have the same entries, adding blanks if needed.
# flat_course is a list of dictionaries.
def fillInRows(flat_course):

    # Get a list of all dict keys from the entire nested structure and store it in a set.
    key_set = getAllKeys(flat_course)

    # Iterate through the list and add blank entries for any keys in the set that aren't present.
    for row in flat_course:
        for key in key_set:
            if key not in row:
                row[key]=''

    return flat_course

# Takes a nested structure of lists and dicts that represents the course
# and returns a single list of dicts where each dict is a component
def courseFlattener(course_dict, new_row={}):
    flat_course = []
    temp_row = new_row.copy()

    # Add all the data from the current level to the current row except 'contents'.
    for key in course_dict:
        if key is not 'contents':
            temp_row[key] = course_dict[key]

    # If the current structure has "contents", we're not at the bottom of the hierarchy.
    if 'contents' in course_dict:
        # Go down into each item in "contents" and add its contents to the course.
        for entry in course_dict['contents']:
            temp = courseFlattener(entry, temp_row)
            if temp:
                flat_course = flat_course + temp
        return flat_course

    # If there are no contents, we're at the bottom.
    else:
        # Don't include the wiki and certain other items.
        if temp_row['type'] not in skip_tags:
            return [temp_row]

#########
# MAIN
#########

if len(sys.argv) == 1 or '-h' in sys.argv or '--h' in sys.argv:
    # If run without argument, show instructions.
    sys.exit(instructions)

# Get the filename and set working directory
if len(sys.argv) > 1:
    course_file_path = sys.argv[1]
    course_folder_path = os.path.dirname(os.path.abspath(course_file_path))
    os.chdir(course_folder_path)
    coursefile = os.path.basename(os.path.abspath(course_file_path))

if '-problems' in sys.argv or '--problems' in sys.argv:
    global_options.append('problems')
    global_options.remove('video')
if '-all' in sys.argv or '--all' in sys.argv:
    global_options.append('all')
    global_options.remove('video')
if '-html' in sys.argv or '--html' in sys.argv:
    global_options.append('html')
    global_options.remove('video')
if '-video' in sys.argv or '--video' in sys.argv:
    if 'video' not in global_options:
        global_options.append('video')

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


# Create a "csv" file with tabs as delimiters
with open(course_dict['name'] + '.tsv','wb') as outputfile:
    fieldnames = ['chapter','sequential','vertical','component','type','url']

    # Include the XML if we're dealing with problems
    if 'problems' in global_options:
            fieldnames.append('inner_xml')
    # Include video data if we're dealing with videos
    if 'video' in global_options:
            fieldnames = fieldnames + ['sub','youtube','edx_video_id']

    writer = csv.DictWriter(outputfile,
        delimiter='\t',
        fieldnames=fieldnames,
        extrasaction='ignore')
    writer.writeheader()

    spreadsheet = fillInRows(courseFlattener(course_dict))
    for index, row in enumerate(spreadsheet):
        for key in row:
            spreadsheet[index][key] = spreadsheet[index][key]
    printable = []

    if 'all' in global_options:
        printable = spreadsheet
    else:
        if 'html' in global_options:
            printable += [row for row in spreadsheet if row['type'] == 'html']
        if 'video' in global_options:
            printable += [row for row in spreadsheet if row['type'] == 'video']
        if 'problems' in global_options:
            printable += [row for row in spreadsheet if row['type'] == 'problem']

    for row in printable:
        writer.writerow(row)

    print 'Spreadsheet created for ' + course_dict['name']
