import hashlib
import urllib.parse

import bs4

from digslash import logger


class Node:

    FOLLOWED_ELEMENTS_ATTRS = (
        ('a', 'href'),
        ('script', 'src'),
        ('iframe', 'src'),
        ('form', 'action'),
    )

    def __init__(self, site, content, encoding='ascii', current=None):
        self.site = site
        self.encoding = encoding
        self.results = set()
        self._checksum = None
        if current:
            self.current = urllib.parse.urlsplit(current)
        else:
            self.current = self.site.urlsplit
        try:
            self.content = content.decode(self.encoding)
        except Exception as exc:
            logger.debug(f'Cannot decode due {current} to {exc}')
            self.content = None
        else:
            self.parser = bs4.BeautifulSoup(content, 'html.parser')

    def extract_links(self):
        for elem, attr in self.FOLLOWED_ELEMENTS_ATTRS:
            for ele in self.parser.find_all(elem):
                try:
                    self.results.add(ele[attr])
                except KeyError:
                    pass

    def links_filter(self):
        refined = set()
        for link in self.results:
            url = urllib.parse.urlparse(link)
            discard = False
            if url.scheme not in ['http', 'https'] and url.scheme != '':
                discard = True
            for sep in self.site.paths_ignored:
                if sep in url.path or (not url.netloc and sep in link):
                    discard = True
                    break
            if not discard and (url.netloc == self.current.netloc or not url.netloc):
                refined.add(link)
        self.results = refined

    def links_rebase(self):
        refined = set()
        for link in self.results:
            split_url = urllib.parse.urlsplit(link)
            rebased_url = urllib.parse.urljoin(
                self.site.base, urllib.parse.SplitResult('', '', split_url.path, split_url.query, split_url.fragment).geturl()
            )
            refined.add(rebased_url)
        self.results = refined

    @property
    def checksum(self):
        if self._checksum is None:
            self._checksum = hashlib.md5(self.content.encode(self.encoding)).hexdigest()
        return self._checksum

    def process(self):
        if self.content is None:
            return
        self.extract_links()
        self.links_filter()
        self.links_rebase()
        return {
            'encoding': self.encoding,
            'checksum': self.checksum,
            'links': self.results,
        }
