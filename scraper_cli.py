import os
import bs4
import requests
import re
import time
import random
import sys
import pandas as pd

# CLI

if len(sys.argv) >= 2 and int(sys.argv[1]) <= 171:
    amount = int(sys.argv[1])
else: 
    inp = input('How many protocols do you want to download? (max. 171 available): ')
    while int(inp) > 171:
        inp = input('Please insert the number of protocols you want to download (max. 171 for this election period available): ')
    amount = int(inp)
print(f'This script will download the last {amount} protocols.')

# SCRIPT 1

# get the dynamic opendata pages
opendata_page = 'https://www.bundestag.de/ajax/filterlist/de/services/opendata/543410-543410?limit=10&noFilterSet=true&offset='
number_pages = amount
numbers = list(range(0,number_pages,10))
pages = []
for number in numbers:
    pages.append(opendata_page + str(number))

# request the pages to get xml links
links_to_xml = []
for page in pages:
    page_request = requests.get(page)
    regex_link_to_xml = r'/resource/blob/\d+/[a-z0-9]+/\d+-data.xml'
    link_ends = re.findall(regex_link_to_xml, page_request.text)
    link_start = 'https://www.bundestag.de'
    for link_end in link_ends:
        links_to_xml.append(link_start + link_end)

# make a random sleeper to request irregularly
def sleeping():
    sec = random.randint(1, 3)
    split_sec = sec/5
    time.sleep(split_sec)

# request xmls and save to folder
foldername = './Wahlperiode19_data'
os.mkdir(foldername)
for link in links_to_xml:
    if number_pages > 0:
        sleeping()
        xml_request = requests.get(link)
        filename = str(number_pages)+ '.xml'
        file = open(foldername + '/' + filename, 'w', encoding='UTF-8')
        file.write(xml_request.text)
        file.close()
        number_pages-=1

# SCRIPT 2

folder_source = foldername
folder_target = foldername
filenames = os.listdir(folder_source)

for filename in filenames:
    if filename != '.DS_Store':
        # open file and select p klasse redner
        with open(folder_source + '/' + filename, encoding='UTF-8') as file:   
            content = file.read()
            soup = bs4.BeautifulSoup(content, 'xml') # bzw. html.parser
            ps = soup.find_all('p', attrs={'klasse' : 'redner'}) # tag mit spezifischem Attribut abgreifen
            names = soup.find_all('name')
        
            # collect next siblings of p redner
            for p in ps:
                redner_agg = []
                for sibling in p.next_siblings:
                    if isinstance(sibling, bs4.element.Tag) and sibling.get('klasse') == 'redner':
                        break
                    else:
                        redner_agg.append(sibling)
                # define new tag "abschnitt" and wrap p in it
                abschnitt = soup.new_tag('abschnitt')
                p.wrap(abschnitt)
                # add siblings to "abschnitt"
                for tag in redner_agg:
                    abschnitt.append(tag)

            # collect next siblings of name
            for name in names:
                name_agg = []
                if name.find('vorname'):
                    continue
                else:
                    for nsibling in name.next_siblings:
                        name_agg.append(nsibling)
                # define new tag "name_abschnitt" and wrap name in it
                name_abschnitt = soup.new_tag('name_abschnitt')
                name.wrap(name_abschnitt)
                # add siblings to "name_abschnitt"
                for tag in name_agg:
                    name_abschnitt.append(tag)

        # save new files with "abschnitt"
        with open(folder_target + '/preprocessed' + filename, 'w', encoding='UTF-8') as new_file:
            new_file.write(str(soup))

# SCRIPT 3

# functions with beautifulsoup
def get_redner_info(child):
    vorname = child.find('vorname')
    if vorname != None:
        vorname = vorname.text
    nachname = child.find('nachname')
    if nachname != None:
        nachname = nachname.text
    name = str(vorname) + ' ' + str(nachname)
    fraktion = child.find('fraktion')
    if fraktion != None:
        fraktion = fraktion.text
    return name, fraktion

def get_sitzungsnummer_and_datum(soup):
    sitzungsnummer = soup.find('sitzungsnr').text
    datum = soup.find('datum').get('date')
    return sitzungsnummer, datum

def is_redner(child):
    if child.name == 'p' and child.get('klasse', []) == 'redner':
        return True

def is_redner_p_tag(child):
    if child.name == 'p' and (child.get('klasse', []) in ['J_1', 'J', 'O']) and child.parent.name != 'name_abschnitt':
        return True

path = foldername
filenames = os.listdir(path)

# make lists of same length
namen = []
fraktionen = []
p_tags = []
sitzungsnummern = []
datums = []
abschnittsnummern = []
for filename in filenames:
    if filename != '.DS_Store':
        with open(path + '/' + filename, encoding='UTF-8') as file:
            content = file.read()
            soup = bs4.BeautifulSoup(content, 'xml')
            reden = soup.find_all('rede')
            abschnitte = soup.find_all('abschnitt')
            sitzungsnummer, datum = get_sitzungsnummer_and_datum(soup)
            abschnittsnummer = 0
            for abschnitt in abschnitte:
                children = abschnitt.findChildren()
                for child in children:
                    if is_redner(child):
                        name, fraktion = get_redner_info(child)
                        abschnittsnummer += 1
                    if is_redner_p_tag(child):
                        p_tags.append(child.text)
                        namen.append(name)
                        fraktionen.append(fraktion)
                        sitzungsnummern.append(sitzungsnummer)
                        datums.append(datum) 
                        abschnittsnummern.append(abschnittsnummer)       

# create dataframe
df_dict = {'datum':datums, 'sitzung':sitzungsnummern, 'abschnitt':abschnittsnummern, 'name':namen, 'fraktion':fraktionen, 'p_tag':p_tags}
df = pd.DataFrame(df_dict)
df.sort_values(by=['datum', 'sitzung', 'abschnitt'], inplace=True)

# clean p_tags
def clean_text(p_tag):
    p_tag_clean1 = p_tag.replace('\xa0', ' ') # encoding problem inspite of utf-8
    p_tag_clean2 = re.sub(r'(\d+)(\w+)', r'\1 \2', p_tag_clean1) # seperate numbers and words
    p_tag_clean3 = re.sub(r'(\d+)(\s)(\d+)', r'\1\3', p_tag_clean2) # connect two following numbers
    return p_tag_clean3
df['p_tag'] = df['p_tag'].apply(clean_text)

# group by abschnitte and merge with original dataframe
abschnitte_grouped = df.groupby(['datum', 'sitzung', 'abschnitt'])['p_tag'].transform(lambda x: ' '.join(x)).drop_duplicates()
abschnitte_df = pd.DataFrame(abschnitte_grouped)
abschnitte_df.rename(columns={'p_tag':'p_tag_abschnitt'}, inplace=True)
merged_df = df.merge(abschnitte_df, how='inner', left_index=True, right_index=True).drop('p_tag', axis=1)

# save to csv
merged_df.to_csv(path + '/preprocessed_data.csv', encoding='UTF-8')

print('New folder Wahlperiode19_data created.')
print('Documents generated: original xml-files, preprocessed xml-files, csv-file storing structured data.')
