HX-PY: HarvardX Standard Python
====================================

This project collects a large number of python tricks that have been used in various HX courses and puts them all in one place so that they're easier to implement.

Currently Working On...
-----------

Basically everything. This is currently a minimal example.


How to Implement HXJS in your course
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
  videoWatchGrader(ans, grading) - for video watch problems
  matchingAGrader(ans, right_answer, partial_credit, feedback) - for accessible matching problems
```

Currently Available Other Stuff
---------

```
simpleFunctions
  returnTrue() - just to make sure things are working
```