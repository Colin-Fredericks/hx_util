import sys
import os
import json
import HTMLParser

instructions = """
To use:
python sjson2srt.py file_or_directory (options)

Creates a new .srt file for every .srt.sjson file found.

Valid options:
  -o Overwrite. Deletes the .srt.sjson file after it has been converted.
  -r Recursive. Works on .srt.sjson files in subdirectories as well.
  -h Help. Print this message.
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
        try:
            jdata = json.load(inputfile)
        except:
            print 'Skipping ' + filename + ': possible invalid JSON'
            return

        # Get the start time, end time, and text as individual lists.
        try:
            startList = jdata['start']
            endList = jdata['end']
            textList = jdata['text']
        except:
            print 'Skipping ' + filename + ': file is missing needed data.'
            return

        # Convert all the times to strings of format H:M:S,ms
        newStartList = [msecToHMS(time) for time in startList]
        newEndList = [msecToHMS(time) for time in startList]

        # EdX escapes HTML entities like quotes and unicode in sjson files. Unescape them.
        # SRT files handle unicode just fine.
        h = HTMLParser.HTMLParser()
        newTextList = [h.unescape(text) for text in textList]

        # Create a file for output
        newFileName = filename.replace('.srt', '')
        newFileName = newFileName.replace('.sjson', '')
        newFileName += '.srt'
        with open(os.path.join(dirpath or '', newFileName), 'wb') as outfile:
            # Step through the lists and write rows of the output file
            for i, txt in enumerate(newTextList):
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

if len(sys.argv) < 2:
    # Wrong number of arguments, probably
    sys.exit(instructions)

# Get file or directory from command line argument.
# With wildcards we might get passed a lot of them.
filenames = sys.argv[1:]
# Get the options and make a list of them for easy reference.
options = sys.argv[-1]

# If the "options" match a file or folder name, those aren't options.
if os.path.exists(options):
    options = ''
# If they don't, that last filename isn't a filename.
else:
    del filenames[-1]

optionlist = []
if 'o' in options: optionlist.append('o')
if 'r' in options: optionlist.append('r')
if 'h' in options: sys.exit(instructions)

for name in filenames:
    # Make sure single files exist.
    assert os.path.exists(name), "File or directory not found."

    # If it's just a file...
    if os.path.isfile(name):
        # Make sure this is an sjson file (just check extension)
        if name.lower().endswith('.sjson'):
            # Convert it to an SRT file
            ConvertToSRT(name, optionlist, False)

    # If it's a directory and not just as part of a wildcard...
    if os.path.isdir(name) and len(filenames) == 1:
        # Recursive version using os.walk for all levels.
        if 'r' in optionlist:
            for dirpath, dirnames, files in os.walk(name):
                for eachfile in files:
                    # Convert every file in that directory.
                    if eachfile.lower().endswith('.sjson'):
                        ConvertToSRT(eachfile, optionlist, dirpath)
        # Non-recursive version breaks os.walk after the first level.
        else:
            topfiles = []
            for (dirpath, dirnames, files) in os.walk(name):
                topfiles.extend(files)
                break
            for eachfile in topfiles:
                if eachfile.lower().endswith('.sjson'):
                    ConvertToSRT(eachfile, optionlist, dirpath)
