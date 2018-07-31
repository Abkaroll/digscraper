import bs4
import os

import pandas as pd
from pprint import pprint

from megajordan.main import SiteInfo


def slurp(filename):
    with open(filename, "r", encoding='UTF-8') as fh:
        return fh.read()


def chunker(seq, size):
    chunks = []
    for item in seq:
        chunks.append(item)
        if len(chunks) >= size:
            yield chunks
            chunks = []


def geo_median(coords):
    if coords:
        coords = coords.split(",")
        coords = [c.split() for c in coords]
        x = [float(c[0]) for c in coords]
        y = [float(c[1]) for c in coords]
        return (sum(x)/float(len(x)), sum(y)/float(len(y)))


def general(filename):
    """
    Returns a list of
    :param filename:
    :return:
    """
    soup = bs4.BeautifulSoup(slurp(filename), 'lxml')
    # print(soup.prettify())
    # Grab the basic data out of its god-awful single-row table, anchored by the MEGA NUMBER cell
    basename = os.path.basename(filename)
    gid, page = basename.split('-')
    basic_data = {'gid': gid, 'file': basename}
    for key, value in chunker(soup.find_all('td'), 2):
        if key.string is not None and value.string is not None:
            key = key.string.strip()
            value = value.string.strip()
            basic_data[key] = value
            if 'Coordinates' in key:
                basic_data['Coordinate Mean'] = geo_median(basic_data[key])
    return basic_data


if __name__ == "__main__":
    general_sheet = []
    general_files = []
    for gid in os.listdir('results'):
        directory = os.path.join('results', gid)
        general_files.extend([os.path.join(directory, f) for f in os.listdir(directory) if "General" in f])

    for f in general_files:
        general_sheet.append(general(f))

    df = pd.DataFrame(general_sheet)
    df['MEGA Number'] = df['MEGA Number'].apply(int)
    df = df.set_index('MEGA Number')
    df = df.sort_index()
    df.to_csv(os.path.join(SiteInfo.RESULTS_DIR, 'general.csv'))
    pprint(df)