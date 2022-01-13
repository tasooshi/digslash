import asyncio
import urllib.parse
import ssl
from collections import defaultdict

import aiohttp

from digslash import (
    logger,
    nodes,
)


class Site:

    ACCEPTED_CONTENT_TYPES = (
        'text/html',
        'text/xml',
        'text/plain',
        'text/javascript',
        'application/javascript',
        'application/json',
        'application/xml',
        'application/xhtml+xml',
        'application/octet-stream',
    )

    PATHS_IGNORED = (
        ' + ',
        '\'+',
        '+\'',
        '\\\'',
        '#',
    )

    def __init__(self,
        base,
        deduplicate=True,
        workers_no=16,
        limit=100,
        store_content=False,
        store_headers=False,
        accepted_content_types=ACCEPTED_CONTENT_TYPES,
        ignored_status_codes=None,
        verify_ssl=True,
        body_limit=1000000,
        paths_ignored=PATHS_IGNORED
    ):
        self.base = base
        self.urlsplit = urllib.parse.urlsplit(base)
        self.deduplicate = deduplicate
        self.workers_no = workers_no
        self.limit = limit
        self.queue = None
        self.results = defaultdict(dict)
        self.workers = list()
        self.checksums_index = dict()
        self.store_content = store_content
        self.accepted_content_types = accepted_content_types
        self.ignored_status_codes = tuple() if not ignored_status_codes else ignored_status_codes
        self.verify_ssl = verify_ssl
        self.body_limit = body_limit
        self.paths_ignored = paths_ignored
        self.store_headers = store_headers
        self.ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        self.ssl_context.check_hostname = False
        if not verify_ssl:
            self.ssl_context.verify_mode = ssl.CERT_NONE

    async def worker(self):
        while self.is_populated():
            if self.limit and len(self.results) >= self.limit:
                self.queue_flush()
                break
            url, source = await self.queue.get()
            logger.info('Processing {}'.format(url))
            response = await self.fetch(url)
            if response:
                body, encoding, headers = response
                node = nodes.Node(self, body, encoding, current=url)
                results = node.process()
                if results:
                    self.done(url, source, results, body, headers)
                    self.queue_add(results['links'], url)
            self.worker_done()

    def worker_done(self):
        self.queue.task_done()

    def done(self, url, source, results, body, headers):
        entry = {
            'source': source,
            'encoding': results['encoding'],
            'checksum': results['checksum'],
        }
        if self.store_content:
            entry['body'] = body
        if self.store_headers:
            entry['headers'] = headers
        if self.deduplicate:
            if results['checksum'] not in self.checksums_index:
                self.results[url] = entry
                self.checksums_index[results['checksum']] = url
        else:
            self.results[url] = entry

    def queue_flush(self):
        for _ in range(self.queue.qsize()):
            self.queue.get_nowait()
            self.queue.task_done()

    def queue_add(self, url_list, source=''):
        for url in url_list:
            if (
                url not in self.results and
                url not in dict(self.queue._queue) and  # FIXME: Optimize
                url != source
            ):
                logger.debug('Added to queue: ' + url)
                self.queue.put_nowait((url, source))

    def is_populated(self):
        return not self.queue.empty()

    def handle_worker_result(self, worker):
        try:
            worker.result()
        except asyncio.CancelledError:
            pass
        except Exception:
            logger.exception('Exception raised by {}'.format(worker))

    async def crawl(self):
        self.queue = asyncio.Queue()
        for i in range(self.workers_no):
            worker = asyncio.create_task(self.worker())
            worker.add_done_callback(self.handle_worker_result)
            self.workers.append(worker)
        # Initialize queue with the base URL
        self.queue_add([self.base])
        await self.queue.join()

    async def stop(self):
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers)
        self.workers = None

    async def fetch(self, url):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, ssl_context=self.ssl_context) as response:
                    body = await response.read()
                    if response.status not in self.ignored_status_codes:
                        content_type = response.content_type.split(';')[0]
                        if response.content_type in self.accepted_content_types:
                            logger.debug('Received response with Content-Type {} for {}'.format(response.content_type, url))
                            return body[:self.body_limit], response.get_encoding(), dict(response.headers)
                        else:
                            logger.debug('Unsupported Content-Type {}'.format(response.content_type))
                    else:
                        logger.debug('Status {}, skip processing'.format(response.status))
            except Exception as exc:
                logger.debug('Exception {}, skip processing'.format(exc))
