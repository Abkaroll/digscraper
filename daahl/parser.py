import os
import csv
import uuid

from bs4 import BeautifulSoup

import pandas as pd

def site_records():
    """
    Yields a SiteRecord data-parsing object for each of the 47K results, one after another.
    """
    for root, dirnames, files in os.walk('results'):
        for f in files:
            filename = os.path.join(root, f)
            with open(filename, encoding='UTF-8') as fh:
                yield SiteRecord(fh.read())


class SiteRecord(object):
    """
    A single HTML page about a single archaeological site has data broken into a few different sections
    """
    def __init__(self, html_text):
        self.soup = Soup(html_text, 'lxml')
        self.site_id = None

    def _kv_section(self, cell_value_keyword):
        table = self.soup.find_kv_table(cell_value_keyword)
        data = table.as_dict()
        data['site_id'] = self.site_id
        # Return a list of one dict for consistency with the list_section so the collector can always .extend
        return [data]

    def _list_section(self, cell_value_keyword, kv=True):
        if kv:
            table = self.soup.find_kv_table(cell_value_keyword)
        else:
            table = self.soup.find_titled_table(cell_value_keyword)
        data = table.list_of_dicts()
        for d in data:
            d['site_id'] = self.site_id
        return data

    def basic_data(self):
        """
        Returns dict of basic site data from the soup, like name/lat/lon
        """
        # The basic data is in one of the very common "KEY:  value" tables
        data = self._kv_section('DAAHL SITE #:')
        self.site_id = data[0].get('DAAHL SITE #', 'ERR-{}'.format(uuid.uuid4()))
        data[0]['site_id'] = self.site_id
        return data

    def alternate_names(self):
        """
        Returns a list of alternate names for the site, if any.
        """
        return self._list_section('MNEMONIC', kv=False)

    def condition_report(self):
        """
        Returns a dict of dated condition report information, if any
        """
        # Actually up to three parts:
        #  1) Condition Report (k:v pairs)
        #  2) Threats (multidict)
        #  3) Disturbances (multidict)
        # Looks like #2 and/or #3 shows up only after #1 does in the document?
        # I haven't actually seen multiple copies of #1 in the same site yet?
        return self._kv_section('OVERALL CONDITION:')

    def site_tags(self):
        """
        returns dict of tags
        """
        return self._list_section('FEATURE TYPE', kv=False)

    def contributor(self):
        """
        Returns contributor information
        """
        return self._kv_section('CONTRIBUTOR:')

    def references(self):
        """
        Bibliographic entry.
        
        List of reference/title/serial name dictionaries
        """
        return self._list_section('REFERENCE:', kv=True)


class Soup(BeautifulSoup):
    """
    A BeautifulSoup processing tree with some handy utility methods for pulling out common constructs in these 
    DAAHL records
    """

    def find_titled_table(self, cell_value):
        """
        Find a regular table with the given cell value. The first row is assumed to be headers, and the rest are values
        """
        cell = self.find(lambda x: x.text.strip() == cell_value)
        if cell is None:
            return RegularTable(BeautifulSoup("", 'lxml'))
        table_node = (
            cell
            .parent  # <td> element
            .parent  # <tr> element
            .parent  # container element
        )
        return RegularTable(table_node)

    def find_kv_table(self, cell_value):
        """
        Find a table which contains the given cell value
        """
        cell = self.find(lambda x: x.text.strip() == cell_value)
        if cell is None:
            return KeyValueTable(BeautifulSoup("", 'lxml'))
        table_node = (
            cell
            .parent  # <td> element
            .parent  # <tr> element
            .parent  # container element
        )
        return KeyValueTable(table_node)


class Section(object):
    """
    A chunk of HTML that contains related data. Probably in some kind of tabular format
    """

    def list_of_dicts(self):
        """
        All sections should be able to pull data in the format of a list, with zero or more data dictionaries in them
        """
        raise NotImplemented()


class RegularTable(Section):
    """
    A regular table, with a header (more than two columns). Less common, but still present
    """

    def __init__(self, table_node):
        self.table_node = table_node
        rows = list(self.rows())
        self.header = []
        self.data_rows = []
        if rows:
            self.header = rows[0]
        if len(rows) > 1:
            self.data_rows = [r for r in rows[1:] if r]

    def rows(self):
        """
        Header row followed by data rows. No title row or empty rows.
        """
        rows = []
        for row in self.table_node.find_all('tr'):
            rdata = [td.text.strip() for td in row.find_all(['th', 'td'])]
            if len(rdata) > 1:
                rows.append(rdata)
        return rows

    def list_of_dicts(self):
        return [dict(zip(self.header, d)) for d in self.data_rows]


class KeyValueTable(Section):
    """
    A common pattern for these pages is a table of key-value paris
      
      KEY1: value
      KEY2: value2
      KEY3: etc
      ...
      
    Most of the time each key is unique (like above). These should be interpreted as a dictionary.
     
    but some sections have a table with repeat keys, like this:
    
      TITLE: cat in the hat
      AUTHOR: Dr. Seuss
      TITLE: hop on pop
      AUTHOR: Dr. Seuess
      
    These should be interpreted as a list of dictionaris.
    
    
    The HTML will look something like this:
    
    <container> <!-- maybe table, maybe div -->
     <tr class=row1>
       <td class=fldname style='width: 140px'>DAAHL SITE #:</td>
       <td class=data>343103707 </td>
     </tr>
     <tr class=row1>
        ...
     </tr>
    </container
    
    """
    def __init__(self, table_node):
        self.table_node = table_node or BeautifulSoup("")

    def kv_pairs(self):
        """
        Yields pairs of elements from any two-column rows in the table.
        """
        for row in self.table_node.find_all('tr'):
            # Iterate over all the rows in the table-like construct
            elements = row.find_all('td')
            if len(elements) == 2:
                # If it fits the pattern of two-column table row, store the human-readable text values as a k: v pair
                k = elements[0].text.strip()
                v = elements[1].text.strip()
                # Don't include the colons in the key names, that's silly.
                k = k.rstrip(':')
                yield k, v

    def as_dict(self):
        """
        For k:v pairs which are not expected to have repeated keys, or when repeated keys should overwrite the earlier
        copy.
        """
        return {k: v for k, v in self.kv_pairs()}

    def list_of_dicts(self):
        """
        For k:v pairs which represent multiple copies of the same kind of thing, repeated keys signify that we should 
        start a new dictionary.
        """
        md = multidict()
        l = []
        for k, v in self.kv_pairs():
            l = md.send((k, v))
        return l


def coroutine(function):
    """
    Automatically "prime" the coroutine:
      1) initialize it
      2) advance it to the first `yield` statement
    """
    def primed(*args, **kwargs):
        f = function(*args, **kwargs)
        next(f)
        return f
    return primed


@coroutine
def multidict():
    """
    Coroutine to turn a stream of 2-tuples into a list of dicts. Whenever it sees a duplicate key come in, it starts a 
    new dict.
    
    Yields a reference to the list of dicts it's building up with each .send() call so you can pull data out whenever.
    """
    l = [{}]  # List with one empty dict to start
    while True:
        k, v = yield l   # Yields a reference to the same list over and over.
        if k in l[-1].keys():
            l.append({})
        l[-1][k] = v


def save_csv(fname, data):
    """
    Save a list of dictionaries to a given file
    """
    dirname = os.path.dirname(__file__)
    # Frustratingly, we don't actually know the headers beforehand. We have to pull all the data into memory and
    header = set()
    for d in data:
        header |= set(d.keys())
    with open(os.path.join(dirname, fname), 'w', encoding='UTF-8') as fh:
        writer = csv.DictWriter(fh, header)
        writer.writeheader()
        for row in data:
            if row:
                writer.writerow(row)

def save_ws(wb, sheet_name, list_of_dicts):
    sh = wb._add_sheet(sheet_name)

if __name__ == "__main__":
    sections = {
        'basic_data': [],
        'alternate_names': [],
        'condition_report': [],
        'site_tags': [],
        'contributor': [],
        'references': [],
    }
    for i, site in enumerate(site_records()):
        # call each section parser, and collect the data from the section (if any)
        for section, container in sections.items():
            f = getattr(site, section)
            container.extend(f())

        # Progress counter
        if i and not i % 100:
            print(".", end="", flush=True)
        if i and not i % 10000:
            print(i)

    print('Save everything as an excel workbook')
    panel = pd.Panel()
    with pd.ExcelWriter('daahl.xlsx') as writer:
        for section, container in sections.items():
            df = pd.DataFrame(data=container)
            if 'site_id' in df:
                df = df.set_index('site_id')
            df.to_excel(writer, sheet_name=section)
        writer.save()
