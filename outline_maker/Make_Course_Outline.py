import xml.etree.ElementTree as ET
import sys
import os
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1
import argparse

instructions = """
To use:
python Make_Course_Outline.py path/to/course.xml (options)

Run this on a course folder, or a course.xml file inside an edX course folder (from export).
You will get a Tab-Separated Value file that you should open with Google Drive,
which has the course outline (sections, subsections, and units) with URL names.

You can specify the following options:
    -h  Print this message and exit.

This script may fail on courses with empty containers.

Last modified: October 16th, 2017
"""

# Note that we're not including any containers below the verticals, like A/B tests.
branch_nodes = ['course','chapter','sequential']
leaf_nodes = ['vertical']
skip_tags = ['wiki']
global_options = ['video']


# Always gets the display name.
# For video and problem files, gets other info too
def getComponentInfo(folder, filename, depth):
    tree = ET.parse(folder + '/' + filename + '.xml')
    root = tree.getroot()

    temp = {
        'type': root.tag,
        'name': ''
        # space for other info
    }

    # get display_name or use placeholder
    if 'display_name' in root.attrib:
        temp['name'] = root.attrib['display_name']
    else:
        temp['name'] = root.tag

    # Label all of them as verticals regardless of type.
    temp['vertical'] = temp['name']

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
def prepRows(flat_course):

    # Get a list of all dict keys from the entire nested structure and store it in a set.
    key_set = getAllKeys(flat_course)

    # Iterate through the list and add blank entries for any keys in the set that aren't present.
    for row in flat_course:
        for key in key_set:
            if key not in row:
                row[key]=''

    def singleLine(row, type):
        return {
            'chapter': row['chapter'] if type == 'chapter' else '',
            'index': row['index'],
            'sequential': row['sequential'] if type == 'sequential' else '',
            'name': '',
            'vertical': row['vertical'] if type == 'vertical' else '',
            'url': row['url'],
            'type': row['type']
            }

    # Set up the new course from the top.
    new_flat_course = []

    # Arrange the rows to look like a tabbed-out index or TOC,
    # adding new rows for the container tags.
    for index, newrow in enumerate(flat_course):
        if index == 0:
            new_flat_course.append(singleLine(flat_course[index], 'chapter'))
            new_flat_course.append(singleLine(flat_course[index], 'sequential'))
            new_flat_course.append(singleLine(flat_course[index], 'vertical'))
        else:
            if newrow['chapter'] != flat_course[index-1]['chapter']:
                new_flat_course.append(singleLine(flat_course[index], 'chapter'))
                new_flat_course.append(singleLine(flat_course[index], 'sequential'))
                new_flat_course.append(singleLine(flat_course[index], 'vertical'))
            elif newrow['sequential'] != flat_course[index-1]['sequential']:
                new_flat_course.append(singleLine(flat_course[index], 'sequential'))
                new_flat_course.append(singleLine(flat_course[index], 'vertical'))
            elif newrow['vertical'] != flat_course[index-1]['vertical']:
                new_flat_course.append(singleLine(flat_course[index], 'vertical'))

    return new_flat_course

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
def Make_Course_Outline(args = ['-h']):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('course_file_path')

    args = parser.parse_args()

    if args.help:
        sys.exit(instructions)

    # Get the filename and set working directory
    course_file_path = args.course_file_path

    if os.path.isdir(course_file_path):
        # If we're fed a course directory, find the course.xml file in it and use that.
        course_folder_path = os.path.abspath(course_file_path)
        course_file_path = os.path.join(course_folder_path, 'course.xml')
    else:
        # Otherwise, assume we're running on a course.xml file already.
        course_folder_path = os.path.dirname(os.path.abspath(course_file_path))

    os.chdir(course_folder_path)
    coursefile = os.path.basename(os.path.abspath(course_file_path))

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
    with open(course_dict['name'] + ' Outline.tsv','wb') as outputfile:
        fieldnames = ['chapter','sequential','vertical','url','Concept1','Concept2','Concept3']

        writer = csv.DictWriter(outputfile,
            delimiter='\t',
            fieldnames=fieldnames,
            extrasaction='ignore')
        writer.writeheader()

        spreadsheet = prepRows(courseFlattener(course_dict))
        for index, row in enumerate(spreadsheet):
            for key in row:
                spreadsheet[index][key] = spreadsheet[index][key]

        for row in spreadsheet:
            writer.writerow(row)

        print 'Outline created for ' + course_dict['name'] + '.'

if __name__ == "__main__":
    # this won't be run when imported
    Make_Course_Outline(sys.argv)
