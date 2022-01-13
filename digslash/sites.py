import asyncio
import urllib.parse
from collections import defaultdict

import aiohttp

from digslash import (
    logger,
    nodes,
)


class Site:

    ACCEPTED_CONTENT_TYPES = [
        'text/html',
        'text/xml',
        'test/plain',
        'test/javascript',
        'application/javascript',
        'application/json',
        'application/xml',
        'application/xhtml+xml',
    ]

    def __init__(self, base, deduplicate=True, workers_no=16, limit=200):
        self.base = base
        self.urlsplit = urllib.parse.urlsplit(base)
        self.deduplicate = deduplicate
        self.workers_no = workers_no
        self.limit = limit
        self.queue = None
        self.results = defaultdict(dict)
        self.workers = list()
        self.checksums_index = dict()

    async def worker(self):
        while self.is_populated():
            if len(self.results) <= self.limit:
                url, source = await self.queue.get()
                logger.info('Processing {}'.format(url))
                response = await self.fetch(url)
                if response:
                    body, content_type, encoding = response
                    node = nodes.Node(self, body, content_type, encoding)
                    results = node.process()
                    self.done(url, source, results)
                    self.queue_add(results['links'], url)
                self.worker_done()
            else:
                self.queue_flush()

    def worker_done(self):
        self.queue.task_done()

    def done(self, url, source, results):
        entry = {
            'source': source,
            'encoding': results['encoding'],
            'content_type': results['content_type'],
            'checksum': results['checksum'],
        }
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
            if url not in self.results and url not in dict(self.queue._queue):  # FIXME: Optimize
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

    async def start(self):
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
            async with session.get(url) as response:
                body = await response.read()
                if response.status not in [404, 403]:
                    if response.content_type in self.ACCEPTED_CONTENT_TYPES:
                        return body, response.content_type, response.get_encoding()

    def crawl(self):
        asyncio.run(self.start())
        logger.debug(self.results)
