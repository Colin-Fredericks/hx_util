HX-PY XML Utilities
====================================

This is a bunch of batch tools to work directly with a course export (the file structure, not the tarball) or with .srt files. You can run `python3 filename.py` for each one to have it show a set of instructions, or just open the code with a text editor - the instructions are the first thing there.

Because python's built-in xml parser has trouble with namespaces and xpaths, some XML parsing is done with BeautifulSoup instead. It's included in this folder as `bs4`. For better unicode handling, `unicodecsv` is also included. BeautifulSoup requires `lxml` for XML parsing, so you'll need to install that, probably via `sudo pip3 install lxml`.

* `SetMaxAttempts.py`, which sets the number of attempts automatically in every problem in a course.
* `SetShowAnswer.py`, which sets the showanswer value automatically (or removes it) in every problem in a course.
* `SetVideoDownloads.py`, which enables or disables video and/or transcript downloading for every video in a course.
* `Make_Course_Sheet.py`, which creates a spreadsheet showing which SRT file is for which video. It'll also make lists of other things in your course, such as problems or html components. This is also available as a Mac executable (download the zip file).
 * You can also run this with the `-links` argument to get a list of all the links in your course, including those in .html, .xml, and .docx files in your Files & Uploads. If you do this, you will want to grab the bs4 and unicodecsv folders, and you might want `GetWordLinks.py` to handle the word docs.
* `Make_Link_Spreadsheet.zip`, which contains a Mac executable that runs `Make_Course_Sheet.py` with `GetWordLinks.py` to create a csv of all the links in the course for quick checking. This executable is behind the rest of them because of some sort of incompatibility between python3, BeautifulSoup, and Platypus that keeps bs4 from opening files with unicode characters. Trying to figure out a good way to handle this without having a thousand try/except clauses.
* `json2srt.py`, which converts the .srt.sjson files that edX uses into .srt files that more other things use.
* `SrtRename`, which copies all the SRT files that were in use in your course and then uses the sheet from Make_Course_Sheet to rename them to match the original video upload names. Useful for archiving.
* The **HX Archive Prep** tool, which is an executable that combines Make_Course_Sheet, json2srt, and SrtRename. Download the zip file for the Mac app, or get `HXArchive.py` for the all-in-one script.
* `SRTTimeShifter.py`, which moves the subtitles in an SRT file forward or backward a specified number of seconds.
* `PrepAdaptiveProblems.py` makes a course container structure for some of our adaptive assessment implementations. You probably don't need or want this tool; it's an in-house thing.
* In the `outline_maker` folder there are a set of related items:
 * The `unicodecsv` package, which you should download and keep in the same folder with the python scripts.
 * Run `Make_Course_Outline.py` on your course export to create a TSV file with an outline of your course.
 * Open that in Google Docs and edit it to indicate which items are in which categories. Just mark the appropriate cells with an x.
 * Then save that as a new TSV file and run `Outline_to_HTML.py` on it to create a linked, filterable HTML outline that you can use as alternative navigation in your course.
 * Upload `hx-collapse-nav.js` and `hx-collapse-nav.css` to your Files & Uploads folder to complete the process.
 * If you want to show student scores next to each subsection, you should also upload `hx-grade-display.css` and `hx-grade-reader.js`, and add the following line of HTML (or something similar) near the top of your page: `<div id="progressbar">(Loading your scores <span class="fa fa-spinner fa-pulse fa-fw"></span>)</div>`

 ### In Progress
 * Adding an XLSX parser
 * Considering adding a PDF parser, perhaps using https://github.com/metachris/pdfx
