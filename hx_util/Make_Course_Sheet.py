import sys

if sys.version_info <= (3, 0):
    sys.exit("I am a Python 3 script. Run me with python3.")

import os
import argparse
from bs4 import BeautifulSoup
import lxml
import glob
import json
import unicodecsv as csv  # https://pypi.python.org/pypi/unicodecsv/0.14.1

try:
    from hx_util import GetWordLinks
except:
    print("Cannot find GetWordLinks.py, skipping links in .docx files.")
try:
    from hx_util import GetExcelLinks
except:
    print("Cannot find GetExcelLinks.py, skipping links in .xlsx files.")
try:
    from hx_util import GetPPTLinks
except:
    print("Cannot find GetPPTLinks.py, skipping links in .pptx files.")
try:
    from hx_util import GetPDFLinks
except:
    print("Cannot find GetPDFLinks.py, skipping links in .pdf files.")


instructions = (
    """
To use:
python3 Make_Course_Sheet.py path/to/course.xml (options)

Run this on a course folder, or a course.xml file inside an edX course folder (from export).
You will get a Tab-Separated Value file that you should open with Google Drive,
which shows the location of each video and the srt filename for that video.

You can specify the following options:
    -problems  Includes problems AND problem XML instead of videos
    -html      Includes just HTML components
    -video     Forces inclusion of video with html or problems
    -all       Includes most components, including problem,
               html, video, discussion, poll, etc.
    -links     Lists all links in the course.
               Not compatible with above options.
    -alttext   Lists all images with their alt text.
               Not compatible with above options.
    -o         Sets the output filename to the next argument.

This script may fail on courses with empty containers.

Last update: May 14th 2025, Version """
    + sys.modules[__package__].__version__
)


# Many of these are being skipped because they're currently expressed in inline XML
# rather than having their own unique folder in the course export.
# These will be moved out as we improve the parsing.
skip_tags = [
    "annotatable",  # This is the older, deprecated annotation component.
    "google-document",
    "oppia",
    "openassessment",  # This is the older, deprecated ORA.
    "poll_question",  # This is the older, deprecated poll component.
    "problem-builder",
    "recommender",
    "step-builder",
    "wiki",
]

# Canonical leaf node. Only for copying.
canon_leaf = {
    "type": "",
    "name": "",
    "url": "",
    "filename": "",
    "links": [],
    "images": [],
    "sub": [],
}


# Converts from seconds to hh:mm:ss,msec format
# Used to convert duration
def secToHMS(time):
    # Round it to an integer.
    time = int(round(float(time), 0))

    # Downconvert through hours.
    seconds = int(time % 60)
    time -= seconds
    minutes = int((time / 60) % 60)
    time -= minutes * 60
    hours = int((time / 3600) % 24)

    # Make sure we get enough zeroes.
    if int(seconds) == 0:
        seconds = "00"
    elif int(seconds) < 10:
        seconds = "0" + str(seconds)
    if int(minutes) == 0:
        minutes = "00"
    elif int(minutes) < 10:
        minutes = "0" + str(minutes)
    if int(hours) == 0:
        hours = "00"
    if int(hours) < 10:
        hours = "0" + str(hours)

    # Send back a string
    return str(hours) + ":" + str(minutes) + ":" + str(seconds)


# Adds notes to links based on file type
def describeLinkData(newlink):
    image_types = [
        ".png",
        ".gif",
        ".jpg",
        ".jpeg",
        ".svg",
        ".tiff",
        ".tif",
        ".bmp",
        ".jp2",
        ".jif",
        ".pict",
        ".webp",
    ]

    if newlink["href"].endswith(tuple(image_types)):
        newlink["text"] += " (image link)"
    if newlink["href"].endswith(".pdf"):
        newlink["text"] += " (PDF file)"
    if newlink["href"].endswith(".ps"):
        newlink["text"] += " (PostScript file)"
    if newlink["href"].endswith(".zip"):
        newlink["text"] += " (zip file)"
    if newlink["href"].endswith(".tar.gz"):
        newlink["text"] += " (tarred gzip file)"
    if newlink["href"].endswith(".gz"):
        newlink["text"] += " (gzip file)"
    return newlink


# get list of links from HTML pages, with href and link text
# "soup" is a BeautifulSoup object
def getHTMLLinks(soup):
    links = []

    all_links = soup.find_all(["a", "iframe"])

    for link in all_links:
        if link.has_attr("href"):
            # It's a link and not just an anchor.
            if len(link.contents) > 0:
                link_text = "".join(link.find_all(string=True))
            else:
                link_text = ""
            links.append({"href": link.get("href"), "text": link_text})

        if link.has_attr("src"):
            # It's an iframe.
            links.append({"href": link.get("src"), "text": "(iframe)"})

    betterlinks = [describeLinkData(x) for x in links]
    return betterlinks


# get list of all images from HTML pages, with alt text
# "soup" is a BeautifulSoup object
def getAltText(soup):
    image_list = []

    all_images = soup.find_all(["img", "drag_and_drop_input"])
    temp_alt = "No alt attribute"
    temp_src = "No source attribute"

    for img in all_images:
        if img.has_attr("img"):
            # This is a version-1 drag-and-drop problem.
            temp_src = "¡Drag-and-drop v1 problem, replace!"
            temp_alt = "¡Drag-and-drop v1 problem, replace!"
        elif img.has_attr("src"):
            temp_src = img.get("src")
            if img.has_attr("alt"):
                temp_alt = img.get("alt")
        image_list.append({"src": temp_src, "alt": temp_alt})

    return image_list


# Gets alt text that isn't in the courseware
def getAuxAltText(rootFileDir):
    # Folders to check:
    aux_folders = ["tabs", "info", "static"]
    aux_paths = [os.path.join(rootFileDir, x) for x in aux_folders]
    aux_images = []

    for folder in aux_paths:
        if os.path.isdir(folder):
            folder_temp = {"type": "", "name": "", "url": "", "contents": []}

            # Placing all of these folders at the "chapter" level.
            for f in os.listdir(folder):
                file_temp = canon_leaf.copy()
                file_temp["filename"] = os.path.join(os.path.basename(folder), f)
                # Use the file's extension as its type.
                file_temp["type"] = os.path.splitext(f)[1][1:]
                # Remove the leftmost character
                file_temp["name"] = f
                file_temp["url"] = f

                if file_temp["type"] == "html" or file_temp["type"] == "htm":
                    try:
                        soup = BeautifulSoup(
                            open(os.path.join(folder, f), encoding="utf8"), "html.parser"
                        )
                    except UnicodeDecodeError:
                        # If we have a Unicode error, skip the file.
                        print(
                            "Unicode error in file "
                            + os.path.join(folder, f)
                            + ", skipping."
                        )
                        continue
                    file_temp["images"] = getAltText(soup)
                    folder_temp["contents"].append(file_temp)
                elif file_temp["type"] == "xml":
                    try:
                        tree = lxml.etree.parse(folder + "/" + f)
                    except lxml.etree.XMLSyntaxError:
                        # If we have broken XML, tell us and skip the file.
                        print("Broken XML in file " + folder + "/" + f + ", skipping.")
                        continue
                    soup = BeautifulSoup(
                        open(os.path.join(folder, f), encoding="utf8"), "lxml"
                    )
                    file_temp["images"] = getAltText(soup)
                    folder_temp["contents"].append(file_temp)

            folder_temp["chapter"] = os.path.basename(folder)
            folder_temp["name"] = os.path.basename(folder)
            aux_images.append(folder_temp)

    return aux_images


# Gets links that aren't in the courseware
def getAuxLinks(rootFileDir):
    # Folders to check:
    aux_folders = ["tabs", "info", "static"]
    aux_paths = [os.path.join(rootFileDir, x) for x in aux_folders]
    aux_links = []

    # Ignore any links from tabs that aren't currently in use.
    # Get the list of tabs from all policies/???/policy.json files
    policy_files = []
    tab_files = []
    policy_folders = [
        os.path.join(rootFileDir, "policies", x)
        for x in os.listdir(os.path.join(rootFileDir, "policies"))
    ]
    for folder in policy_folders:
        if os.path.isdir(folder):
            for f in os.listdir(folder):
                if f == "policy.json":
                    policy_files.append(os.path.join(folder, f))

    for f in policy_files:
        with open(f, "r") as policy:
            policy_data = json.load(policy)
            # Strip off the outer object wrapper.
            policy_data = policy_data[list(policy_data.keys())[0]]
            # If there's a URL slug, add it to the list of tabs.
            for tab in policy_data["tabs"]:
                if "url_slug" in tab:
                    tab_files.append(tab["url_slug"] + ".html")

    print("Tabs found in policy files: " + str(tab_files))

    for folder in aux_paths:
        if os.path.isdir(folder):
            folder_temp = {"type": "", "name": "", "url": "", "contents": []}

            for f in os.listdir(folder):
                file_temp = canon_leaf.copy()
                file_temp["name"] = f
                file_temp["url"] = f
                file_temp["filename"] = os.path.join(os.path.basename(folder), f)
                # Use the file's extension as its type.
                file_temp["type"] = os.path.splitext(f)[1][1:]

                if file_temp["type"] == "html" or file_temp["type"] == "htm":
                    if "tabs" in folder:
                        # Skip tabs that aren't in use.
                        if os.path.basename(f) not in tab_files:
                            continue
                    try:
                        soup = BeautifulSoup(
                            open(os.path.join(folder, f), encoding="utf8"), "html.parser"
                        )
                    except UnicodeDecodeError:
                        # If we have a Unicode error, skip the file.
                        print(
                            "Unicode error in file "
                            + os.path.join(folder, f)
                            + ", skipping."
                        )
                        continue
                    file_temp["links"] = getHTMLLinks(soup)
                    folder_temp["contents"].append(file_temp)
                if file_temp["type"] == "xml":
                    try:
                        tree = lxml.etree.parse(folder + "/" + f)
                    except lxml.etree.XMLSyntaxError:
                        # If we have broken XML, tell us and skip the file.
                        print("Broken XML in file " + folder + "/" + f + ", skipping.")
                        continue
                    root = tree.getroot()
                    soup = BeautifulSoup(
                        open(os.path.join(folder, f), encoding="utf8"), "lxml"
                    )
                    file_temp["links"] = getHTMLLinks(soup)
                    folder_temp["contents"].append(file_temp)
                if file_temp["type"] == "docx":
                    file_temp["links"] = GetWordLinks.getWordLinks(
                        [os.path.join(folder, f), "-l"]
                    )
                    folder_temp["contents"].append(file_temp)
                if file_temp["type"] == "xlsx":
                    file_temp["links"] = GetExcelLinks.getExcelLinks(
                        [os.path.join(folder, f), "-l"]
                    )
                    folder_temp["contents"].append(file_temp)
                if file_temp["type"] == "pptx":
                    file_temp["links"] = GetPPTLinks.getPPTLinks(
                        [os.path.join(folder, f), "-l"]
                    )
                    folder_temp["contents"].append(file_temp)
                if file_temp["type"] == "pdf":
                    file_temp["links"] = GetPDFLinks.getPDFLinks(
                        [os.path.join(folder, f), "-l"]
                    )
                    folder_temp["contents"].append(file_temp)

            # Placing all of these folders at the "chapter" level.
            folder_temp["chapter"] = os.path.basename(folder)
            folder_temp["name"] = os.path.basename(folder)
            aux_links.append(folder_temp)

    return aux_links


# Always gets the display name.
# For video and problem files, gets other info too
def getComponentInfo(folder, filename, child, args):
    # Try to open file.
    try:
        tree = lxml.etree.parse(folder + "/" + filename + ".xml")
        root = tree.getroot()
    except OSError:
        # If we can't get a file, try to traverse inline XML.
        root = child

    temp = {
        "type": root.tag,
        "name": "",
        # space for other info
    }

    # get display_name or use placeholder
    if "display_name" in root.attrib:
        temp["name"] = root.attrib["display_name"]
    else:
        temp["name"] = root.tag

    # get video information
    if root.tag == "video" and args.video:
        # List of subscripts because multiple languages.
        temp["sub"] = []

        # Old-style course exports have non-blank 'sub' attributes.
        if "sub" in root.attrib:
            if root.attrib["sub"] != "":
                temp["sub"] = ["subs_" + root.attrib["sub"] + ".srt.sjson"]

        # New-style course exports (Aug 15 2018) have a different hierarchy.
        # Use this preferentially over the old-style formatting.
        for va in root.iter("video_asset"):
            for trs in va.iter("transcripts"):
                for transcript in trs.iter("transcript"):
                    temp["sub"].append(
                        root.attrib["edx_video_id"]
                        + "-"
                        + transcript.attrib["language_code"]
                        + ".srt"
                    )
            # The download URL looks a lot like the cloudfront URL.
            # Guess we'll find out if we have a lot of courses without that.
            for ev in va.iter("encoded_video"):
                if ev.attrib["profile"] == "desktop_mp4":
                    cloudfront_url = ev.attrib["url"]
                    cloudfront_filename = cloudfront_url.split(".net")[-1]
                    temp["download_url"] = "https://edx-video.net" + cloudfront_filename

        if len(temp["sub"]) == 0:
            temp["sub"] = ["No subtitles found."]

        if "youtube_id_1_0" in root.attrib:
            temp["youtube"] = root.attrib["youtube_id_1_0"]
        elif "youtube" in root.attrib:
            # slice to remove the '1.00:' from the start of the ID
            temp["youtube"] = root.attrib["youtube"][5:]
        else:
            temp["youtube"] = "No YouTube ID found."

        if "edx_video_id" in root.attrib:
            temp["edx_video_id"] = root.attrib["edx_video_id"]

        # We need our original uploaded filename.
        # It's not present in the old XML. :(
        # In new XML, it's in a video_asset tag.
        found_video_asset = False
        for child in root:
            if child.tag == "video_asset":
                if "client_video_id" in child.attrib:
                    found_video_asset = True
                    src = child.attrib["client_video_id"]
                    # Stripping the host and folders
                    src = src[src.rfind("/") + 1 :]
                    # Stripping the extension, if there is one.
                    if src.rfind(".") > 0:
                        src = src[: src.rfind(".")]
                    if src == "":
                        temp["upload_name"] = (
                            "No_Upload_Name_" + root.attrib["url_name"]
                        )
                    temp["upload_name"] = src

                if "duration" in child.attrib:
                    # Get duration in seconds
                    duration = child.attrib["duration"]
                    temp["duration"] = secToHMS(duration)

        # Need a placeholder if there's no video_asset tag or if it's less than informative.
        if not found_video_asset:
            temp["upload_name"] = "No_Upload_Name_" + root.attrib["url_name"]
            temp["duration"] = "unknown"

    # get problem information
    if root.tag == "problem":
        if "rerandomize" in root.attrib:
            temp["rerandomize"] = root.attrib["rerandomize"]
        if "show_reset_button" in root.attrib:
            temp["show_reset_button"] = root.attrib["show_reset_button"]
        if root.text is not None:
            temp["inner_xml"] = root.text + "".join(
                str(lxml.etree.tostring(e)) for e in root
            )
            soup = BeautifulSoup(temp["inner_xml"], "lxml")
            temp["links"] = getHTMLLinks(soup)
            temp["images"] = getAltText(soup)
        else:
            temp["inner_xml"] = "No XML."

    # Right now all we get from HTML is links and images.
    if root.tag == "html":
        if args.links or args.alttext:
            # Most of the time our XML will just point to a separate HTML file.
            # In those cases, go open that file and get the links from it.
            if root.text is None:
                innerfilepath = os.path.join(
                    os.path.dirname(folder), "html", (root.attrib["filename"] + ".html")
                )
                soup = BeautifulSoup(
                    open(innerfilepath, encoding="utf8"), "html.parser"
                )
            # If it's declared inline, just get the links right away.
            else:
                soup = BeautifulSoup("".join(root.itertext()), "html.parser")
            if args.links:
                temp["links"] = getHTMLLinks(soup)
            if args.alttext:
                temp["images"] = getAltText(soup)

    # special handlers for other xml:
    if root.tag == "drag-and-drop-v2":
        temp["links"] = []
        temp["images"] = [
            {
                "src": "Drag-and-drop problem (v2)",
                "alt": "¡Check manually for alt text!",
            }
        ]

    # Label all of them as components regardless of type.
    temp["component"] = temp["name"]

    return {"contents": temp, "parent_name": temp["name"]}


# Recursion function for outline-declared xml files
def drillDown(folder, filename, root, args):
    # Try to open file.
    try:
        tree = lxml.etree.parse(os.path.join(folder, (filename + ".xml")))
        root = tree.getroot()
    except IOError:
        # If we can't get a file, try to traverse inline XML.
        ddinfo = getXMLInfo(folder, root, args)
        if ddinfo:
            return ddinfo
        else:
            print(
                "Possible missing file or empty XML element: "
                + os.path.join(folder, (filename + ".xml"))
            )
            return {"contents": [], "parent_name": "", "found_file": False}

    return getXMLInfo(folder, root, args)


def getXMLInfo(folder, root, args):
    # We need lists of container nodes and leaf nodes so we can tell
    # whether we have to do more recursion.
    leaf_nodes = [
        "discussion",
        "done",
        "drag-and-drop-v2",
        "html",
        "imageannotation",
        "library_content",
        "lti",
        "lti_consumer",
        "pb-dashboard",  # This is currently unique to HarvardX DataWise
        "poll",
        "problem",
        "survey",
        "textannotation",
        "ubcpi",
        "video",
        "videoannotation",
        "word_cloud",
    ]
    branch_nodes = [
        "course",
        "chapter",
        "sequential",
        "vertical",
        "split_test",
        "conditional",
    ]

    contents = []

    # Some items are created without a display name; use their tag name instead.
    if "display_name" in root.attrib:
        display_name = root.attrib["display_name"]
    else:
        display_name = root.tag

    for index, child in enumerate(root):
        temp = {
            "index": index,
            "type": child.tag,
            "name": "",
            "url": "",
            "filename": "",
            "contents": [],
            "links": [],
            "images": [],
            "sub": [],
        }

        # get display_name or use placeholder
        if "display_name" in child.attrib:
            temp["name"] = child.attrib["display_name"]
        else:
            temp["name"] = child.tag + str(index)
            temp["tempname"] = True

        # get url_name but there are no placeholders
        # Note that even some inline XML have url_names.
        if "url_name" in child.attrib:
            temp["url"] = child.attrib["url_name"]
            temp["filename"] = child.attrib["url_name"]
        else:
            temp["url"] = None

        # In the future: check to see whether this child is a pointer tag or inline XML.
        nextFile = os.path.join(os.path.dirname(folder), child.tag)
        if child.tag in branch_nodes:
            child_info = drillDown(nextFile, temp["url"], child, args)
            temp["contents"] = child_info["contents"]
        elif child.tag in leaf_nodes:
            child_info = getComponentInfo(nextFile, temp["url"], child, args)
            # For leaf nodes, add item info to the dict
            # instead of adding a new contents entry
            temp.update(child_info["contents"])
            del temp["contents"]
        elif child.tag in skip_tags:
            child_info = {"contents": False, "parent_name": child.tag}
            del temp["contents"]
        else:
            sys.exit("New tag type found: " + child.tag)

        # If the display name was temporary, replace it.
        if "tempname" in temp:
            temp["name"] = child_info["parent_name"]
            del temp["tempname"]

        # We need not only a name, but a custom key with that name.
        temp[temp["type"]] = temp["name"]

        contents.append(temp)

    return {"contents": contents, "parent_name": display_name, "found_file": True}


# Gets the full set of data headers for the course.
# flat_course is a list of dictionaries.
def getAllKeys(flat_course, key_set=set()):
    for row in flat_course:
        for key in row:
            key_set.add(key)

    return key_set


# Ensure that all dicts have the same entries, adding blanks if needed.
# flat_course is a list of dictionaries.
def fillInRows(flat_course):
    # Get a list of all dict keys from the entire nested structure and store it in a set.
    key_set = getAllKeys(flat_course)

    # Iterate through the list and add blank entries for any keys in the set that aren't present.
    for row in flat_course:
        for key in key_set:
            if key not in row:
                row[key] = ""

    return flat_course


# Returns a usable URL for verticals and components, and just filenames for other types.
def makeURL(component_type, filename, parent_url, org, nickname, run):
    if component_type in ["course", "chapter", "sequential", "vertical", "wiki", run]:
        return filename

    course_id = org + "+" + nickname + "+" + run
    no_extension = ".".join(filename.split("/")[-1].split(".")[0:-1])
    if filename.startswith("tabs"):
        url = (
            "https://courses.edx.org/courses/course-v1:"
            + course_id
            + "/"
            + no_extension
        )
    elif filename.startswith("static"):
        url = (
            "https://courses.edx.org/asset-v1:"
            + course_id
            + "+type@asset+block@"
            + no_extension
        )
    else:
        url = (
            "https://studio.edx.org/container/block-v1:"
            + course_id
            + "+type@vertical+block@"
            + no_extension
        )

    return url


# Takes a nested structure of lists and dicts that represents the course
# and returns a single list of dicts where each dict is a component
def courseFlattener(course_dict, parent_url, org, nickname, run, new_row={}):
    flat_course = []
    temp_row = new_row.copy()

    # Add all the data from the current level to the current row except 'contents'.
    # For the "url" key, turn it into an actual URL.
    for key in course_dict:
        if key == "url":
            if "filename" in course_dict:
                temp_row["url"] = makeURL(
                    course_dict["type"],
                    course_dict["filename"],
                    parent_url,
                    org,
                    nickname,
                    run,
                )
            else:
                temp_row["url"] = makeURL(
                    course_dict["type"],
                    course_dict["url"],
                    parent_url,
                    org,
                    nickname,
                    run,
                )
        elif key != "contents":
            temp_row[key] = course_dict[key]

    # If the current structure has "contents", we're not at the bottom of the hierarchy.
    if "contents" in course_dict:
        # Go down into each item in "contents" and add its contents to the course.
        for entry in course_dict["contents"]:
            temp = courseFlattener(entry, temp_row["url"], org, nickname, run, temp_row)
            if temp:
                flat_course = flat_course + temp
        return flat_course

    # If there are no contents, we're at the bottom.
    else:
        # Don't include the wiki and certain other items.
        if temp_row["type"] not in skip_tags:
            # If there are links, images, or transcripts in this row,
            # break it into multiple entries.
            if len(temp_row["sub"]) > 0:
                transcript_rows = []
                for sub in temp_row["sub"]:
                    transcript_breakout = temp_row.copy()
                    transcript_breakout["sub"] = sub
                    transcript_rows.append(transcript_breakout)
                return transcript_rows
            if len(temp_row["links"]) > 0:
                link_rows = []
                for link in temp_row["links"]:
                    link_breakout = temp_row.copy()
                    link_breakout["href"] = link["href"]
                    link_breakout["linktext"] = link["text"]
                    link_rows.append(link_breakout)
                return link_rows
            if len(temp_row["images"]) > 0:
                img_rows = []
                for img in temp_row["images"]:
                    img_breakout = temp_row.copy()
                    img_breakout["src"] = img["src"]
                    img_breakout["alt"] = img["alt"]
                    img_rows.append(img_breakout)
                return img_rows
            else:
                return [temp_row]


def writeCourseSheet(rootFileDir, rootFileName, course_dict, args):
    course_name = course_dict["name"]
    if args.links:
        course_name += " Links"
    if args.alttext:
        course_name += " Images"
    course_name += ".tsv"

    outFileName = args.o if args.o else course_name

    # Create a "csv" file with tabs as delimiters
    with open(os.path.join(rootFileDir, outFileName), "wb") as outputfile:
        fieldnames = [
            "chapter",
            "sequential",
            "vertical",
            "component",
            "type",
            "url",
            "filename",
        ]

        # Include the XML if we're dealing with problems
        if args.problems:
            fieldnames.append("inner_xml")
        # Include link data if we're dealing with links
        if args.links:
            fieldnames = fieldnames + ["href", "linktext"]
        # Include alt text data if we're dealing with images
        if args.alttext:
            fieldnames = fieldnames + ["src", "alt"]
        # Include video data if we're dealing with videos
        if args.video:
            fieldnames = fieldnames + [
                "duration",
                "sub",
                "youtube",
                "edx_video_id",
                "upload_name",
                "download_url",
            ]

        writer = csv.DictWriter(
            outputfile, delimiter="\t", fieldnames=fieldnames, extrasaction="ignore"
        )
        writer.writeheader()

        spreadsheet = fillInRows(
            courseFlattener(
                course_dict,
                os.path.basename(rootFileName),
                course_dict["org"],
                course_dict["nickname"],
                course_dict["url"],
            )
        )
        for index, row in enumerate(spreadsheet):
            for key in row:
                spreadsheet[index][key] = spreadsheet[index][key]
        printable = []

        if args.all:
            printable = spreadsheet
        else:
            if args.links:
                printable += [
                    row
                    for row in spreadsheet
                    if row["type"]
                    in ["html", "problem", "xml", "docx", "pptx", "xlsx", "pdf"]
                ]
            if args.alttext:
                printable += [
                    row
                    for row in spreadsheet
                    if row["type"] in ["html", "problem", "xml"]
                ]
            if args.html:
                printable += [row for row in spreadsheet if row["type"] == "html"]
            if args.video:
                printable += [row for row in spreadsheet if row["type"] == "video"]
            if args.problems:
                printable += [row for row in spreadsheet if row["type"] == "problem"]

        for row in printable:
            # If we're printing links, skip entries with no links.
            # Checking if "href" attrib exists. Case: course has no links at all.
            if args.links:
                if "href" in row:
                    if row["href"] != "":
                        writer.writerow(row)
            # If we're printing alt text, skip entries with no images.
            # Checking if "src" attrib exists. Case: course has no images at all.
            elif args.alttext:
                if "src" in row:
                    if row["src"] != "":
                        writer.writerow(row)
            else:
                writer.writerow(row)

        print("Spreadsheet created for " + course_dict["name"] + ".")
        print("Location: " + outFileName)


# Main function
def Make_Course_Sheet(args=["-h"]):
    print("Creating course sheet")

    # Handle arguments and flags
    parser = argparse.ArgumentParser(usage=instructions, add_help=False)
    parser.add_argument("--help", "-h", action="store_true")
    parser.add_argument("-all", action="store_true")
    parser.add_argument("-problems", action="store_true")
    parser.add_argument("-html", action="store_true")
    parser.add_argument("-video", default=True, action="store_true")
    parser.add_argument("-links", action="store_true")
    parser.add_argument("-alttext", action="store_true")
    parser.add_argument("-o", action="store")
    parser.add_argument("file_names", nargs="*")

    # "extra" will help us deal with out-of-order arguments.
    args, extra = parser.parse_known_args(args)

    print("Arguments:")
    print(args, extra)

    if args.help:
        sys.exit(instructions)

    # Do video by default. Don't do it when we're doing other stuff,
    # unless someone intentionally turned it on.
    if not args.video:
        if args.problems or args.html or args.all or args.links or args.alttext:
            args.video = False

    # Link lister is not compatible with other options,
    # mostly because it makes for too big a spreadsheet.
    # Ditto for the alt text option.
    if args.links:
        args.problems = args.html = args.all = args.video = args.alttext = False
    elif args.alttext:
        args.problems = args.html = args.all = args.video = args.links = False

    # Replace arguments with wildcards with their expansion.
    # If a string does not contain a wildcard, glob will return it as is.
    # Mostly important if we run this on Windows systems.
    file_names = list()
    for arg in args.file_names:
        file_names += glob.glob(glob.escape(arg))
    for item in extra:
        file_names += glob.glob(glob.escape(item))

    # Don't run the script on itself.
    if sys.argv[0] in file_names:
        file_names.remove(sys.argv[0])

    # If the filenames don't exist, say so and quit.
    if file_names == []:
        sys.exit("No file or directory found by that name.")

    # Get the course.xml file and root directory
    for name in file_names:
        if os.path.isdir(name):
            if os.path.exists(os.path.join(name, "course.xml")):
                rootFileDir = name
        else:
            if "course.xml" in name:
                rootFileDir = os.path.dirname(name)

        rootFilePath = os.path.join(rootFileDir, "course.xml")
        course_tree = lxml.etree.parse(rootFilePath)

        # Open course's root xml file
        # Get the current course run filename
        course_root = course_tree.getroot()

        course_dict = {
            "type": course_root.tag,
            "name": "",
            "url": course_root.attrib["url_name"],
            "nickname": course_root.attrib["course"],
            "org": course_root.attrib["org"],
            "contents": [],
        }

        course_info = drillDown(
            os.path.join(rootFileDir, course_dict["type"]),
            course_dict["url"],
            course_root,
            args,
        )
        course_dict["name"] = course_info["parent_name"]
        course_dict["contents"] = course_info["contents"]

        if args.links:
            course_dict["contents"].extend(getAuxLinks(rootFileDir))
        if args.alttext:
            course_dict["contents"].extend(getAuxAltText(rootFileDir))

        with open(os.path.join(rootFileDir, "course.json"), "w") as course_json:
            course_json.write(json.dumps(course_dict, indent=4))
        writeCourseSheet(rootFileDir, rootFilePath, course_dict, args)


if __name__ == "__main__":
    # this won't be run when imported
    Make_Course_Sheet(sys.argv)
