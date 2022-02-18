import asyncio
import functools
import pathlib
import threading
from http import server

import pytest

from digslash import sites


def get_dir(dirname):
    return pathlib.os.path.join(
        pathlib.os.path.dirname(__file__),
        dirname
    )


@pytest.fixture
def website1():
    web_dir = get_dir('website-1')
    httpd = server.HTTPServer(
        ('127.0.0.1', 8000),
        functools.partial(server.SimpleHTTPRequestHandler, directory=web_dir)
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    site = sites.Site('http://127.0.0.1:8000/')
    yield site
    httpd.server_close()
    httpd.shutdown()
    httpd_thread.join()


@pytest.fixture
def website1_with_duplicates():
    web_dir = get_dir('website-1')
    httpd = server.HTTPServer(
        ('127.0.0.1', 8000),
        functools.partial(server.SimpleHTTPRequestHandler, directory=web_dir)
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    site = sites.Site('http://127.0.0.1:8000/', deduplicate=False)
    yield site
    httpd.server_close()
    httpd.shutdown()
    httpd_thread.join()


@pytest.fixture
def website2():
    web_dir = get_dir('website-2')
    httpd = server.HTTPServer(
        ('127.0.0.1', 8000),
        functools.partial(server.SimpleHTTPRequestHandler, directory=web_dir)
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    site = sites.Site('http://127.0.0.1:8000/')
    yield site
    httpd.server_close()
    httpd.shutdown()
    httpd_thread.join()


def test_handle_duplicates(website1):
    asyncio.run(website1.crawl())
    assert set(website1.results.keys()) == {
        'http://127.0.0.1:8000/',
        'http://127.0.0.1:8000/pages/contact.html',
        'http://127.0.0.1:8000/pages/about.html',
        'http://127.0.0.1:8000/pages/feedback.html',
        'http://127.0.0.1:8000/js/script.js',
        'http://127.0.0.1:8000/scripts/feedback.html',
    }


def test_keep_duplicates(website1_with_duplicates):
    asyncio.run(website1_with_duplicates.crawl())
    assert set(website1_with_duplicates.results.keys()) == {
        'http://127.0.0.1:8000/',
        'http://127.0.0.1:8000/pages/contact.html',
        'http://127.0.0.1:8000/pages/about.html',
        'http://127.0.0.1:8000/pages/feedback.html',
        'http://127.0.0.1:8000/js/script.js',
        'http://127.0.0.1:8000/scripts/feedback.html',
        'http://127.0.0.1:8000/index.html',
    }


def test_site_response_content_type(website2):
    asyncio.run(website2.crawl())
    assert website2.results == {
        'http://127.0.0.1:8000/': {
            'checksum': '4d651f294542b8829a46d8dc191838bd',
            'content_type': 'text/html',
            'encoding': 'utf-8',
            'source': '',
        },
        'http://127.0.0.1:8000/code.js': {
            'checksum': 'b4577eafb339aab8076a1e069e62d2c5',
            'content_type': 'application/javascript',
            'encoding': 'ascii',
            'source': 'http://127.0.0.1:8000/page.html',
        },
        'http://127.0.0.1:8000/page.html': {
            'checksum': '091ee4d646a8e62a6bb4092b439b07a1',
            'content_type': 'text/html',
            'encoding': 'latin_1',
            'source': 'http://127.0.0.1:8000/',
        }
    }
