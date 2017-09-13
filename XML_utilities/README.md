HX-PY XML Utilities
====================================

This is a bunch of batch tools to work directly with a course export (the file structure, not the tarball) or with .srt files. You can run `python filename.py` for each one to have it show a set of instructions, or just open the code with a text editor - the instructions are the first thing there.

* `SetMaxAttempts.py`, which sets the number of attempts automatically in every problem in a course.
* `SetShowAnswer.py`, which sets the showanswer value automatically (or removes it) in every problem in a course.
* `SetVideoDownloads.py`, which enables or disables video and/or transcript downloading for every video in a course.
* `Make_Course_Sheet.py`, which creates a spreadsheet showing which SRT file is for which video. It'll also make lists of other things in your course, such as problems or html components. This is also available as a Mac executable (download the zip file).
* `json2srt.py`, which converts the .srt.sjson files that edX uses into .srt files that more other things use.
* `SrtRename`, which copies all the SRT files that were in use in your course and then uses the sheet from Make_Course_Sheet to rename them to match the original video upload names. Useful for archiving.
* The **HX Archive Prep** tool, which is an executable that combines Make_Course_Sheet, json2srt, and SrtRename. Download the zip file for the Mac app, or get `HXArchive.py` for the all-in-one script.
* `SRTTimeShifter.py`, which moves the subtitles in an SRT file forward or backward a specified number of seconds.
