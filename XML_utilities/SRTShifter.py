import sys
import os
import csv

instructions = """
To use:
python SRTShifter.py seconds filename (options)

Takes the given subtitle file or files, in SRT format,
and shifts the times in each by the given number of seconds.
Use decimals, not frames (e.g. 2.5 seconds).

You can use negative times to shift backwards, if there's enough
padding at the start of the file.

Valid options:
  -c Copy. Makes a new file rather than shifting the old one.
  -h Help. Print this message.
"""

# Converts from miliseconds to hh:mm:ss,msec format
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
    elif int(msec) < 10: msec = '00' + str(msec)
    elif int(msec) < 100: msec = '0' + str(msec)
    if seconds == 0: seconds = '00'
    if seconds < 10: seconds = '0' + str(seconds)
    if minutes == 0: minutes = '00'
    if minutes < 10: minutes = '0' + str(minutes)
    if hours == 0: hours = '00'
    if hours < 10: hours = '0' + str(hours)

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

# Opens our input and output files, and maybe deletes the original.
def openFiles(name, seconds, optionList):
    # Open the existing SRT file.
    with open(name,'r') as inputFile:
        # Open a new file to work with.
        newname = name.rsplit('.srt',1)[0]
        newname += '_plus_' if seconds >= 0 else '_minus_'
        newname += str(seconds)
        newname += '.srt'
        with open(newname, 'wb') as outputFile:
            shiftTimes(inputFile, outputFile, seconds, optionList)

    # If we're not making copies, delete the old file.
    if 'c' not in optionList:
        os.remove(name)

    return

# Gets the next entry from our original SRT file
def getNextEntry(inFile, lastLine):
    entryData = {
        'start': 0,
        'end': 0,
        'index': 0,
        'text1': '',
        'text2': ''
    }

    for index, line in enumerate(inFile):
        print 'line - ' + line
        print 'last line - ' + lastLine

        # Loop down the file, storing lines, until you find ' --> '
        if ' --> ' in line:
            # The line before that is the index.
            entryData['index'] = int(lastLine)
            # That line is the timecode. Store it in miliseconds.
            entryData['start'] = HMSTomsec(line.split(' --> ')[0])
            entryData['end'] = HMSTomsec(line.split(' --> ')[1])
            # The next line is text1, and the one after is text2 or maybe blank.
            entryData['text1'] = unicode(inFile.next())
            # Watch out for the end of the file.
            try:
                entryData['text2'] = unicode(inFile.next())
            except StopIteration:
                pass

            # Once we've gotten our info, send it back.
            return entryData, lastLine

        lastLine = line

# Writes a standard SRT entry into our output files.
def writeEntry(outFile, entry):
    print entry
    outFile.write(unicode(entry['index'])+ '\n')
    outFile.write(unicode(msecToHMS(entry['start'])) + ' --> ' + unicode(msecToHMS(entry['end'])) + '\n')
    outFile.write(unicode(entry['text1']))
    if ''.join(entry['text2'].split()) is not '':
        outFile.write(unicode(entry['text2']))
    outFile.write(unicode('\n'))

# The core loop that calls the important stuff.
def shiftTimes(inFile, outFile, seconds, optionList):
    # If we're not shifting anything, just return.
    if seconds == 0:
        return

    # Loop through all our entries and write ones with corrected times.
    lastLine = ''
    while True:
        try:
            nextEntry, lastLine = getNextEntry(inFile, lastLine)
        except TypeError:
            # No last line to return.
            break

        # If we're out of entries, stop.
        if nextEntry is None:
            break
        if nextEntry['index'] == -1:
            break

        # For the first entry, if we're going positive:
        if seconds > 0 and nextEntry['index'] == 0:
            # Add a blank 'padding' entry at 0.
            blankEntry = {
                'start': 0,
                'end': seconds*1000,
                'index': 0,
                'text1': '',
                'text2': ''
            }
            print blankEntry
            writeEntry(outFile, blankEntry)

        # For the first entry, if we're going negative:
        elif seconds < 0 and nextEntry['index'] == 0:
            # Check to see if we can shrink the first entry enough.
            # If we have enough time, shrink the first entry back.
            # If not, stop and throw an error message.
            if nextEntry['end'] > abs(seconds*1000):
                nextEntry['end'] += seconds*1000
                writeEntry(outFile, nextEntry)
            else:
                print 'Cannot shift negative. First entry in file is ' + str(-seconds) + ' seconds or less.'
                return

        # For all other entries:
        # Write the adjusted entry and go on to the next one.
        else:
            nextEntry['start'] += seconds * 1000
            nextEntry['end'] += seconds * 1000
            writeEntry(outFile, nextEntry)

    return

# Takes in arguments and runs the shifter on each file.
def SRTShifter(args):
    # Get arguments
    if len(args) < 3:
        # Wrong number of arguments, probably
        sys.exit(instructions)

    # Get the number of seconds to shift by.
    seconds = args[1]
    try:
        seconds = float(seconds)
    except ValueError:
        # Probably fed arguments in wrong order.
        sys.exit(instructions)

    # Get file or directory from command line argument.
    # With wildcards we might get passed a lot of them.
    filenames = args[2:]
    # Get the options and make a list of them for easy reference.
    options = args[-1]

    # If the "options" match a file or folder name, those aren't options.
    if os.path.exists(options):
        options = ''
    # If they ARE options, then that last filename isn't a filename.
    else:
        del filenames[-1]

    optionList = []
    if 'c' in options: optionList.append('c')
    if 'h' in options: optionList.append('h')

    fileCount = 0

    # Convert every file we're passed.
    for name in filenames:
        # Make sure single files exist.
        assert os.path.exists(name), "File or directory not found: " + name

        # If it's just a file...
        if os.path.isfile(name):
            # Make sure this is an srt file (just check extension)
            if name.lower().endswith('.srt'):
                # Shift the times in that file
                openFiles(name, seconds, optionList)
                fileCount += 1

    plFiles = 'files' if fileCount > 1 else 'file'
    plSeconds = 'seconds' if seconds > 1 else 'second'
    print 'Shifted ' + str(fileCount) + ' ' + plFiles + ' by ' + str(seconds) + ' ' + plSeconds + '.'


if __name__ == "__main__":
    # This won't be run when the file is imported
    SRTShifter(sys.argv)
