import xml.etree.ElementTree as ET
import sys
import os
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1

instructions = """
To use:
python Make_Course_Sheet.py path/to/course.xml (options)

Run this on a course folder, or a course.xml file inside an edX course folder (from export).
You will get a Tab-Separated Value file that you should open with Google Drive,
which shows the location of each video and the srt filename for that video.

You can specify the following options:
    -problems (includes problems AND problem XML instead of videos)
    -html (includes just HTML components)
    -video (forces inclusion of video with html or problems)
    -all (includes all components)

This script may fail on courses with empty containers.

Last update: January 26th, 2018
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
    'drag-and-drop-v2',
    'imageannotation',
    'library_content',
    'lti',
    'lti_consumer',
    'oppia',
    'openassessment',
    'poll',
    'poll_question',
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

# Converts from seconds to hh:mm:ss,msec format
# Used to convert duration
def secToHMS(time):
    # Round it to an integer.
    time = int(round(float(time), 0))

    # Downconvert through hours.
    seconds = time % 60
    time -= seconds
    minutes = (time / 60) % 60
    time -= (minutes * 60)
    hours = (time / 3600) % 24

    # Make sure we get enough zeroes.
    if seconds == 0: seconds = '00'
    if seconds < 10: seconds = '0' + unicode(seconds)
    if minutes == 0: minutes = '00'
    if minutes < 10: minutes = '0' + unicode(minutes)
    if hours == 0: hours = '00'
    if hours < 10: hours = '0' + unicode(hours)

    # Send back a string
    return unicode(hours) + ':' + unicode(minutes) + ':' + unicode(seconds)


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

    # get video information
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

        # We need our original uploaded filename.
        # It's not present in the old XML. :(
        # In new XML, it's in a video_asset tag.
        for child in root:
            if child.tag == 'video_asset':
                if 'client_video_id' in child.attrib:
                    src = child.attrib['client_video_id']
                    # Stripping the host and folders
                    src = src[src.rfind("/")+1:]
                    # Stripping the extension, if there is one.
                    if src.rfind('.') > 0:
                        src = src[:src.rfind('.')]
                    temp['upload_name'] = src

                if 'duration' in child.attrib:
                    # Get duration in seconds
                    duration = child.attrib['duration']
                    temp['duration'] = secToHMS(duration)


    # get problem information
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
def drillDown(folder, filename, depth):
    contents = []

    # If there's no file here, just go back.
    try:
        tree = ET.parse(folder + '/' + filename + '.xml')
    except IOError:
        print "Possible missing file: " + folder + '/' + filename + '.xml'
        return {'contents': contents, 'parent_name': '', 'found_file': False}

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

    return {'contents': contents, 'parent_name': display_name, 'found_file': True}

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

# Main function
def Make_Course_Sheet(args = ['-h']):

    if len(args) == 1 or '-h' in args or '--h' in args:
        # If run without argument, show instructions.
        sys.exit(instructions)

    # Get the filename and set working directory
    if len(args) > 1:
        course_file_path = args[1]

        if os.path.isdir(course_file_path):
            # If we're fed a course directory, find the course.xml file in it and use that.
            course_folder_path = os.path.abspath(course_file_path)
            course_file_path = os.path.join(course_folder_path, 'course.xml')
        else:
            # Otherwise, assume we're running on a course.xml file already.
            course_folder_path = os.path.dirname(os.path.abspath(course_file_path))

        os.chdir(course_folder_path)
        coursefile = os.path.basename(os.path.abspath(course_file_path))

    if '-problems' in args or '--problems' in args:
        global_options.append('problems')
        global_options.remove('video')
    if '-all' in args or '--all' in args:
        global_options.append('all')
        global_options.remove('video')
    if '-html' in args or '--html' in args:
        global_options.append('html')
        global_options.remove('video')
    if '-video' in args or '--video' in args:
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
                fieldnames = fieldnames + ['duration','sub','youtube','edx_video_id','upload_name']

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

        print 'Spreadsheet created for ' + course_dict['name'] + '.'

if __name__ == "__main__":
    # this won't be run when imported
    Make_Course_Sheet(sys.argv)
