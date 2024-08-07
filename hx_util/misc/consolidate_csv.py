#!usr/bin/python3

import os
import csv
import sys

# Read in a filename from the command line.
if len(sys.argv) != 2:
    print("Usage: consolidate_csv.py <filename>")
    sys.exit(1)

filename = sys.argv[1]

# In every folder in the current directory, look for a file with the given name.
# If found, read it in and append it to a master file.
master = []
for root, dirs, files in os.walk("."):
    if filename in files:
        with open(os.path.join(root, filename), "r") as f:
            reader = csv.reader(f)
            for row in reader:
                master.append(row)

# De-duplicate the headers.
master = [master[0]] + [row for row in master if row != master[0]]

# Write out the master file.
with open(filename, "w") as f:
    writer = csv.writer(f)
    writer.writerows(master)