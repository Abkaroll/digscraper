"""
Data-driven way to figure out if we got the parsers right.

Hand-parse a few HTML sites, and make sure the parser can handle them correctly.
"""
from unittest import TestCase, SkipTest
import os

try:
    from daahl.parser import SiteRecord
except ImportError:
    from parser import SiteRecord

BASE_DIR = os.path.join(os.path.dirname(__file__), 'results')


class ParserTest(TestCase):
    """
    Each test case is for one file
    """
    filename = ''
    basic_data = {
        'DAAHL SITE #': "",
        'SIZE': "",
        'ELEVATION': "",
        'SITE NAME': "",
        'LATITUDE': "",
        'LONGITUDE': "",
        'NOTES': "",
    }
    contribution = {
        'CONTRIBUTOR': "",
        'INSTITUTION': "",
        'ADDRESS': "",
        'E-MAIL': "",
        'URL': "",
        'DATA DESCRIPTION': "",
    }
    components = [
        {'PERIOD': "", 'FEATURE TYPE': "", 'SIZE (ha)': "", 'DESCRIPTION': ""}
    ]
    condition_report = {
        'OVERALL CONDITION': "",
        'OVERALL RATING': "",
        'CUMULATIVE RISK': "",
        'SEVERITY OF RISK': "",
        'DATE VISITED': "",
        'ENTERED BY': "",
        'DATE ENTERED': "",
    }

    def get_soup(self):
        if not self.filename:
            raise SkipTest("No file. Don't test this.")
        fname = os.path.join(BASE_DIR, self.filename)
        with open(fname) as fh:
            return SiteRecord(fh.read())

    def test_basic_data(self):
        """
        Basic data like ID, size, elevation, name, lat, lon, notes
        """
        soup = self.get_soup()
        data = soup.basic_data()
        self.assertEqual(data, self.basic_data)

    def test_contributions(self):
        """
        Bibliographic entry for the site
        """
        soup = self.get_soup()
        data = soup.contributor()
        self.assertEqual(data, self.contribution)

    def test_components(self):
        """
        Features the site has, along with which time period they existed and their size
        """
        soup = self.get_soup()
        data = soup.site_tags()
        for d, c in zip(data, self.components):
            self.assertEqual(d, c)

    def test_condition_report(self):
        """
        A condition report, if any
        """
        soup = self.get_soup()
        data = soup.condition_report()
        self.assertEqual(data, self.condition_report)


class Parse353002210(ParserTest):
    """
    Each test case is for one file
    """
    filename = '10/Site_353002210.html'
    basic_data = {
        'DAAHL SITE #': "353002210",
        'SIZE': "18",
        'ELEVATION': "852",
        'SITE NAME': "NN - WHNBS Site 485",
        'LATITUDE': "30.90850",
        'LONGITUDE': "35.85870",
        'NOTES': "Elevation from Google Elevation Service.",
    }
    contribution = {
        'CONTRIBUTOR': "Dr. Geoffrey A. Clark",
        'INSTITUTION': "School of Human Evolution & Social Change, Arizona State University",
        'ADDRESS': "Box 872402, Tempe, AZ  85287",
        'E-MAIL': "gaclark@asu.eu",
        'URL': "http://shesc.asu.edu/clark",
        'DATA DESCRIPTION': "Wadi Hasa North Bank Survey sites in siuthwestern Jordan.",
    }
    components = [
        {'PERIOD': "Unspecified", 'FEATURE TYPE': "Sherd / Flint Scatter", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Unspecified", 'FEATURE TYPE': "Tower", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Iron IIa/b", 'FEATURE TYPE': "Sherd / Flint Scatter", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Iron IIc", 'FEATURE TYPE': "Sherd / Flint Scatter", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
    ]
    condition_report = {
        'OVERALL CONDITION': "No Information",
        'OVERALL RATING': "Site Destroyed (Excavation impossible)",
        'CUMULATIVE RISK': "Unknown / Not Noted",
        'SEVERITY OF RISK': "Unknown",
        'DATE VISITED': "1993-09-18",
        'ENTERED BY': "SA",
        'DATE ENTERED': "1993-09-18",
    }


class Parser353102710(ParserTest):
    """
    Each test case is for one file
    """
    filename = '10/Site_353102710.html'
    basic_data = {
        'DAAHL SITE #': "353102710",
        # This page has no SIZE datum
        'ELEVATION': "417",
        'SITE NAME': "Horbat `Adullam",
        'LATITUDE': "31.65000",
        'LONGITUDE': "35.00000",
        'NOTES': "ANS - Imported from Israel Place Names Gazette, compiled by U.S. Defense Mapping Agency. Elevation from Google Elevation Service.",
    }
    alternate_names = [
        "Horbat Nakar",
        "Horbat `Adullam",
        "Khirbat Id al Minya",
        "Khirbat Jubeil Naqqar",
        "Miya",
    ]
    contribution = {}
    components = []
    condition_report = {}


class ParserTest353102110(ParserTest):
    """
    Each test case is for one file
    """
    filename = '10/Site_353102110.html'
    basic_data = {
        'DAAHL SITE #': "353102110",
        'SIZE': "1000",
        'ELEVATION': "291",
        'SITE NAME': "NN - Wadi Isal Survey Site D 7- 7",
        'LATITUDE': "31.17140",
        'LONGITUDE': "35.58510",
        'NOTES': "Elevation from Google Elevation Service.",
    }
    contribution = {} # no contributor listed
    components = [
        {'PERIOD': "Unspecified", 'FEATURE TYPE': "Sherd / Flint Scatter", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Middle Paleolithic/Mousterian", 'FEATURE TYPE': "Sherd / Flint Scatter", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Iron IIa/b", 'FEATURE TYPE': "Sherd / Flint Scatter (Uncertain Presence)", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Iron IIc", 'FEATURE TYPE': "Sherd / Flint Scatter (Uncertain Presence)", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
        {'PERIOD': "Late Byzantine", 'FEATURE TYPE': "Sherd / Flint Scatter", 'SIZE (ha)': "0", 'DESCRIPTION': ""},
    ]
    condition_report = {
        'OVERALL CONDITION': "No Information",
        'OVERALL RATING': "Site Destroyed (Excavation impossible)",
        'CUMULATIVE RISK': "Unknown / Not Noted",
        'SEVERITY OF RISK': "Unknown",
        'DATE VISITED': "1993-03-06",
        # no ENTERED BY key
        'DATE ENTERED': "1993-03-06",
    }


if __name__ == "__main__":
    import unittest
    unittest.main()
