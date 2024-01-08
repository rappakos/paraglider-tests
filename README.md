
# Evaluation of paraglider certification documents

Tool to easily get new certification data and compare gliders.

## Data

 A,B,C certification tests by DHV or Air Turquoise starting with test dates around 2020-01-01.

###  Air Turquoise

 Air Turquoise provides data over PDF links, most of which can be processed relatively easily. Some files have broken text content that need some additional tricks.

### DHV

The DHV test reports are available as HTML, which can be extracted using standard tools.


## Home - summary of the data

![Home screen with all current data on Jan. 1, 2024](./screenshots/home_2024-01-07.PNG)

## Paraglider comparisons

![Filter and compare paragliders](./screenshots/filter_results.png)

### Tesseract 

Some PDF files need to be processed with an OCR tool.

Add `tesseract_cmd` with path to the exe to a `.env` file.


### Run on Android

* install Termux (with F-Droid)
* install Termux:Widget (with F-Droid)
* check out this repo in Termux
* install python requirements
* copy a `glider_tests.db` next to the `app.py` file
* create `.shortcuts/tasks/pg-test.bash` in ~ with following:
 ** cd <github folder>/paraglider-tests;
 ** python app.py
* add shortcut with the termux widget to the screen
* go to 
http://localhost:3978/









