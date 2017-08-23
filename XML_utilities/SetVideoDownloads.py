# import XML libraries
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom
import HTMLParser
import sys
import os

instructions = """
To use:
python SetVideoDownloads.py option path/to/video/folder

Set your option as...
  "true" to allow downloads of videos and transcripts for every video.
  "false" to disallow downloads of videos and transcripts for every video.
  "transcript" to allow only transcripts to be downloaded.
  "video" to allow only videos to be downloaded.
  "reset" to clear this attribute and let the edX defaults take over.

"""

# Get directory from command line argument
try:
    allowDownloads = sys.argv[1]
    directory = sys.argv[2]
except IndexError:
    # Probably the wrong number of arguments
    sys.exit(instructions)

# Walk through the problems folder
for dirpath, dirnames, filenames in os.walk(directory):
    for eachfile in filenames:

        # Get the XML for each file
        tree = ET.parse(os.path.join(dirpath, eachfile))
        root = tree.getroot()

        # Set the download_track and download_video values
        if allowDownloads.lower() == 'true':
            root.set('download_track', 'true')
            root.set('download_video', 'true')
        elif allowDownloads.lower() == 'false':
            root.set('download_track', 'false')
            root.set('download_video', 'false')
        elif allowDownloads.lower() == 'video':
            root.set('download_track', 'false')
            root.set('download_video', 'true')
        elif allowDownloads.lower() == 'transcript':
            root.set('download_track', 'true')
            root.set('download_video', 'false')
        elif allowDownloads.lower() == 'reset':
            try:
                del root.attrib['download_track']
                del root.attrib['download_video']
            except:
                pass
        else:
            sys.exit(instructions)

        # Save the file
        tree.write(os.path.join(dirpath, eachfile), encoding='UTF-8', xml_declaration=False)
