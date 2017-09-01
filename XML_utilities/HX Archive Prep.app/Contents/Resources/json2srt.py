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
    seconds = (time / 1000) % 60
    time -= seconds
    minutes = (time / 60 / 1000) % 60
    time -= minutes
    hours = (time / 1000 / 3600) % 24

    # Make sure we get enough zeroes.
    if msec == 0: msec = '000'
    if int(msec) < 10: msec = '00' + str(msec)
    if int(msec) < 100: msec = '0' + str(msec)
    if seconds == 0: seconds = '00'
    if seconds < 10: seconds = '0' + str(seconds)
    if minutes == 0: minutes = '00'
    if minutes < 10: minutes = '0' + str(minutes)
    if hours == 0: hours = '00'
    if hours < 10: hours = '0' + str(hours)

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
        newEndList = [msecToHMS(time) for time in endList]

        # EdX escapes HTML entities like quotes and unicode in sjson files. Unescape them.
        # SRT files handle unicode just fine.
        h = HTMLParser.HTMLParser()
        newTextList = [h.unescape(text) for text in textList]

        # Create a file for output
        newFileName = filename.replace('.srt', '')
        newFileName = newFileName.replace('.sjson', '')
        newFileName += '.srt'
        with open(os.path.join(dirpath or '', newFileName), 'wb') as outfile:
            # Step through the lists and write rows of the output file.
            for i, txt in enumerate(newTextList):
                outfile.write(unicode(i) + '\n')
                outfile.write(newStartList[i] + ' --> ' + newEndList[i] + '\n')
                # If it's a short line or one without a space, output the whole thing.
                if len(txt) < 45 or txt.find(' ') == -1:
                    outfile.write(unicode(txt).encode('utf-8') + '\n')
                # Otherwise, break it up.
                else:
                    lineA, lineB = splitString(txt)
                    outfile.write(unicode(lineA).encode('utf-8') + '\n')
                    outfile.write(unicode(lineB).encode('utf-8') + '\n')
                outfile.write('\n')

    # If the -o option is set, delete the original
    if 'o' in optionlist:
        os.remove(filename)

# Main function:
def json2srt(args):
    if len(args) < 2:
        # Wrong number of arguments, probably
        sys.exit(instructions)

    # Get file or directory from command line argument.
    # With wildcards we might get passed a lot of them.
    filenames = args[1:]
    # Get the options and make a list of them for easy reference.
    options = args[-1]

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

    filecount = 0

    for name in filenames:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found."

        # If it's just a file...
        if os.path.isfile(name):
            # Make sure this is an sjson file (just check extension)
            if name.lower().endswith('.sjson'):
                # Convert it to an SRT file
                ConvertToSRT(name, optionlist, False)
                filecount += 1

        # If it's a directory and not just as part of a wildcard...
        if os.path.isdir(name) and len(filenames) == 1:
            # Recursive version using os.walk for all levels.
            if 'r' in optionlist:
                for dirpath, dirnames, files in os.walk(name):
                    for eachfile in files:
                        # Convert every file in that directory.
                        if eachfile.lower().endswith('.sjson'):
                            ConvertToSRT(eachfile, optionlist, dirpath)
                            filecount += 1
            # Non-recursive version breaks os.walk after the first level.
            else:
                topfiles = []
                for (dirpath, dirnames, files) in os.walk(name):
                    topfiles.extend(files)
                    break
                for eachfile in topfiles:
                    if eachfile.lower().endswith('.sjson'):
                        ConvertToSRT(eachfile, optionlist, dirpath)
                        filecount += 1

    print 'Converted ' + str(filecount) + ' SJSON files to SRT.'

if __name__ == "__main__":
    # this won't be run when imported
    json2srt(sys.argv)
