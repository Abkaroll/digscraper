import random

from requests import Session
from concurrent import futures
from time import sleep
import logging
import os
import datetime as dt
import re
from collections import defaultdict
from pprint import pprint

logger = logging.getLogger(__name__)

session = Session()





class SiteInfo(object):
    BASE_URL = 'http://www.megajordan.org/Reports/'
    PAGE_URLS = [
        'SiteGeneral',
        'SiteSignificance',
        'SiteSiteElements',
        'SiteAdministration',
        'SiteMonitoringEvents',
        'SiteReferences',
    ]
    HERE = os.path.dirname(__file__)
    RESULTS_DIR = os.path.join(HERE, "results")
    FAILURE_DIR = os.path.join(RESULTS_DIR, 'failure')
    for DIR in [RESULTS_DIR, FAILURE_DIR]:
        try:
            os.mkdir(DIR)
        except OSError:
            pass
    def __init__(self, gid):
        self.gid = gid

    def save_page(self, url, timeout=None):
        """
        A function to perform one unit of work: Make a request, save the response.
        """
        # Expects a URL in the format "http://example.com/path/<resource>?gid=<gid>

        base, gid = url.split('=')
        base, _ = base.split("?")
        resource = base.split("/")[-1]
        r = session.request('GET', url, timeout=timeout)
        # Construct filename differently based on success/failure
        if r.ok:
            try:
                os.mkdir("{}/{}".format(self.RESULTS_DIR, gid))
            except OSError:
                pass
            filename = "{}/{}/{}-{}.html".format(self.RESULTS_DIR, gid, gid, resource)
        else:
            filename = "{}/{}-{}-{}.html".format(self.FAILURE_DIR, r.status_code, gid, resource)

        # Write it out regardless of status code
        with open(filename, 'w', encoding='UTF-8') as fh:
            fh.write(r.text)
        return r

    @property
    def all(self):
        """
        Returns a list of all page urls for a given GID
        """
        resources = self.PAGE_URLS
        return ["{}{}?gid={}".format(self.BASE_URL, page, self.gid) for page in resources]
    
    @property
    def done(self):
        pages = []
        for basename in os.listdir(os.path.join(self.RESULTS_DIR, str(self.gid))):
                gid, page = basename.split('-')
                page = page.replace(".html", "")
                pages.append("{}{}?gid={}".format(self.BASE_URL, page, self.gid))
        return pages
    
    @property
    def to_do(self):
        all = self.all
        done = self.done
        return [p for p in all if p not in done]
    
    def run(self):
        for p in self.to_do:
            self.save_page(p)
        
        


def all_urls(start=0, stop=1):
    """
    Construct a list of all target URLs on the megajordan system.
    """
    gids = list(range(start, stop))
    for gid in gids:
        g = SiteInfo(gid)
        for url in g.all:
            yield url


def finished_urls():
    finished = [basename for basename in os.listdir(SiteInfo.RESULTS_DIR)]
    finished_urls = []
    for gid in finished:
        finished_urls.extend(SiteInfo(gid).done)
    return finished_urls


def partially_complete(start=102, stop=15000):
    at_least_some_data = [gid for gid in os.listdir(SiteInfo.RESULTS_DIR)]
    targets = []
    for gid in at_least_some_data:
        targets.extend(SiteInfo(gid).to_do)
    return targets

  
def tried_already():
    errors = []
    success = []
    with open('finished.txt') as fh:
        for l in fh.readlines():
            if " 200 " in l:
                success.append(re.search(r'(http://.*=\d+)', l).group(1))
            elif " 500 " in l:
                errors.append(re.search(r'(http://.*=\d+)', l).group(1))
    return success

 
    
if __name__ == "__main__":

  with open('finished.txt', 'a+') as fh:
    # Enumerate what we've already done
    print("Missing GIDs:      {}".format(len(range(102, 13000)) - len(os.listdir(SiteInfo.RESULTS_DIR))))
    all = all_urls(102, 13000)
    print("All urls:          {}".format(len(list(all))))
    
    finished = finished_urls()
    print("Finished:          {}".format(len(finished)))
    
    tried = tried_already()

    # Grab the list of URLS to work on.
    missing_urls = set(all) - set(finished) # - set(tried)
    print("Missing:           {}".format(len(missing_urls)))
	
    partials = partially_complete(start=102, stop=13000)
    random.shuffle(partials)
    print("Partially Missing: {}".format(len(partials)))
	
    target_urls = partials + [u for u in missing_urls if u not in partials]
    target_count = len(target_urls)
	
    print("Target URLS:       {}".format(len(target_urls)))
    # print("\n".join(target_urls))
    
    URLS = [u for u in target_urls if u not in finished]
    print("Left: {}".format(len(URLS)))
    successes = len(finished)
    total = successes + target_count
    failures = 0

    # raise Exception
    backoff = 1  # second
    # Start the load operations and mark each future with its URL
	
    while URLS:
        url = URLS.pop()
        try:
            start = dt.datetime.now()
            r = SiteInfo(None).save_page(url, 60)
            successes += 1
        except Exception as exc:
            finish = dt.datetime.now()
            print('[%s] backoff %s; %r generated an exception: %s' % (dt.datetime.now(), backoff, url, exc))
            backoff *= 2
            backoff = min(backoff, 60 * 60)
            sleep(backoff)
            failures += 1
            URLS.append(url)
        else:
            finish = dt.datetime.now()
            backoff = .1 #max(backoff / 2, 0.5)
            sleep(backoff)
            message = "[{}] {}/{}/{} ({:.2f}%) {} ({:.2f}s|{}s) {}".format(
                dt.datetime.now(), successes, failures, total,
                100 * float(successes) / total,
                r.status_code, (finish - start).total_seconds(), backoff, r.url
            )
            fh.write(message + "\n")
            print(message)



