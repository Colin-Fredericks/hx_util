HX-PY Course Outline Maker
====================================

Do you want a linked outline of your course that also shows student grades and can be filtered to show specific concepts or materials? Sure, we all do! Here's how to do it. It'll take a few hours, mostly in the actual categorization of the course materials.

* First, get the `unicodecsv` folder, which you should download and keep in the same folder with the python scripts.
* Run `Make_Course_Outline.py` on your course export to create a TSV (tab-separated value) file with an outline of your course.
* Open that in Google Docs and edit it to indicate which items are in which categories. Just mark the appropriate cells with an x. This is the part that takes a while. Don't use Excel because Excel sucks at Unicode.
* Then export that as a new TSV file and run `Outline_to_HTML.py` on it to create a linked, filterable HTML outline that you can use as alternative navigation in your course.
* Upload `hx-collapse-nav.js` and `hx-collapse-nav.css` to your Files & Uploads folder to complete the process.
* If you want to show student scores next to each subsection, you should also upload `hx-grade-display.css` and `hx-grade-reader.js`, and add the following line of HTML (or something similar) near the top of your page: `<div id="progressbar">(Loading your scores <span class="fa fa-spinner fa-pulse fa-fw"></span>)</div>`
