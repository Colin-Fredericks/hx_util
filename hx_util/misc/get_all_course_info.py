#!usr/bin/python3
# Reads in some basic course info from a set of edX .tar.gz files
# without expanding them, and writes it to a CSV file.

import os
import csv
import sys
import glob
import lxml.etree as ET
import tarfile
import argparse

# Read in a filenames from the command line.
if len(sys.argv) < 2:
    print("Usage: get_all_course_info.py <filename> <tarball>...")
    sys.exit(1)

argparser = argparse.ArgumentParser(
    description="Reads in some basic course info from a set of edX .tar.gz files without expanding them, and writes it to a CSV file."
)
argparser.add_argument("-o", "--output", help="The name of the CSV file to write.", default="course_info.csv")
argparser.add_argument("tarballs", nargs="+", help="The .tar.gz files to read.")
args = argparser.parse_args()

# Open the output file.
with open(args.output, "w") as f:
    writer = csv.writer(f)

    # Write out the header.
    writer.writerow(["Course Name", "Course ID", "Chapters"])

    # For each tarball, open it and look for course info files.
    for tarball in args.tarballs:
        print(tarball)
        # Check to make sure it's not an empty file.
        if os.path.getsize(tarball) == 0:
            print("Skipping empty file:", tarball)
            continue

        with tarfile.open(tarball, "r:gz") as tar:
            course_name = ""
            course_id = ""
            course_run = ""
            nickname = ""
            num_chapters = 0

            # Look for course info files.
            root_file = tar.getmember("course/course.xml")
            if not root_file:
                print("No course.xml found in", tarball)
                continue

            # Open the root file.
            f = tar.extractfile(root_file)

            root_tree = ET.parse(f)
            root_root = root_tree.getroot()

            # Get info from the root tag.
            nickname = root_root.get("course")
            course_run = root_root.get("url_name")
            course_id = nickname + "+" + course_run

            course_file = tar.getmember("course/course/" + course_run + ".xml")
            if not course_file:
                print("No course/" + course_run + ".xml found in", tarball)
                continue

            # Open the course file.
            g = tar.extractfile(course_file)
            course_tree = ET.parse(g)
            course_root = course_tree.getroot()

            # Get info from the course tag.
            course_name = course_root.get("display_name")
            # Count the number of <chapter> tags.
            chapters = course_root.findall("chapter")
            for c in chapters:
                # Open the chapter file so we can see if it's hidden.
                chapter_file = tar.getmember("course/chapter/" + c.get("url_name") + ".xml")
                if not chapter_file:
                    print("No course/chapter/" + c.get("url_name") + ".xml found in", tarball)
                    continue
                cf = tar.extractfile(chapter_file)
                chapter_tree = ET.parse(cf)
                chapter_root = chapter_tree.getroot()
                if("visible_to_staff_only" in chapter_root.keys()):
                    if chapter_root.get("visible_to_staff_only") == "true":
                        continue
                num_chapters += 1

            # Write out the info.
            writer.writerow([course_name, course_id, num_chapters])


# Say we're done and print the filename.
print("Course CSV created: ", args.output)
