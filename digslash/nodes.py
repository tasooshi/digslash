import hashlib
import urllib.parse

import bs4

from digslash import logger


class Node:

    ACCEPTED_ELEMENT_ATTRS = (
        ('a', 'href'),
        ('script', 'src'),
        ('iframe', 'src'),
        ('form', 'action'),
    )

    def __init__(self, site, content, content_type='text/html', encoding='ascii', current=None):
        self.site = site
        self.content_type = content_type
        self.encoding = encoding
        self.results = set()
        self.discarded = set()
        self._checksum = None
        if current is None:
            self.current = self.site.urlsplit
        else:
            self.current = urllib.parse.urlsplit(current)
        try:
            self.content = content.decode(self.encoding)
        except Exception as exc:
            logger.warning(exc)
            self.content = None
        else:
            self.parser = bs4.BeautifulSoup(content, 'html.parser')

    def extract_links(self):
        if self.content_type in ['text/html']:
            for elem, attr in self.ACCEPTED_ELEMENT_ATTRS:
                for ele in self.parser.find_all(elem):
                    try:
                        self.results.add(ele[attr])
                    except KeyError:
                        pass

    def links_filter(self):
        refined = set()
        for link in self.results:
            url = urllib.parse.urlparse(link)
            if url.scheme not in ['http', 'https'] and url.scheme != '':
                self.discarded.add(link)
            elif url.netloc == self.current.netloc or url.netloc == '':
                refined.add(link)
            else:
                self.discarded.add(link)
        self.results = refined

    def links_rebase(self):
        refined = set()
        for link in self.results:
            split_url = urllib.parse.urlsplit(link)
            refined.add(
                urllib.parse.urljoin(
                    self.current.geturl(), urllib.parse.SplitResult('', '', split_url.path, split_url.query, split_url.fragment).geturl()
                )
            )
        self.results = refined

    @property
    def checksum(self):
        if self._checksum is None:
            self._checksum = hashlib.md5(self.content.encode(self.encoding)).hexdigest()
        return self._checksum

    def process(self):
        if self.content is None:
            raise Exception('No content to process, binary?')
        self.extract_links()
        self.links_filter()
        self.links_rebase()
        return {
            'encoding': self.encoding,
            'content_type': self.content_type,
            'checksum': self.checksum,
            'links': self.results,
        }
