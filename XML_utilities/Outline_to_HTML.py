# import XML libraries
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import HTMLParser
import sys
import os
import csv
import argparse
from glob import glob

instructions = """
To use:
python Outline_to_HTML.py course_outline_file.tsv

Takes a tab-separated course outline (as produced by Make_Course_Outline.py)
and creates an HTML snippet that will display a linked outline.

Options:
  -h  Show this message and exit.

Last update: October 16th, 2017
"""

# For prettifying XML.
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def ConvertToHTML(filename, optionList, dirpath):

    # Open the TSV file
    with open(filename) as tsvfile:
        try:
            # Read in the spreadsheet as a dictionary.
            outline_file = csv.DictReader(tsvfile, delimiter='\t')
        except:
            print 'Skipping ' + filename + ': possible invalid file format'
            return False

        # Set up an HTML file for output.
        root = ET.Element('html')

        # Add tags for the css.
        css_tag = ET.SubElement(root, 'link')
        css_tag.set('rel', 'stylesheet')
        css_tag.set('type', 'text/css')
        css_tag.set('href', '/static/hx-collapse-nav.css')

        # Set up the checkboxes
        checkboxes_div = ET.SubElement(root, 'div')
        checkboxes_div.set('class', 'checkboxes')
        check_header = ET.SubElement(checkboxes_div, 'h4')
        check_header.text = 'Topics'

        show_all = ET.SubElement(checkboxes_div, 'input')
        show_all.set('type', 'checkbox')
        show_all.set('class','showall')
        show_all.set('name', 'showAll')
        show_all.set('id', 'showAll')
        show_all.set('checked', 'checked')
        show_all_label = ET.SubElement(show_all, 'label')
        show_all_label.set('for', 'showAll')
        strong = ET.SubElement(show_all_label, 'strong')
        strong.text = 'Show All'
        ET.SubElement(checkboxes_div, 'br')
        ET.SubElement(checkboxes_div, 'br')

        for key in outline_file.fieldnames:
            if key not in ['chapter','sequential','vertical','url']:
                input_tag = ET.SubElement(checkboxes_div, 'input')
                input_tag.set('type', 'checkbox')
                input_tag.set('class', 'pageselector')
                input_tag.set('name', key)
                input_tag.set('id', key)
                input_label = ET.SubElement(input_tag, 'label')
                input_label.set('for', key)
                input_label.text = key
                ET.SubElement(checkboxes_div, 'br')

        # Make a div and a link for each row in the outline.
        pages_div = ET.SubElement(root, 'div')
        pages_div.set('class', 'allPages')

        for row in outline_file:
            row_tag = ET.SubElement(pages_div, 'div')

            # Get all the classes from the TSV.
            classes = 'hiddenpage '
            if row['chapter']: classes += 'nav-section '
            if row['sequential']: classes += 'nav-sub '
            if row['vertical']: classes += 'nav-unit '
            for key in row:
                if key not in ['chapter','sequential','vertical','url']:
                    if row[key]:
                        classes += key + ' '
            row_tag.set('class', classes.strip())

            a_tag = ET.SubElement(row_tag, 'a')
            a_tag.set('href','/jump_to_id/' + row['url'])
            a_tag.set('target','_blank')
            # Only one of these will have a value in it.
            # This takes the name from that one.
            a_tag.text = row['chapter'] or row['sequential'] or row['vertical']


        # Add tags for the javascript that will make this work.
        # This is intentionally at the bottom of the file.
        js_tag = ET.SubElement(root, 'script')
        js_tag.set('src','/static/hx-collapse-nav.js')

        # Set the new filename
        new_filename = filename[:-3] + ' HTML.html'

        # Prettify the XML.
        indent(root)
        tree = ET.ElementTree(root)

        # Output the new file
        tree.write(os.path.join(dirpath, new_filename), encoding='UTF-8', xml_declaration=False)
        return True


def Outline_to_HTML(args):
    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args()
    if args.help: sys.exit(instructions)

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob(arg)

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    optionlist = []
    filecount = 0

    for name in file_names:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found."

        # If it's just a file, convert it.
        if os.path.isfile(name):
            # Make sure this is a TSV file (just check extension)
            if name.lower().endswith('.tsv'):
                # Convert it to an HTML snippet
                rawfile = ConvertToHTML(name, optionlist, False)

                filecount += 1

        # If it's a directory, we aren't going recursive.
        if os.path.isdir(name) and len(file_names) == 1:
            topfiles = []
            for (dirpath, dirnames, files) in os.walk(name):
                topfiles.extend(files)
                break
            for eachfile in topfiles:
                if eachfile.lower().endswith('.tsv'):
                    ConvertToHTML(eachfile, optionlist, dirpath)
                    filecount += 1

    print 'Converted ' + str(filecount) + ' outline to HTML.'


if __name__ == "__main__":
    # this won't be run when imported
    Outline_to_HTML(sys.argv)
