HX-PY: HarvardX Standard Python
====================================

This project collects a large number of python tricks that have been used in various HX courses and puts them all in one place so that they're easier to implement.

This repo also has a few utility scripts for batch-work in course XML.

Currently Working On...
-----------

A script that creates a spreadsheet showing which SRT file is for which video.


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
  textResponseGrader(ans) - for text-logging problems
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
* `Make_Video_SRT.py`, which creates a spreadsheet showing which SRT file is for which video. Currently under development.

You can run `python filename.py` to have each one show a set of instructions.
