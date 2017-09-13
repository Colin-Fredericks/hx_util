# import XML libraries
import xml.etree.ElementTree as ET
import sys
import os

instructions = """
To use:
python SetShowAnswer.py show_answer_value path/to/problem/folder

show_answer_value can be one of the usual edX set:
Always
Answered
Attempted
Closed
Finished
CorrectOrPastDue
PastDue
Never

It can also be delete or default, in which case all showanswer values are removed
and the course-wide default takes over.

"""

# Here are all the problem types we work on:
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


# Get directory from command line argument
try:
    answerSetting = sys.argv[1]
    directory = sys.argv[2]
except IndexError:
    # Wrong number of arguments, probably
    sys.exit(instructions)

# Walk through the problems folder
for dirpath, dirnames, filenames in os.walk(directory):
    for eachfile in filenames:

        # Get the XML for each file
        tree = ET.parse(os.path.join(dirpath, eachfile))
        root = tree.getroot()

        # If this isn't a problem file, skip it.
        if root.tag is not 'problem':
            continue

        # Set the showanswer value
        if answerSetting.lower() in allAnswerValues:
            root.set('showanswer', answerSetting)
        elif answerSetting.lower() == 'default' or answerSetting.lower() == 'delete':
            try:
                del root.attrib['showanswer']
            except:
                pass
        else:
            sys.exit('Invalid showanswer setting.')

        # Save the file
        tree.write(os.path.join(dirpath, eachfile), encoding='UTF-8', xml_declaration=False)
