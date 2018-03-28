import sys
if sys.version_info <= (3, 0):
    sys.exit('I am a Python 3 script. Run me with python3.')

import os
import argparse
from bs4 import BeautifulSoup
import lxml
from glob import glob
import unicodecsv as csv # https://pypi.python.org/pypi/unicodecsv/0.14.1
try:
    import GetWordLinks
except:
    print('Cannot find GetWordLinks.py, skipping links in .docx files.')
try:
    import GetExcelLinks
except:
    print('Cannot find GetExcelLinks.py, skipping links in .xlsx files.')
try:
    import GetPPTLinks
except:
    print('Cannot find GetPPTLinks.py, skipping links in .pptx files.')

instructions = """
To use:
python3 Make_Course_Sheet.py path/to/course.xml (options)

Run this on a course folder, or a course.xml file inside an edX course folder (from export).
You will get a Tab-Separated Value file that you should open with Google Drive,
which shows the location of each video and the srt filename for that video.

You can specify the following options:
    -problems  Includes problems AND problem XML instead of videos
    -html      Includes just HTML components
    -video     Forces inclusion of video with html or problems
    -all       Includes html, video, and problem components
    -links     Lists all links in the course.
               Not compatible with above options.
    -o         Sets the output filename to the next argument.

This script may fail on courses with empty containers.

Last update: March 23rd, 2018
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
    'done',
    'drag-and-drop-v2',
    'imageannotation',
    'library_content',
    'lti',
    'lti_consumer',
    'oppia',
    'openassessment',
    'poll',
    'poll_question',
    'problem-builder',
    'recommender',
    'step-builder',
    'survey',
    'textannotation',
    'ubcpi',
    'videoannotation',
    'wiki',
    'word_cloud'
]

# We're skipping many of the skip_tags because they're inline.
# Need to develop that code to handle them.
# Best suggestion to date: try to open file, and traveerse inline XML if we can't.

# Converts from seconds to hh:mm:ss,msec format
# Used to convert duration
def secToHMS(time):
    # Round it to an integer.
    time = int(round(float(time), 0))

    # Downconvert through hours.
    seconds = int(time % 60)
    time -= seconds
    minutes = int((time / 60) % 60)
    time -= (minutes * 60)
    hours = int((time / 3600) % 24)

    # Make sure we get enough zeroes.
    if int(seconds) == 0: seconds = '00'
    elif int(seconds) < 10: seconds = '0' + str(seconds)
    if int(minutes) == 0: minutes = '00'
    elif int(minutes) < 10: minutes = '0' + str(minutes)
    if int(hours) == 0: hours = '00'
    if int(hours) < 10: hours = '0' + str(hours)

    # Send back a string
    return str(hours) + ':' + str(minutes) + ':' + str(seconds)

# Adds notes to links based on file type
def describeLinkData(newlink):
    image_types = ['.png','.gif','.jpg','.jpeg','.svg',
        '.tiff','.tif','.bmp','.jp2','.jif','.pict']

    if newlink['href'].endswith(tuple(image_types)):
        newlink['text'] += ' (image link)'
    if newlink['href'].endswith('.pdf'):    newlink['text'] += ' (PDF file)'
    if newlink['href'].endswith('.ps'):     newlink['text'] += ' (PostScript file)'
    if newlink['href'].endswith('.zip'):    newlink['text'] += ' (zip file)'
    if newlink['href'].endswith('.tar.gz'): newlink['text'] += ' (tarred gzip file)'
    if newlink['href'].endswith('.gz'):     newlink['text'] += ' (gzip file)'
    return newlink

# get list of links from HTML pages, with href and link text
# "soup" is a BeautifulSoup object
def getHTMLLinks(soup):
    links = []

    all_links = soup.findAll(['a','iframe'])

    for link in all_links:
        if link.has_attr('href'):
            # It's a link and not just an anchor.
            if len(link.contents) > 0:
                link_text = ''.join(link.findAll(text=True))
            else:
                link_text = ''
            links.append({
                'href': link.get('href'),
                'text': link_text
            })

        if link.has_attr('src'):
            #It's an iframe.
            links.append({
                'href': link.get('src'),
                'text': '(iframe)'
            })

    betterlinks = [describeLinkData(x) for x in links]
    return betterlinks

# Gets links that aren't in the courseware
def getAuxLinks(rootFileDir):
    # Folders to check:
    aux_folders = ['tabs','info','static']
    aux_paths = [os.path.join(rootFileDir, x) for x in aux_folders]
    aux_links = []

    for folder in aux_paths:
        if os.path.isdir(folder):
            folder_temp = {
                'type': '',
                'name': '',
                'url': '',
                'contents': []
            }

            # Placing all of these folders at the "chapter" level.
            for f in os.listdir(folder):
                file_temp = {
                    'type': '',
                    'name': '',
                    'url': '',
                    'links': []
                }

                # All currently accepted file types:
                if f.endswith( tuple( ['.html','.htm','xml','docx','xlsx','pptx'] ) ):
                    file_temp['name'] = f
                    file_temp['url'] = f

                if f.endswith( tuple( ['.html','.htm'] ) ):
                    soup = BeautifulSoup(open(os.path.join(folder, f), encoding='utf8'), 'html.parser')
                    file_temp['links'] = getHTMLLinks(soup)
                    file_temp['type'] = 'html'
                    folder_temp['contents'].append(file_temp)
                if f.endswith('.xml'):
                    try:
                        tree = lxml.etree.parse(folder + '/' + f)
                    except lxml.etree.XMLSyntaxError:
                        # If we have broken XML, tell us and skip the file.
                        print('Broken XML in file ' + folder + '/' + f + ', skipping.')
                        continue
                    root = tree.getroot()
                    soup = BeautifulSoup(open(os.path.join(folder, f),  encoding='utf8'), 'lxml')
                    file_temp['links'] = getHTMLLinks(soup)
                    file_temp['type'] = 'xml'
                    folder_temp['contents'].append(file_temp)
                if f.endswith('.docx'):
                    if 'GetWordLinks' in sys.modules:
                        targetFile = os.path.join(folder,f)
                        file_temp['links'] = GetWordLinks.getWordLinks([targetFile, '-l'])
                        file_temp['type'] = 'docx'
                        folder_temp['contents'].append(file_temp)
                if f.endswith('.xlsx'):
                    if 'GetExcelLinks' in sys.modules:
                        targetFile = os.path.join(folder,f)
                        file_temp['links'] = GetExcelLinks.getExcelLinks([targetFile, '-l'])
                        file_temp['type'] = 'xlsx'
                        folder_temp['contents'].append(file_temp)
                if f.endswith('.pptx'):
                    if 'GetPPTLinks' in sys.modules:
                        targetFile = os.path.join(folder,f)
                        file_temp['links'] = GetPPTLinks.getPPTLinks([targetFile, '-l'])
                        file_temp['type'] = 'pptx'
                        folder_temp['contents'].append(file_temp)

            folder_temp['chapter'] = os.path.basename(folder)
            folder_temp['name'] = os.path.basename(folder)
            aux_links.append(folder_temp)

    return aux_links

# Always gets the display name.
# For video and problem files, gets other info too
def getComponentInfo(folder, filename, args):
    tree = lxml.etree.parse(folder + '/' + filename + '.xml')
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
    if root.tag == 'video' and args.video:
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
        found_video_asset = False
        for child in root:
            if child.tag == 'video_asset':
                if 'client_video_id' in child.attrib:
                    found_video_asset = True
                    src = child.attrib['client_video_id']
                    # Stripping the host and folders
                    src = src[src.rfind("/")+1:]
                    # Stripping the extension, if there is one.
                    if src.rfind('.') > 0: src = src[:src.rfind('.')]
                    if src == '': temp['upload_name'] = 'No_Upload_Name_' + root.attrib['url_name']
                    temp['upload_name'] = src

                if 'duration' in child.attrib:
                    # Get duration in seconds
                    duration = child.attrib['duration']
                    temp['duration'] = secToHMS(duration)

        # Need a placeholder if there's no video_asset tag or if it's less than informative.
        if not found_video_asset:
            temp['upload_name'] = 'No_Upload_Name_' + root.attrib['url_name']
            temp['duration'] = 'unknown'


    # get problem information
    if root.tag == 'problem':
        if 'rerandomize' in root.attrib:
            temp['rerandomize'] = root.attrib['rerandomize']
        if 'show_reset_button' in root.attrib:
            temp['show_reset_button'] = root.attrib['show_reset_button']
        if root.text is not None:
            temp['inner_xml'] = root.text + ''.join(str(lxml.etree.tostring(e)) for e in root)
            soup = BeautifulSoup(temp['inner_xml'], 'lxml')
            temp['links'] = getHTMLLinks(soup)
        else:
            temp['inner_xml'] = 'No XML.'

    # Right now all we get from HTML is links.
    if root.tag == 'html':
        if args.links:
            # Most of the time our XML will just point to a separate HTML file.
            # In those cases, go open that file and get the links from it.
            if root.text is None:
                innerfilepath = os.path.join(os.path.dirname(folder), 'html', (root.attrib['filename'] + '.html'))
                soup = BeautifulSoup(open(innerfilepath, encoding='utf8'), 'html.parser')
                temp['links'] = getHTMLLinks(soup)
            # If it's declared inline, just get the links right away.
            else:
                soup = BeautifulSoup("".join(root.itertext()), 'html.parser')
                temp['links'] = getHTMLLinks(soup)

    # Label all of them as components regardless of type.
    temp['component'] = temp['name']

    return {'contents': temp, 'parent_name': temp['name']}

# Recursion function for outline-declared xml files
def drillDown(folder, filename, args):
    contents = []

    # If there's no file here, just go back.
    try:
        tree = lxml.etree.parse(os.path.join(folder, (filename + '.xml')))
    except IOError:
        print('Possible missing file: ' + os.path.join(folder, (filename + '.xml')))
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
            'contents': [],
            'links': []
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
        nextFile = os.path.join(os.path.dirname(folder), child.tag)
        if child.tag in branch_nodes:
            child_info = drillDown(nextFile, temp['url'], args)
            temp['contents'] = child_info['contents']
        elif child.tag in leaf_nodes:
            child_info = getComponentInfo(nextFile, temp['url'], args)
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
            # If there are links in this row, break it into multiple entries.
            if len(temp_row['links']) > 0:
                link_rows = []
                for link in temp_row['links']:
                    link_breakout = temp_row.copy()
                    link_breakout['href'] = link['href']
                    link_breakout['linktext'] = link['text']
                    link_rows.append(link_breakout)
                return link_rows
            else:
                return [temp_row]

def writeCourseSheet(rootFileDir, rootFileName, course_dict, args):
    course_name = course_dict['name']
    if args.links: course_name += ' Links'
    course_name += '.tsv'

    outFileName = args.o if args.o else course_name

    # Create a "csv" file with tabs as delimiters
    with open(os.path.join(rootFileDir, outFileName),'wb') as outputfile:
        fieldnames = ['chapter','sequential','vertical','component','type','url']

        # Include the XML if we're dealing with problems
        if args.problems:
                fieldnames.append('inner_xml')
        # Include video data if we're dealing with videos
        if args.links:
                fieldnames = fieldnames + ['href','linktext']
        # Include video data if we're dealing with videos
        if args.video:
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

        if args.all:
            printable = spreadsheet
        else:
            if args.links:
                printable += [row for row in spreadsheet if row['type'] in ['html','problem','xml','docx','pptx','xlsx']]
            if args.html:
                printable += [row for row in spreadsheet if row['type'] == 'html']
            if args.video:
                printable += [row for row in spreadsheet if row['type'] == 'video']
            if args.problems:
                printable += [row for row in spreadsheet if row['type'] == 'problem']

        for row in printable:
            if args.links:
                if row['href'] != '':
                    writer.writerow(row)
            else:
                writer.writerow(row)

        print('Spreadsheet created for ' + course_dict['name'] + '.')
        print('Location: ' + outFileName)

# Main function
def Make_Course_Sheet(args = ['-h']):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-all', action='store_true')
    parser.add_argument('-problems', action='store_true')
    parser.add_argument('-html', action='store_true')
    parser.add_argument('-video', default='True', action='store_true')
    parser.add_argument('-links', action='store_true')
    parser.add_argument('-o', action='store')
    parser.add_argument('file_names', nargs='*')

    # "extra" will help us deal with out-of-order arguments.
    args, extra = parser.parse_known_args(args)

    if args.help: sys.exit(instructions)

    # Do video by default. Don't do it when we're doing other stuff,
    # unless someone intentionally turned it on.
    if not args.video:
        if args.problems or args.html or args.all or args.links:
            args.video = False

    # Link lister is not compatible with other options,
    # mostly because it makes for too big a spreawdsheet.
    if args.links:
        args.problems = args.html = args.all = args.video = False

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob(arg)
    for item in extra:
        file_names += glob(item)

    # Don't run the script on itself.
    if sys.argv[0] in file_names:
        file_names.remove(sys.argv[0])

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    # Get the course.xml file and root directory
    for name in file_names:
        if os.path.isdir(name):
            if os.path.exists( os.path.join(name, 'course.xml')):
                rootFileDir = name
        else:
            if 'course.xml' in name:
                rootFileDir = os.path.dirname(name)

        rootFilePath = os.path.join(rootFileDir, 'course.xml')
        course_tree = lxml.etree.parse(rootFilePath)

        # Open course's root xml file
        # Get the current course run filename
        course_root = course_tree.getroot()

        course_dict = {
            'type': course_root.tag,
            'name': '',
            'url': course_root.attrib['url_name'],
            'contents': []
        }

        course_info = drillDown(
            os.path.join(rootFileDir, course_dict['type']),
            course_dict['url'],
            args
        )
        course_dict['name'] = course_info['parent_name']
        course_dict['contents'] = course_info['contents']

        if args.links:
            course_dict['contents'].extend(getAuxLinks(rootFileDir))

        writeCourseSheet(rootFileDir, rootFilePath, course_dict, args)


if __name__ == "__main__":
    # this won't be run when imported
    Make_Course_Sheet(sys.argv)
