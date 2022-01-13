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


# TODO: A "website" factory here?


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


@pytest.fixture
def website2_with_body():
    web_dir = get_dir('website-2')
    httpd = server.HTTPServer(
        ('127.0.0.1', 8000),
        functools.partial(server.SimpleHTTPRequestHandler, directory=web_dir)
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    site = sites.Site('http://127.0.0.1:8000/', store_content=True)
    yield site
    httpd.server_close()
    httpd.shutdown()
    httpd_thread.join()


@pytest.fixture
def website2_with_body_with_duplicates():
    web_dir = get_dir('website-2')
    httpd = server.HTTPServer(
        ('127.0.0.1', 8000),
        functools.partial(server.SimpleHTTPRequestHandler, directory=web_dir)
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    site = sites.Site('http://127.0.0.1:8000/', store_content=True, deduplicate=False)
    yield site
    httpd.server_close()
    httpd.shutdown()
    httpd_thread.join()


@pytest.fixture
def website2_with_headers():
    web_dir = get_dir('website-2')
    httpd = server.HTTPServer(
        ('127.0.0.1', 8000),
        functools.partial(server.SimpleHTTPRequestHandler, directory=web_dir)
    )
    httpd_thread = threading.Thread(target=httpd.serve_forever)
    httpd_thread.daemon = True
    httpd_thread.start()
    site = sites.Site('http://127.0.0.1:8000/', store_headers=True)
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


def test_site_response_body_in_results(website2_with_body):
    asyncio.run(website2_with_body.crawl())
    assert website2_with_body.results == {
        'http://127.0.0.1:8000/': {
            'source': '',
            'encoding': 'utf-8',
            'checksum': '4d651f294542b8829a46d8dc191838bd',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    <ul>\n        <li><a href="page.html">Page</a></li>\n        <li><a href="binary.exe">Binary</a></li>\n        <li><a href="image.png">Image</a></li>\n    </ul>\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/page.html': {
            'source': 'http://127.0.0.1:8000/',
            'encoding': 'latin_1',
            'checksum': 'f8f1acd16e78bf0b9b13cd90567c68c2',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="iso-8859-1">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website - Page</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    Test!\n    <script type="text/javascript" src="code.js"></script>\n    <a href="#1a7273747da4797577">Ignore</a>\n    <a href="page2.html#1a7273747da4797577">Ignore</a>\n    <a href="?arg=2">Follow</a>\n    <a href="page2.html?arg=2">Follow</a>\n    <a href="\\\'https:/example.com/\\\'">Ignore</a>\n    <a href="page2.html\\\'https:/example.com/\\\'">Ignore</a>\n    <a href="\' + SOMETHING + \'">Ignore</a>\n    <a href="page2.html\' + SOMETHING + \'">Ignore</a>\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/page2.html?arg=2': {
            'source': 'http://127.0.0.1:8000/page.html',
            'encoding': 'latin_1',
            'checksum': '1e9b0ff7d25ad34037f3f8bd5b92b434',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="iso-8859-1">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website - Page 2</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    Test 2!\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/code.js': {
            'source': 'http://127.0.0.1:8000/page.html',
            'encoding': 'ascii',
            'checksum': 'b4577eafb339aab8076a1e069e62d2c5',
            'body': b'alert("Test!");'
        }
    }


def test_site_response_body_in_results_with_duplicates(website2_with_body_with_duplicates):
    asyncio.run(website2_with_body_with_duplicates.crawl())
    assert website2_with_body_with_duplicates.results == {
        'http://127.0.0.1:8000/': {
            'source': '',
            'encoding': 'utf-8',
            'checksum': '4d651f294542b8829a46d8dc191838bd',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="utf-8">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    <ul>\n        <li><a href="page.html">Page</a></li>\n        <li><a href="binary.exe">Binary</a></li>\n        <li><a href="image.png">Image</a></li>\n    </ul>\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/page.html': {
            'source': 'http://127.0.0.1:8000/',
            'encoding': 'latin_1',
            'checksum': 'f8f1acd16e78bf0b9b13cd90567c68c2',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="iso-8859-1">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website - Page</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    Test!\n    <script type="text/javascript" src="code.js"></script>\n    <a href="#1a7273747da4797577">Ignore</a>\n    <a href="page2.html#1a7273747da4797577">Ignore</a>\n    <a href="?arg=2">Follow</a>\n    <a href="page2.html?arg=2">Follow</a>\n    <a href="\\\'https:/example.com/\\\'">Ignore</a>\n    <a href="page2.html\\\'https:/example.com/\\\'">Ignore</a>\n    <a href="\' + SOMETHING + \'">Ignore</a>\n    <a href="page2.html\' + SOMETHING + \'">Ignore</a>\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/page.html?arg=2': {
            'source': 'http://127.0.0.1:8000/page.html',
            'encoding': 'latin_1',
            'checksum': 'f8f1acd16e78bf0b9b13cd90567c68c2',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="iso-8859-1">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website - Page</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    Test!\n    <script type="text/javascript" src="code.js"></script>\n    <a href="#1a7273747da4797577">Ignore</a>\n    <a href="page2.html#1a7273747da4797577">Ignore</a>\n    <a href="?arg=2">Follow</a>\n    <a href="page2.html?arg=2">Follow</a>\n    <a href="\\\'https:/example.com/\\\'">Ignore</a>\n    <a href="page2.html\\\'https:/example.com/\\\'">Ignore</a>\n    <a href="\' + SOMETHING + \'">Ignore</a>\n    <a href="page2.html\' + SOMETHING + \'">Ignore</a>\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/page2.html?arg=2': {
            'source': 'http://127.0.0.1:8000/page.html',
            'encoding': 'latin_1',
            'checksum': '1e9b0ff7d25ad34037f3f8bd5b92b434',
            'body': b'<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="iso-8859-1">\n    <meta name="viewport" content="width=device-width, initial-scale=1">\n    <title>Website - Page 2</title>\n    <link rel="stylesheet" type="text/css" href="style.css">\n</head>\n<body>\n    Test 2!\n</body>\n</html>'
        },
        'http://127.0.0.1:8000/code.js': {
            'source': 'http://127.0.0.1:8000/page.html',
            'encoding': 'ascii',
            'checksum': 'b4577eafb339aab8076a1e069e62d2c5',
            'body': b'alert("Test!");'
        }
    }


def test_site_response_headers_in_results(website2_with_headers):
    asyncio.run(website2_with_headers.crawl())
    for result in website2_with_headers.results.values():
        assert 'headers' in result
