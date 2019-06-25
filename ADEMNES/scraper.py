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
from ADEMNES.log_db import Attempt, DBSession

RE_URL = re.compile(r'href=[\'"]([\w:/=?.]+)[\'"]')
RE_ID = re.compile(r's=(\d+)')


session = DBSession()


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
    text = str(r.content, encoding="UTF-8")
    path = os.path.join(os.path.dirname(__file__), 'results', "Site_{}.html".format(site_id))
    mkdirp(os.path.dirname(path))
    print((path, r.status_code, url, text[:10]))
    with open(path, 'w') as fh:
        fh.write(text)
        log_entry.saved = True
        session.add(log_entry)
        session.commit()
    return r.status_code, url


def download(max_workers=100):
    """Pull everything from the site"""
    site_ids = range(1075)
    already_tried = [a.site_id for a in session.query(Attempt).filter(Attempt.saved == True).all()]
    to_scrape = [s for s in site_ids if int(s) not in already_tried]
    print("Total {}".format(len(site_ids)))
    print("Tried {}".format(len(already_tried)))
    print("ToDo {}".format(len(to_scrape)))
    print("Go!")
    for id in site_ids:
        scrape_details(id)



def mkdirp(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


if __name__ == "__main__":
    download()
