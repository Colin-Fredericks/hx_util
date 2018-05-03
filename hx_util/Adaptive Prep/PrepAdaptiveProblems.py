import os
import sys
import shutil
import argparse
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

Last update: December 8th, 2017
"""

final_instructions = """
Complete.
Copy all the files inside the new_material/problem, /chapter, /sequential, and /vertical
folders into your course XML structure.

Add the following line to your course/course.xml file:
<chapter url_name="Adaptive_Problems"/>

Then tar, gzip, and upload the course structure to Studio.
"""

# Makes a dictionary out of the problem filenames and content groupings.
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

    # Make new_material directory in script folder
    root = os.path.abspath(os.path.join(sys.path[0], 'upload_course'))
    if not os.path.exists(root):
        os.makedirs(root)
    folder_paths = { x: os.path.join(root, folder_names[x]) for x in folder_names }

    for name in folder_paths:
        if not os.path.exists(folder_paths[name]):
            os.makedirs(folder_paths[name])

    return folder_paths

# For prettifying XML.
def indent(elem, level=0):
    i = '\n' + level*'  '
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + '  '
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# Creates the XML files for the new piece of course structure.
def writeCourseXML(problem_dict, folder_paths):

    # Get the prefixes for the broad content groups.
    # Start with the narrow groups (longer names) and throw out duplicates via set.
    long_content_groups = set(problem_dict[key] for key in problem_dict)
    long_content_groups = sorted(list(long_content_groups))
    # Fix the blank entry that shows up when things have a blank group listed.
    long_content_groups[0] = 'unlisted'

    scg = set()
    for group in long_content_groups:
        # Probably named CG0, CG1, but just take what's left of the first dash or dot.
        scg.add(group.replace('-','.').split('.')[0])
    short_content_groups = sorted(list(scg))

    # Create a section named "Adaptive Problems"
    section_text = '<chapter display_name="Adaptive Problems" visible_to_staff_only="true">'

    # Create subsections named for the broad content groupings.
    for shortgroup in short_content_groups:

        # With subsections named after the broad content groupings
        section_text += '<sequential url_name="' + shortgroup + '"/>'
        subsection_text = '<sequential display_name="' + shortgroup + '">'

        # Get the narrow groups that fit within the current broad group.
        local_longs = []
        for lg in long_content_groups:
            if lg.startswith(shortgroup):
                local_longs.append(lg)

        for longgroup in local_longs:

            # Get the problems that fall into the current narrow group.
            local_problems = []
            for prob in problem_dict:
                if problem_dict[prob] == longgroup:
                    local_problems.append(prob)

            local_problems.sort()

            # Break up the local problems into groups of 20.
            problem_stack = [local_problems[i:i + 20] for i in xrange(0, len(local_problems), 20)]
            # Put them into units.
            for index, plist in enumerate(problem_stack):
                # We'll use a _part_number suffix to name them.
                filename = longgroup + '_part_' + str(index)

                # Create units named "CG1.0.1", "CG1.1.3", etc. for the narrow content groupings
                subsection_text += '<vertical url_name="' + filename + '"/>'
                unit_text = '<vertical display_name="' + filename + '">'

                for problem in plist:
                    # Put problems into the units according to the first content group listed for them.
                    unit_text += '<problem url_name="' + problem + '"/>'
                unit_text += '</vertical>'

                # Write the unit files.
                unit = ET.ElementTree(ET.fromstring(unit_text))
                indent(unit.getroot())
                unit.write(
                    os.path.join(folder_paths['unit'], filename + '.xml'),
                    encoding='UTF-8',
                    xml_declaration=False
                )

        subsection_text += '</sequential>'

        # Write the subsection files.
        subsection = ET.ElementTree(ET.fromstring(subsection_text))
        indent(subsection.getroot())
        subsection.write(
            os.path.join(folder_paths['subsection'], shortgroup + '.xml'),
            encoding='UTF-8',
            xml_declaration=False
        )

    section_text += '</chapter>'

    # Write the section file.
    section = ET.ElementTree(ET.fromstring(section_text))
    indent(section.getroot())
    section.write(
        os.path.join(folder_paths['section'], 'Adaptive_Problems.xml'),
        encoding='UTF-8',
        xml_declaration=False
    )


# Move/copy problems into the new problem/ folder
def copyProblems(old_folder, doMove, new_folder, problem_dict):
    try:
        # If we're moving:
        if doMove:
            # Delete the new problem folder and move/rename the old one in its place.
            shutil.rmtree(old_folder)
            shutil.move(new_folder, old_folder)
        # If we're copying:
        else:
            # Copy all the problems from the old problem_folder into the new one.
            for f in os.listdir(old_folder):
                if os.path.isfile(os.path.join(old_folder, f)):
                    shutil.copy(os.path.join(old_folder, f), new_folder)

        return True

    except Error:
        return False


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
    copied = copyProblems(args.problem_folder, args.m, folder_paths['problem'], problem_dict)
    if copied:
        # Print instructions for use.
        # Include the XML tag to insert into the course.xml file.
        print final_instructions
    else:
        sys.exit('Error in copying problems to new location.')


if __name__ == "__main__":
    # this won't be run when imported
    PrepAdaptiveProblems(sys.argv)
