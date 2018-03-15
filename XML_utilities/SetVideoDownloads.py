# import XML libraries
import xml.etree.ElementTree as ET
import sys
import os
import argparse

instructions = """
To use:
python3 SetVideoDownloads.py choice path/to/video/folder -options

Set your choice as...
  "true" to allow downloads of videos and transcripts for every video.
  "false" to disallow downloads of videos and transcripts for every video.
  "transcript" to allow only transcripts to be downloaded.
  "video" to allow only videos to be downloaded.
  "reset" to clear this attribute and let the edX defaults take over.

Options:
  -h   Print this message and exit

Last update: March 15th 2018
"""

parser = argparse.ArgumentParser(usage=instructions, add_help=False)
parser.add_argument('-h', '--help', action='store_true')
parser.add_argument('choice', default='true')
parser.add_argument('directory', default='.')

args = parser.parse_args()
if args.help:
    sys.exit(instructions)
choice = args.choice.lower()

if not os.path.exists(args.directory):
    sys.exit('Directory not found: ' + args.directory)

numfiles = 0

# Walk through the problems folder
for dirpath, dirnames, filenames in os.walk(args.directory):
    for eachfile in filenames:

        # Get the XML for each file
        tree = ET.parse(os.path.join(dirpath, eachfile))
        root = tree.getroot()

        # If this isn't a video file, skip it.
        if root.tag != 'video':
            continue

        # Set the download_track and download_video values
        if choice == 'true':
            root.set('download_track', 'true')
            root.set('download_video', 'true')
        elif choice == 'false':
            root.set('download_track', 'false')
            root.set('download_video', 'false')
        elif choice == 'video':
            root.set('download_track', 'false')
            root.set('download_video', 'true')
        elif choice == 'transcript':
            root.set('download_track', 'true')
            root.set('download_video', 'false')
        elif choice == 'reset':
            try:
                del root.attrib['download_track']
                del root.attrib['download_video']
            except:
                pass
        else:
            sys.exit(instructions)

        # Save the file
        tree.write(os.path.join(dirpath, eachfile), encoding='UTF-8', xml_declaration=False)
        # Increment file counter
        numfiles += 1

if numfiles == 0:
    print('No files found - wrong or empty directory?')
else:
    print('Video download options set for ' + str(numfiles) + ' files.')
