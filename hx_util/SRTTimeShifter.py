import sys
import os
import argparse
from glob import glob

instructions = """
To use:
python3 SRTTimeShifter.py filename seconds (options)

Takes the given subtitle file or files, in SRT format,
and shifts the times in each by the given number of seconds.

For time, use decimals, not frames (e.g. 2.5 seconds).
You can use negative times to shift backwards, if there's enough
padding at the start of the file.

Valid options:
  -o Overwrite. Overwrites the old file rather than making a new one.
  -h Help. Print this message.

Last update: March 15th 2018
"""

# Converts from miliseconds to hh:mm:ss,msec format
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

# Converts from hh:mm:ss,msec format to miliseconds
def HMSTomsec(timestring):
    # Get hours, minutes, and seconds as individual strings
    hours, minutes, seconds = timestring.split(':')

    # Convert the comma in seconds to a decimal
    seconds = seconds.replace(',','.')

    # Convert times to numbers
    hours = int(hours)
    minutes = int(minutes)
    seconds = float(seconds)

    # Convert everything to miliseconds and add them all up
    msec = int(seconds * 1000) + minutes * 60000 + hours * 3600000

    # Send back an integer
    return msec

# Opens our input and output files.
def openFiles(name, seconds, args):
    completed = False

    # Open the existing SRT file.
    with open(name,'r') as inputFile:
        # Open a new file to work with.
        newname = name + '.new'
        with open(newname, 'w') as outputFile:
            # With the files open, shift the times.
            completed = shiftTimes(inputFile, outputFile, name, seconds, args)

        # If we fail, we shouldn't leave a random file lying around.
        if not completed: os.remove(newname)
        return completed, newname

    # If we got here, we couldn't open the file I guess.
    return False, 'error.srt'

# Gets a list of dicts with all the entries from our original SRT file
def getSRTEntries(inFile):

    SRTEntries = []
    lastLine = ''

    # Loop down the file, storing lines, until you find ' --> '
    for index, line in enumerate(inFile):
        entryData = {}

        if ' --> ' in line:
            # The line before that is the index.
            entryData['index'] = int(lastLine)
            # That line is the timecode. Store it in miliseconds.
            entryData['start'] = HMSTomsec(line.split(' --> ')[0])
            entryData['end'] = HMSTomsec(line.split(' --> ')[1])
            # Watch out for the end of the file.
            try:
                # The next line is text1, and the one after is text2 or maybe blank.
                entryData['text1'] = str(inFile.readline())
                # If text1 is blank, move on.
                if entryData['text1'].strip() == '':
                    entryData['text2'] = ''
                    SRTEntries.append(entryData)
                    continue
                entryData['text2'] = str(inFile.readline())
            except StopIteration:
                pass

            # Once we've gotten our info, add it to the list.
            SRTEntries.append(entryData)

        lastLine = line

    return SRTEntries

# Writes a standard SRT entry into our output files.
def writeEntry(outFile, entry, index):
    outFile.write(str(index)+ '\n')
    outFile.write(str(msecToHMS(entry['start'])) + ' --> ' + str(msecToHMS(entry['end'])) + '\n')
    outFile.write(str(entry['text1']))
    if ''.join(entry['text2'].split()) is not '':
        outFile.write(str(entry['text2']))
    outFile.write('\n')

# The core loop that calls the important stuff.
def shiftTimes(inFile, outFile, name, seconds, args):

    # Get a list of all the entries.
    SRTEntries = getSRTEntries(inFile)

    removeEntry = False
    blankEntry = None

    # Go through the list and adjust times.
    for i, entry in enumerate(SRTEntries):

        # If we're going positive:
        if seconds > 0 and i==0:

            # If there's already a blank 'padding' entry, extend it.
            if entry['text1'].strip() == '':
                entry['start'] = 0
                entry['end'] += seconds * 1000
            # If not, add a blank entry at 0.
            else:
                blankEntry = {
                    'start': 0,
                    'end': SRTEntries[i]['start'] + seconds * 1000,
                    'index': 0,
                    'text1': '',
                    'text2': ''
                }

                # Adjust the existing first entry.
                entry['start'] += seconds * 1000
                entry['end'] += seconds * 1000

        # If we're going negative:
        elif seconds < 0 and i==0:
            # Check to see if we can shrink the first entry enough.
            # If we have enough time, shrink the first entry back.
            # If not, stop and throw an error message.
            # print('start: ' + str(entry['start']/1000.0))
            # print('end: ' + str(entry['end']/1000.0))
            # print(entry['start'] > abs(seconds*1000))
            # print(entry['end'] > abs(seconds*1000))

            # If the first entry starts at or after our time, we're all good.
            if entry['start'] > abs(seconds*1000):
                entry['start'] += seconds * 1000
                entry['end'] += seconds * 1000
            elif entry['end'] == abs(seconds*1000):
                removeEntry = True
            # We might still be good if our first entry is blank. We can shrink it back.
            elif entry['end'] > abs(seconds*1000) and entry['text1'].strip() == '':
                entry['end'] += seconds*1000
            # But if not, we can't change this file.
            else:
                print('Cannot shift ' + name + '. First subtitle is before ' + str(-seconds) + ' seconds.')
                return False

        if i>0:
            entry['start'] += seconds * 1000
            entry['end'] += seconds * 1000

    if blankEntry: SRTEntries.insert(0, blankEntry)
    if removeEntry: del SRTEntries[0]

    # Write the file.
    for i, entry in enumerate(SRTEntries):
        writeEntry(outFile, entry, i)

    return True

# Takes in arguments and runs the shifter on each file.
def SRTTimeShifter(args):

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument('--help', '-h', action='store_true')
    parser.add_argument('-o', action='store_true')
    parser.add_argument('file_names', nargs='*')
    parser.add_argument('seconds', action='store')

    args = parser.parse_args(args)

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob(arg)

    # If "seconds" is not a number, it's probably in the wrong place.
    try:
        seconds = float(args.seconds)
    except ValueError:
        # Probably fed arguments in wrong order.
        sys.exit(instructions)

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit('No file or directory found by that name.')

    if args.help: sys.exit(instructions)

    fileCount = 0

    # If we're not shifting anything, just return.
    if seconds == 0:
        print('Zero second shift - no files changed.')
        return False

    # Convert every file we're passed.
    for name in file_names:
        # Make sure single files exist.
        if not os.path.exists(name):
            print('File or directory not found: ' + name)
            return

        # If it's just a file...
        if os.path.isfile(name):
            # Make sure this is an srt file (just check extension)
            if name.lower().endswith('.srt'):
                # Open that file and shift the times in that file
                completed, newname = openFiles(name, seconds, args)
                if completed:
                    # If we're not copying files, clean up the original.
                    if args.o:
                        os.remove(name)
                    else:
                        os.rename(name, name + '.old')
                    os.rename(newname, name)
                    fileCount += 1

    # Finish by saying how many files we shifted.
    if fileCount > 0:
        plFiles = 'file' if fileCount == 1 else 'files'
        plSeconds = 'second' if seconds == 1 else 'seconds'
        print('Shifted ' + str(fileCount) + ' ' + plFiles + ' by ' + str(seconds) + ' ' + plSeconds + '.')


if __name__ == "__main__":
    # This won't be run when the file is imported
    SRTTimeShifter(sys.argv)
