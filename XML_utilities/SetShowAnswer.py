# import XML libraries
import xml.etree.ElementTree as ET
import sys
import os
import argparse

instructions = """
To use:
python3 SetShowAnswer.py show_answer_value path/to/problem/folder

show_answer_value can be one of the usual edX set:
  Always
  Answered
  Attempted
  Closed
  Finished
  CorrectOrPastDue
  PastDue
  Never

It can also be delete or default, in which case all
show_answer values are removed and the course-wide
default takes over.

Options:
  -h  Print help message and exit.

Last update: March 15th 2018
"""

# Here are all the options for show_answer values:
allAnswerValues = [
    'always',
    'answered',
    'attempted',
    'closed',
    'finished',
    'correctorpastdue',
    'pastdue',
    'never'
]


parser = argparse.ArgumentParser(usage=instructions, add_help=False)
parser.add_argument('-h', '--help', action='store_true')
parser.add_argument('answerSetting', default='finished')
parser.add_argument('directory', default='.')

args = parser.parse_args()
if args.help:
    sys.exit(instructions)
answerSetting = args.answerSetting.lower()

if not os.path.exists(args.directory):
    sys.exit('Directory not found: ' + args.directory)

numfiles = 0

# Walk through the problems folder
for dirpath, dirnames, filenames in os.walk(args.directory):
    for eachfile in filenames:

        # Get the XML for each file
        tree = ET.parse(os.path.join(dirpath, eachfile))
        root = tree.getroot()

        # If this isn't a problem file, skip it.
        if root.tag != 'problem':
            continue

        # Set the showanswer value
        if answerSetting in allAnswerValues:
            root.set('showanswer', answerSetting)
        elif answerSetting == 'default' or answerSetting == 'delete':
            try:
                del root.attrib['showanswer']
            except:
                pass
        else:
            sys.exit('Invalid showanswer setting.')

        # Save the file
        tree.write(os.path.join(dirpath, eachfile), encoding='UTF-8', xml_declaration=False)
        numfiles += 1


if numfiles == 0:
    print('No files found - wrong or empty directory?')
else:
    print('Show Answer options set for ' + str(numfiles) + ' files.')
