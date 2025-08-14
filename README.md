docx2md - V1.0

# PRESENTATION OF THE SOLUTION

The idea is to be able to loyally convert docx files to markdown format with the least amount of manual processing possible.
The starting point is Pandoc, a versatile and customizable document converting tool that here outputs raw pandoc.
Then : python scripts fix many formats and styles in the document, for a near perfect conversion in the end.


## TECHNICAL PRESENTATION

The solution consists in a bash script that :
1) clears the /source and /output directories
2) picks one file at a time in the /source directory, copies it to /source_marked, exctracts its code blocks in a JSON file, and marks the docx file where the code blocks are.
3) picks the marked file, converts it to raw Markdown with pandoc, exporting the images to the /images directory
4) launches a python script that keeps html tables as is and converts complex tables into html (markdown doesn't work with any special table)
5) launches a python script that finds the table of contents with regex patterns, fixes hyperlinks to look good, and puts it in a beautiful looking ordered list
6) launches a python script that finds sections with headers and formats them correctly
7) launches a python script that finds image links and fixes them to look good and target the image in /images/<document>/media
8) launches a python script that looks for .emf/.wmf images, converts them to .png, then fixes the links to target the new images
9) finally, launches a python script that looks for the marks left precedently, and replaces them with the correspondant code block in the JSON file


# ACCESS DOCX2MD / INSTALLATION PROCESS

### ACCESS THE DOCX2MD DOCKER CONTAINER

Currently, this tool is being used inside a Debian Docker Image (for Orange OINIS)
You can access it with SSH : 

````
ssh debian@172.17.0.7
````

You can ask the person monitoring the Trusted Zone for an login, and the container's password.
Once inside, you can clone the GitLab repository :

````
git clone https://cicd-gitlab.rp-ocn.apps.ocn.infra.ftgroup/engine-documentation/docx2md.git
````

then, install the needed requirements :

````
cd docx2md
pip3 install -r requirements.txt
````

The external tools and latest python3 version are already in the container.
Then, you can make the source directory (inside the workdir) :
````
mkdir source
````
It's the one where you'll put your docx files before running the bash script.
You're ready to go !

### MANUAL INSTALLATION (NEED ROOT PRIVILEGES)

First, clone the GitLab repository :

````
git clone https://github.com/gitgud443/Docx2Md
````

Then, install the dependencies and the tools required if you have root privileges :

````
cd docx2md
pip3 install -r requirements.txt
sudo apt-get install pandoc
sudo apt-get install imagemagick
sudo apt-get install unoconv
sudo apt-get install inkscape
sudo apt-get install pdf2svg
````
Then, you can make the source directory (inside the workdir) :
````
mkdir source
````
It's the one where you'll put your docx files before running the bash script.
You're ready to go !

# DOCX TO MARKDOWN BATCH PROCESSING STEPS

1) Get the **docx** files you want on your VM :
    - do not forget to convert any old .doc file to .docx, directly on Word (save as -> .docx)
    - either by downloading them on your VM
    - or transferring them from your pc using windows cmd : scp <path to folder containing files> debian@172.17.0.7:/home/<TZ_id>

2) Transfer them to $HOME/tech-doc-conversion/source
    - if you're transferring files from a folder : cp -a <folder>/. <dest>/

3) Run the special characters detection script inside tech-doc-conversion :
    - python3 detect_non_unicode.py source/  #source is the folder where the docx files are saved

4) Detect_non_unicode.py will tell you in the terminal for each file in /source whether they have special non-unicode characters.
    - do not take into account \n and \t because these are newline and tab characters.
    - any character that's not them is a special character that you maybe need to replace in the docx file. example : "\uf0b0"
    - Most of the time : special characters in paragraphs, mostly at position 0, are negligeable. The ones you should look for are ones inside tables. (checkmarks and arrows)
    - details on where to find said character and rough number of times it appears is given too
    - once you find one of them, copy it and paste it in the ctrl + f window to find them all. 
    - decide if it's best to replace it with a unicode character, or delete it.

5) Once done, re-upload the files you needed to change to your VM and overwrite them in source/
    - then run the batch processing bash script ./process_documents.sh
    - and python3 detect_non_unicode.py source/ 
    - the final markdown version will be in output/<doc_name>_final_version.md
    - verify that special characters are dealt with, images, table of contents, tables, codeblocks
    - for any trouble : look # troubleshooting at the end of the readme, and you can check every version of the markdown inside output/ to see what didn't work

6) If you want, you can run python3 prepare_for_production.py
    - it takes the final markdown version of each file, and arranges them inside folders with their media folder (and changes markdown links to point well). everything is put inside the production/ directory.


### EXTERNAL TOOLS REQUIRED

For this process, we are using these tools : (already on the docker container)
- Pandoc : sudo apt-get install pandoc
- ImageMagick : sudo apt-get install imagemagick
- unoconv : sudo apt-get install unoconv
- inkscape : sudo apt-get install inkscape
- python3 requirements are inside requirements.txt


# CUSTOM COMMANDS AND USEFUL TOOLS

- type ./process_documents.sh -h or ./process_documents.sh --help and it will show you this :
````
Options:
  -c, --clean-only    Clean old files without processing new ones
  -s, --skip-images   Skip image conversion step
  -v, --vector-svg    Convert vector to SVG instead
  -h, --help          Show this help message
````
- python3 detect_non_unicode.py  to detect special characters in your documents. Remember that \t and \n are normal.
- python3 scripts/debug_toc.py  to debug the table of contents processing


# DOCKER USAGE

- One of the challenges with this conversion process is converting images with a special format. Because of their nature, some images will be in .emf, .wmf or even .gif formats, that do not render well when imported on a web page.
- But the tools needed for that conversion are far too heavy to be installed on the trusted zone. So we're using a docker container to use them.
- Currently, the container is debian@172.17.0.7, and can be accessed via SSH if you know its password.


# TROUBLESHOOTING : KNOWN ISSUES

### TABLE OF CONTENTS

1) a clean table of contents should look like this :
````
## Table of Contents

* [1 References](#references)
* [2 Scope of the agreement](#scope-of-the-agreement)
* [3 Chassis description](#chassis-description)
  * [3.1 Cisco 7609-S](#cisco-7609-s)
    * [3.1.1 Cisco 7609-S Overview](#cisco-7609-s-overview)
    * [3.1.2 Cisco 7609-S Physical Specifications](#cisco-7609-s-physical-specifications)
````
- with a header 2 (##), indented '*'s and clean links.

2) if nothing has '*'s or is indented : it may be that the script **did not recognize** the table of contents, because it has a special format or doesn't have a header or line before with 'table of contents', 'contents' or any variation. and I mean EVERY variation. It can also be that "table of contents" is in another langage, due to Word's settings. In any case, you will need to manually add a "table of contents" or "contents" paragraph inside your docx file, just before the table of contents, and process it again.

3) if the links look messy : compare the example shown above \[<shown text>](#<hyperlink>) to your markdown links. 

4) if hyperlinks to the figures or tables are in the same list as the table of contents, separate them using headers 2.
example : 
````
    * [3.1.2 Cisco 7609-S Physical Specifications](#cisco-7609-s-physical-specifications)
## Figures
* [figure 1](#link_to_figure_1)

## Tables
* [table 1](#link_to_table_1)
````

5) if you still don't find an answer, you can run the debug_toc.py script in scripts/.

### IMAGES

1) **images not appearing :**
    - a clean link should look like this : !\[image](../images/<doc_name>/media/image19.jpeg) or in html.
    - check its link in the markdown, verify it targets a real image in images/<doc_name>/media/
    - check its format : if it isn't .png or .jpeg it might just not render in markdown. you will have to manually convert the picture and replace it.

2) **poor quality / cut / cropped / too big or small**
    - again, that would be because the tools used (unoconv and imagemagick) did not do the job at converting emf/wmf images, or the image was corrupted to begin with. manually grab them from the docx file and change them, or replace them and run ./process_documents.sh again.

### TABLES

- if a table looks messy, does not render and looks like a blob of characters : try to get the original one from the docx file and export it as html, the replace it on te markdown
- if a table is missing content : 
    - run again the detect_non_unicode.py script, and look for that specific file. if strange characters remain, and it specifies "inside table xx", it could be the issue. manually replace that character in the docx file with a known one and process the file again. 
    - again : try to get the original one from the docx file and export it as html, the replace it on te markdown

### INITIAL PANDOC CONVERSION FAILING

- in **very rare** cases, the initial conversion using a pandoc command fails. 
- it could be many things : corrupted docx file, old format, special encoding ...
- the only solution i've found is openning the docx file in Word, then copying its contents with ctrl + a   ctrl + c and pasting it in a new blank Word document, then replacing the old file with it.
