HX Adaptive Problem Prep
====================================

Instructions for use:

1. Download PrepAdaptiveProblems.py and the unicodecsv folder. Put them in the same folder.
2. Get a CSV file of your adaptive assignments, similar to Problem_Table_Sample.csv, so that they all have locations/filenames and content groupings listed.
3. Put all your adaptive problems in a single folder.
4. Make a copy of upload_course_template.zip and unzip it. This makes a blank (or nearly blank) edX course that's complete enough for use in this situation.
5. Run the following command:

`python PrepAdaptiveProblems.py path/to/problem_table.csv path/to/problem_folder (options)`

6. Tar and gzip the resulting `upload_course` folder. You can use the command line or the included Automator application (runs on macs).

Done! You can upload the resulting to a blank edX course (or an existing one, if you're ok with overwriting), or you can hand it off to someone as a single file now.

If you want to see the available options, run the script without any arguments, or with -h.
