import os
import sys
import argparse
from glob import glob
import xml.etree.ElementTree as ET
import unicodecsv as csv

instructions = """
To use:
python PrepAdaptiveProblems.py path/to/problem_table.csv path/to/problem_folder (options)

Run this on a folder full of edX problems and a CSV file that categorizes
these problems into content groups. You will get a file structure that can be
added to your existing course export, in order to create a home for adaptive
problems within your edX course.

Options:
  -h Display this message and quit
  -m Move the problems instead of copying them

Last update: December 7th, 2017
"""


def getProblemDict(problem_table):

    # Open the problem/CG file. Should be CSV.
    # Read it into a dictionary. Only need content_grouping and problem_name.
    problem_dict = {}
    with open(problem_table, 'rU') as table:
        reader = csv.DictReader(table)
        for row in reader:
            filename = row['problem_file_location'].split('@')[-1]
            problem_dict[filename] = row['content_grouping']

    return problem_dict

def writeFolderStructure(problem_folder):

    # Create a folder structure as follows:
    # new_material/
    #   +--- chapter/    where we keep Sections
    #   +--- problem/    where we keep Problems
    #   +--- sequential/ where we keep Subsections
    #   +--- vertical/   where we keep Units

    folder_names = {
        'section': 'chapter',
        'subsection': 'sequential',
        'unit': 'vertical',
        'problem': 'problem'
    }

    # Make new_material directory in parent of problem_folder
    root = os.path.abspath(os.path.join(problem_folder, os.pardir, 'new_material'))
    if not os.path.exists(root):
        os.makedirs(root)
    folder_paths = { x: os.path.join(root, folder_names[x]) for x in folder_names }

    for name in folder_paths:
        if not os.path.exists(folder_paths[name]):
            os.makedirs(folder_paths[name])

    return folder_paths

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

def writeCourseXML(problem_dict, folder_paths):

    # Get the prefixes for the broad content groups.
    # Probably CG0, CG1, but just take what's left of the first dash or dot.
    # Start with the narrow groups and throw out duplicates via set.
    full_content_groups = set(problem_dict[key] for key in problem_dict)
    for group in full_content_groups:
        content_groups = set(x.split('.')[0] for x in full_content_groups)

    # Create a section named "Adaptive Problems"
    section_text = '<chapter display_name="Adaptive Problems" visible_to_staff_only="true">'
    for group in content_groups:
        # With subsections named after the broad content groupings
        section_text += '<sequential url_name="' + group + '"/>'
    section_text += '</chapter>'

    # Write the section file.
    section = ET.ElementTree(ET.fromstring(section_text))
    indent(section.getroot())
    section.write(os.path.join(folder_paths['section'], 'Adaptive_Problems.xml'),
        encoding='UTF-8', xml_declaration=False)

    # Create subsections named for the broad content groupings.
    for group in content_groups:
        subsection_text = '<sequential display_name="' + group + '">'
        for fullgroup in full_content_groups:
            # With units named after the content groups.
            subsection_text += '<vertical url_name="' + fullgroup + '"/>'
        subsection_text += '</sequential>'

        # Write the subsection files.
        subsection = ET.ElementTree(ET.fromstring(subsection_text))
        indent(subsection.getroot())
        subsection.write(os.path.join(folder_paths['subsection'], group + '.xml'),
            encoding='UTF-8', xml_declaration=False)

    # Crete units named "CG1.0.1", "CG1.1.3", etc. for the narrow content groupings
    for group in content_groups:
        for fullgroup in full_content_groups:
            unit_text = '<vertical display_name="' + fullgroup + '">'
            for problem in problem_dict:
                if problem_dict[problem] == fullgroup:
                    unit_text += '<problem url_name="' + problem + '"/>'
            unit_text += '</vertical>'

            # Write the unit files.
            unit = ET.ElementTree(ET.fromstring(unit_text))
            indent(unit.getroot())
            unit.write(os.path.join(folder_paths['unit'], fullgroup + '.xml'),
                encoding='UTF-8', xml_declaration=False)



    # Put problems into the units according to the first content group listed for them.
    # Don't change problems.

def copyProblems(old_folder, doMove, new_folder):
    # If we're moving problems instead of copying:
        # Delete the new problem folder and move/rename the old one in its place.
    # Otherwise:
        # Copy all the problems from the old problem_folder into the new one.
    return True

# Main function
def PrepAdaptiveProblems(args):
    parser = argparse.ArgumentParser()

    # Get the csv file with the problem names and content groups.
    parser.add_argument('problem_table',
        default='problem_table.csv',
        help='The CSV file with the problem filenames and their content groupings.')

    # Get the folder that has the problems stored in it.
    parser.add_argument('problem_folder',
        default='problem',
        help='The folder containing the problem XML files.')

    # Someone might want to move the problems instead of copying them.
    parser.add_argument('-m',
        default=False,
        action='store_true',
        help='move the problems instead of copying them')

    # If we're run without enough argumnets, print the help.
    if len(args) < 3:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    # Get a dict showing the content group for each problem.
    problem_dict = getProblemDict(args.problem_table)
    # Make the folder structure.
    folder_paths = writeFolderStructure(args.problem_folder)
    # Populate it with xml files for the content groups.
    writeCourseXML(problem_dict, folder_paths)
    # Put the problems into the right folder
    # copyProblems(args.problem_folder, args.m, folder_paths.problem)

    # Print instructions for use.
    # Include the XML tag to insert into the course.xml file.



if __name__ == "__main__":
    # this won't be run when imported
    PrepAdaptiveProblems(sys.argv)
