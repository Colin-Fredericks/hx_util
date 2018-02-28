HX-PY Course Link Checker
====================================

Development on this project has halted.

This is an unfinished project. The goal was to be able to check the links from an edX course export automatically, but it turns out that it's not that easy to tell (without some false results) whether a set of hyperlinks all have working destinations. Instead, I added the -link functionality to `Make_Course_Sheet.py` and we can get a spreadsheet full of links to check manually. It's not quite what I wanted, but it's still faster than going through by hand.

-----

When rerunning a course, download the course export, unzip it, and run this script on it as follows:

`python linkcheck.py path/to/course/folder`

Requires [BeautifulSoup 4](https://www.crummy.com/software/BeautifulSoup/) (which is included this folder, courtesy of the MIT License).
Requires the [Requests](http://docs.python-requests.org/en/latest/user/install/) library, which can be installed via `sudo pip install requests`.
