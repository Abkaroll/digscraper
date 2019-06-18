import concurrent
import os
import re
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

import requests
requests.packages.urllib3.disable_warnings()

import requests
from lxml import etree
import csv
try:
    from log_db import Attempt, DBSession
except ImportError:
    from admnes.log_db import Attempt, DBSession

RE_URL = re.compile(r'href=[\'"]([\w:/=?.]+)[\'"]')
RE_ID = re.compile(r's=(\d+)')


session = DBSession()

def parse_kml(filename):
    """
    Returns a dict of site name, ID, URL, and coordinates out of the KML file
    """
    with open(filename, encoding='UTF-8', errors='replace') as fh:
        contents = fh.read()
        xml = etree.fromstring(bytes(contents, encoding='UTF-8'))
    sites = []
    for place in xml.xpath('//Placemark'):
        description = place.xpath('description')[0].text
        url = RE_URL.search(description).group(1)
        site_id = RE_ID.search(url).group(1)
        sites.append({
            'name': place.xpath('name')[0].text,
            'coords': place.xpath('Point/coordinates')[0].text,
            'url': url,
            'id': site_id,
         })
    return sites


def extract_site_data(kml_file):
    """
    Saves the contents of a KML file as a .csv
    """
    sites = parse_kml(kml_file)
    with open('site_list.csv', 'w') as fh:
        writer = csv.DictWriter(fh, fieldnames=['id', 'name', 'coords', 'url'])
        writer.writeheader()
        [writer.writerow(s) for s in sites]
    return sites


def scrape_details(site_id):
    """
    Download the HTML for a given site ID
    """
    session = DBSession()
    url = "http://www.ademnes.de/db/site.php?s={}".format(site_id)
    r = requests.get(url, verify=False)
    log_entry = Attempt(
        site_id=site_id,
        url=url,
        status_code=r.status_code,
    )
    session.add(log_entry)
    session.commit()
    dirname = site_id[-2:]  # Kinda like git -- split the saved files into folders
    mkdirp(dirname)
    print((r.status_code, url))
    with open(os.path.join('results', dirname, "Site_{}.html".format(site_id)), 'w') as fh:
        fh.write(str(r.content, encoding='UTF-8'))
        log_entry.saved = True
        session.add(log_entry)
        session.commit()
    return r.status_code, url


def download(max_workers=100):
    """Pull everything from the site"""
    sites = extract_site_data('results/ucsd.xml')
    already_tried = [a.site_id for a in session.query(Attempt).filter(Attempt.saved == True).all()]
    to_scrape = [s for s in sites if int(s['id']) not in already_tried]
    print("Total {}".format(len(sites)))
    print("Tried {}".format(len(already_tried)))
    print("ToDo {}".format(len(to_scrape)))
    print("Go!")
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(scrape_details, s['id']) for s in to_scrape]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(result)


def mkdirp(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


if __name__ == "__main__":
    pass