# german_parliament_scraper

This python script enables you to automatically download session protocols of the German Parliament in three forms:
- the original format (xml)
- a preprocessed format (xml)
- a consolidated file (csv).
The preprocessed xml-files wrap the speaker and his/her speech by introducing an additional tag("abschnitt"). This custom specification simplifies data analysis.
The csv-file contains the columns "datum" (date), "sitzung" (session number), "abschnitt" (section number, seperated by speakers), "name" (the speaker's name), "fraktion" (party), "p_tag_abschnitt" (speech of the section).

This script provides a command line interface. Just insert "python scraper_cli.py <number of protocols requested>" into your shell.
At the moment, only protocols from the current election period (Wahlperiode 19) are available, that is 171 protocols for now.

Be sure to have installed the packages that are specified in the requirements.txt py typing "sudo pip install -r requirements.txt".
(Before you might want to check your python-version with "which python" / "python --version". If you don't have python3, you can use "sudo easy_install python3" for example.) 