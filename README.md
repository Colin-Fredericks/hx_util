HX-PY: HarvardX Standard Python
====================================

This project collects a large number of python tricks that have been used in various HX courses and puts them all in one place so that they're easier to implement.

This repo also has a few utility scripts for batch-work in course XML.

Currently Working On...
-----------

Nothing in particular.


How to Implement HXPY in your course
-----------

Put `python_lib.zip` in your Files & Uploads. Leave it zipped. Do *not* unzip it first.

You should be able to call functions from that library as demonstrated in the XML_Example file, basically like this:

```
from python_lib import HXFileName

HXFileName.nameOfFunction(options, moreoptions)
```


Currently Available Graders
---------

```
HXGraders
  qualtricsSurveyGrader(ans, options) - for grading Qualtrics surveys
  textResponseGrader(ans, options) - for text-logging problems
  videoWatchGrader(ans, grading) - for video watch problems
  matchingAGrader(ans, right_answer, partial_credit, feedback) - for accessible matching problems
  rangeGuessGrader(ans, options) - for range guessing problems
  getRangeGuesserParams(options) - also for range guessing problems, just not the grader
```

Currently Available Other Function
---------

```
simpleFunctions
  returnTrue() - just to make sure things are working

JSBridge
  insertJavascript() - just to make sure things are working
  JSAlert() - it console.logs whatever you put into it. Just a proof-of-concept.
```


Currently Available Tools
----------
* `SetMaxAttempts.py`, which sets the number of attempts automatically in every problem in a course.
* `SetShowAnswer.py`, which sets the showanswer value automatically (or removes it) in every problem in a course.
* `SetVideoDownloads.py`, which enables or disables video and/or transcript downloading for every video in a course.
* `Make_Course_Sheet.py`, which creates a spreadsheet showing which SRT file is for which video. It'll also make lists of other things in your course, such as links, problems, or html components. This is also available as a Mac executable (download the zip file). When listing links, this uses `GetWordLinks.py`.
* `json2srt.py`, which converts the .srt.sjson files that edX uses into .srt files that more other things use.
* `SrtRename`, which copies all the SRT files that were in use in your course and then uses the sheet from Make_Course_Sheet to rename them to match the original video upload names. Useful for archiving.
* The **HX Archive Prep** tool, which is an executable that combines Make_Course_Sheet, json2srt, and SrtRename. Download the zip file for the Mac app, or get `HXArchive.py` for the all-in-one script.
* The **HX Live Tool**, which will be run online.
* `SRTTimeShifter.py`, which moves the subtitles in an SRT file forward or backward a specified number of seconds.
* In the `outline_maker` folder you'll find a way to make a linked, filterable outline of your course that even pulls in student grades.


You can run `python filename.py` for each one to have it show a set of instructions.
