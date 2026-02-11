import requests
import os
from dotenv import load_dotenv

from sopp.tle_fetcher.tle_fetcher_base import TleFetcherBase

load_dotenv()
IDENTITY = os.getenv("IDENTITY")
PASSWORD = os.getenv("PASSWORD")


class TleFetcherSpacetrack(TleFetcherBase):
    def _fetch_content(self):
        url = 'https://www.space-track.org/ajaxauth/login'
        query = 'https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/epoch/%3Enow-30/orderby/norad_cat_id/format/3le'
        data = {'identity': IDENTITY, 'password': PASSWORD, 'query': query}
        return requests.post(url=url, data=data)
