import sys
import os
import json
import html
import argparse
from glob import glob

instructions = """
To use:
python3 sjson2srt.py file_or_directory (options)

Creates a new .srt file for every .srt.sjson file found.

Valid options:
  -o Overwrite. Deletes the .srt.sjson file after it has been converted.
  -r Recursive. Works on .srt.sjson files in subdirectories as well.
  -h Help. Print this message.

Last update: March 15th 2018
"""

# Split long lines on a space near the middle.
def splitString(line):

    words = line.split(' ')

    # Get the locations of each space in the line
    indices = [i for i, x in enumerate(line) if x == ' ']

    # Get the difference in line length for each choice of break.
    diffs = []
    for index, word in enumerate(words):
        lineA = ' '.join(words[:index])
        lineB = ' '.join(words[index:])
        diffs.append(abs(len(lineA) - len(lineB)))

    # Break the line on the location of the lowest difference between line lengths.
    breakpoint = indices[ diffs.index(min(diffs))-1 ]

    return line[:breakpoint], line[breakpoint+1:]


def msecToHMS(time):
    # Make sure it's an integer.
    time = int(float(time))

    # Downconvert through hours. SRTs don't handle days.
    msec = time % 1000
    time -= msec
    seconds = (time // 1000) % 60
    time -= (seconds * 1000)
    minutes = (time // 60 // 1000) % 60
    time -= (minutes * 60 * 1000)
    hours = (time // 1000 // 3600) % 24

    # Make sure we get enough zeroes.
    if int(msec) == 0: msec = '000'
    elif int(msec) < 10: msec = '00' + str(msec)
    elif int(msec) < 100: msec = '0' + str(msec)
    if int(seconds) == 0: seconds = '00'
    elif int(seconds) < 10: seconds = '0' + str(seconds)
    if int(minutes) == 0: minutes = '00'
    elif int(minutes) < 10: minutes = '0' + str(minutes)
    if int(hours) == 0: hours = '00'
    elif int(hours) < 10: hours = '0' + str(hours)

    # Send back a string
    return str(hours) + ':' + str(minutes) + ':' + str(seconds) + ',' + str(msec)


def ConvertToSRT(filename, args, dirpath):
    # Open the SJSON file
    with open(os.path.join(dirpath or '', filename),'r', encoding='utf8') as inputfile:
        # Read in the JSON as a dictionary.
        try:
            jdata = json.load(inputfile)
        except:
            print('Skipping ' + filename + ': possible invalid JSON')
            return

        # Get the start time, end time, and text as individual lists.
        try:
            startList = jdata['start']
            endList = jdata['end']
            textList = jdata['text']
        except:
            print('Skipping ' + filename + ': file is missing needed data.')
            return

        # Convert all the times to strings of format H:M:S,ms
        newStartList = [msecToHMS(time) for time in startList]
        newEndList = [msecToHMS(time) for time in endList]

        # EdX escapes HTML entities like quotes and unicode in sjson files. Unescape them.
        # SRT files handle unicode just fine.
        newTextList = [html.unescape(text) for text in textList]

        # Create a file for output
        newFileName = filename.replace('.srt', '')
        newFileName = newFileName.replace('.sjson', '')
        newFileName += '.srt'
        with open(os.path.join(dirpath or '', newFileName), 'w', encoding='utf8') as outfile:
            # Step through the lists and write rows of the output file.
            for i, txt in enumerate(newTextList):
                outfile.write(str(i) + '\n')
                outfile.write(newStartList[i] + ' --> ' + newEndList[i] + '\n')
                # If it's a short line or one without a space, output the whole thing.
                if len(txt) < 45 or txt.find(' ') == -1:
                    outfile.write(str(txt) + '\n')
                # Otherwise, break it up.
                else:
                    lineA, lineB = splitString(txt)
                    outfile.write(str(lineA) + '\n')
                    outfile.write(str(lineB) + '\n')
                outfile.write('\n')

    # If the -o option is set, delete the original
    if args.o:
        os.remove(filename)

# Main function:
def json2srt(args):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-o', action='store_true')
    parser.add_argument('-r', action='store_true')
    parser.add_argument('file_names', nargs='*')

    args = parser.parse_args(args)

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob(arg)

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    if args.help: sys.exit(instructions)

    filecount = 0

    for name in file_names:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found."

        # If it's just a file...
        if os.path.isfile(name):
            # Make sure this is an sjson file (just check extension)
            if name.lower().endswith('.sjson'):
                # Convert it to an SRT file
                ConvertToSRT(name, args, False)
                filecount += 1

        # If it's a directory:
        if os.path.isdir(name):
            # Recursive version using os.walk for all levels.
            if args.r:
                for dirpath, dirnames, files in os.walk(name):
                    for eachfile in files:
                        # Convert every file in that directory.
                        if eachfile.lower().endswith('.sjson'):
                            ConvertToSRT(eachfile, args, dirpath)
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.sjson'):
                        ConvertToSRT(eachfile, args, dirpath)
                        filecount += 1

    print('Converted ' + str(filecount) + ' SJSON files to SRT.')

if __name__ == "__main__":
    # this won't be run when imported
    json2srt(sys.argv)
