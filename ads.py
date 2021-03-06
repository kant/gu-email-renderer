import logging, re

from google.appengine.api import urlfetch



class AdFetcher(object):
    """
    Class to fetch advert html from OAS.
    """
    def __init__(self, tag):
        self.root_url = "http://oas.theguardian.com/RealMedia/ads/adstream_sx.ads/" + tag + "/1234567890"

    def fetch_html(self, ad_type):
        """
        Fetches the raw ad html from OAS
        """
        ad_url = self.root_url + "@" + ad_type

        response = None
        try:
            response = urlfetch.fetch(ad_url)
        except urlfetch.DeadlineExceededError as de:
            logging.error("OAS call failed, returning no ad slots")
            logging.error(de)
            return None

        if response.status_code == 200:
            content = re.sub(r'width="\d{1,}" height="\d{1,}"', 'width="100%"', response.content)

            # Adserver will return a 200 even if an advert is missing,
            # in which case the advert will be a single-pixel transparent gif,
            # let's just not bother with it
            if 'empty.gif' in content:
                logging.info("OAS returned an empty gif")
                return None
            else:
                return content
        else:
            logging.error("Failed to fetch ad: status code %s, content '%s'" % (response.status_code, response.content))
            return ''

    def fetch_type(self, type):
        """
        Returns an advert by type, use a string e.g. as follows:
         - 'Top' (leaderboard)
         - 'Bottom' (leaderboard)
         - 'x01' (square)
         - 'Right1' (skyscraper)
        """
        return self.fetch_html(type)
