import sys
import os
import json

instructions = """
To use:
python sjson2srt.py file_or_directory (options)

Creates a new .srt file for every .srt.sjson file found.

Valid options:
  -o Overwrite. Deletes the .srt.sjson file after it has been converted.
  -r Recursive. Works on .srt.sjson files in subdirectories as well.
"""

def msecToHMS(time):
    # Make sure it's an integer.
    time = int(float(time))

    # Downconvert through hours. SRTs don't handle days.
    msec = time % 1000
    time -= msec
    seconds = (time / 1000) % 60
    time -= seconds
    minutes = (time / 60 / 1000) % 60
    time -= minutes
    hours = (time / 1000 / 3600) % 24

    # Make sure we get double-zeroes
    if msec == 0: msec = '000'
    if seconds == 0: seconds = '00'
    if minutes == 0: minutes = '00'
    if hours == 0: hours = '00'

    # Send back a string
    return str(hours) + ':' + str(minutes) + ':' + str(seconds) + ',' + str(msec)


def ConvertToSRT(filename, optionlist, dirpath):
    # Open the SJSON file
    with open(os.path.join(dirpath or '', filename),'r') as inputfile:
        # Read in the JSON as a dictionary.
        jdata = json.load(inputfile)
        # Get the start time, end time, and text as individual lists.
        # Convert all the times to STR-style strings
        startList = jdata['start']
        newStartList = [msecToHMS(time) for time in startList]
        endList = jdata['end']
        newEndList = [msecToHMS(time) for time in startList]
        textList = jdata['text']
        # Create a file for output
        newFileName = filename.replace('.srt', '')
        newFileName = newFileName.replace('.sjson', '')
        newFileName += '.srt'
        with open(os.path.join(dirpath or '', newFileName), 'wb') as outfile:
            # Step through the lists and write rows of the output file
            for i, txt in enumerate(textList):
                outfile.write(str(i) + '\n')
                outfile.write(newStartList[i] + ' --> ' + newEndList[i] + '\n')
                outfile.write(txt + '\n')
                outfile.write('\n')

    # If the -o option is set, delete the original
    if 'o' in optionlist:
        os.remove(filename)

########
# MAIN #
########

# Get directory from command line argument
try:
    filename = sys.argv[1]
except IndexError:
    # Wrong number of arguments, probably
    sys.exit(instructions)

# Get the options and make a list of them for easy reference
try:
    options = sys.argv[2]
except IndexError:
    # it's fine if no options are set.
    options = ''

optionlist = []
if 'o' in options: optionlist.append('o')
if 'r' in options: optionlist.append('r')

assert os.path.exists(filename), "File or directory not found."

# If it's a regular file, convert it to .srt format.
if os.path.isfile(filename):
    # Make sure this is an sjson file (just check extension)
    if filename.lower().endswith('.sjson'):
        # Convert it to an SRT file
        ConvertToSRT(filename, optionlist, False)

# If it's a directory, convert all the files in that directory.
if os.path.isdir(filename):
    # Recursive version using os.walk for all levels.
    if 'r' in optionlist:
        for dirpath, dirnames, filenames in os.walk(filename):
            for eachfile in filenames:
                ConvertToSRT(eachfile, optionlist, dirpath)
    # Non-recursive version breaks os.walk after the first level.
    else:
        topfiles = []
        for (dirpath, dirnames, filenames) in os.walk(filename):
            topfiles.extend(filenames)
            break
        for eachfile in topfiles:
            ConvertToSRT(eachfile, optionlist, dirpath)
