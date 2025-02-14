HX-PY XML Utilities
====================================


This is a bunch of batch tools to work directly with a course export (the file structure, not the tarball) or with .srt files.

Install and Use
---------------

    # clone this repo
    $> git clone https://github.com/Colin-Fredericks/hx_util.git

    # create a virtualenv and activate it
    $> python3 -m venv hxutil
    $> source hxutil/bin/activate
    (hxutil) $>

    # install requirements
    (hxutil) $> cd hx_util
    (hxutil) $> pip install -r requirements.txt

    # install hx_util
    (hxutil) $> pip install .

    # to generate all possible goodies
    (hxutil) $> hx_util /path/to/the/untarred/course_export


Readme previous to packaging hx_util, for reference
---------------------------------------------------

This is a bunch of batch tools to work directly with a course export (the file structure, not the tarball) or with .srt files. You can run `python3 filename.py` for each one to have it show a set of instructions, or just open the code with a text editor - the instructions are the first thing there.

Because python's built-in xml parser has trouble with namespaces and xpaths, some XML parsing is done with BeautifulSoup instead. It's included in this folder as `bs4`. For better unicode handling, `unicodecsv` is also included. BeautifulSoup requires `lxml` for XML parsing, so you'll need to install that, probably via `sudo pip3 install lxml`.

* `Make_Course_Sheet.py`, which creates a spreadsheet showing which SRT file is for which video. It'll also make lists of other things in your course, such as problems or html components.
 * You can also run this with the `-links` argument to get a list of all the links in your course, including those in .html, .xml, .docx, .pptx, and .xlsx files in your Files & Uploads. If you do this, you will want to grab the bs4 and unicodecsv folders, and you might want `GetWordLinks.py` (or another appropriate item) to handle the word docs.
 * You can also run this with the `-alttext` argument to get a list of all the images in your course and their alt text. That cell will be blank if the alt attribute is blank, and will say "No alt attribute" if there is no alt attribute.
* `json2srt.py`, which converts the .srt.sjson files that edX uses into .srt files that more other things use.
* `SrtRename`, which copies all the SRT files that were in use in your course and then uses the sheet from Make_Course_Sheet to rename them to match the original video upload names. Useful for archiving.
* `SRTTimeShifter.py`, which moves the subtitles in an SRT file forward or backward a specified number of seconds.


If you're looking for `outline_maker`, `SetMaxAttempts.py`, and other course-run rools, they're now in [hx-xml](https://github.com/Colin-Fredericks/hx-xml). `PrepAdaptiveProblems.py` has been moved to [hx-adaptive](https://github.com/Colin-Fredericks/hx-adaptive).

 ### In Progress
 * Improving the XML parsing to handle components declared inline.
