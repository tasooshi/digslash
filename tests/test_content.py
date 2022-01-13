import pytest

from digslash import (
    nodes,
    sites,
)


@pytest.fixture
def site():
    site = sites.Site('https://example.com')
    yield site


def test_html_href_src_attrs(site):
    text = b"""
        <link rel="shortcut icon" href="https://cdn.example.com/favicon.ico?v=123456">
        <link rel="stylesheet" type="text/css" href="https://cdn.example.com/default.css?v=123456">
        <a href="pages/about.html">About</a>
        <script src="https://example.com/vendor/jquery/jquery.min.js"></script>
        <script src="http://example.com/vendor/jquery/jquery.min.js"></script>
        <script src="http://example.net/vendor/jquery/jquery.js"></script>
        <script src="/vendor/bootstrap/js/bootstrap.min.js?v=123456"></script>
        <img src="images/example.png">
    """
    currentNode = nodes.Node(site, text, current='https://example.com/home.html')
    results = currentNode.process()
    assert results == {
        'checksum': '9ea017abcc86e3ee381538bc47206b46',
        'encoding': 'ascii',
        'links': {
            'https://example.com/pages/about.html',
            'https://example.com/vendor/bootstrap/js/bootstrap.min.js?v=123456',
            'https://example.com/vendor/jquery/jquery.min.js',
        }
    }


def test_html_href_src_attrs_relative(site):
    text = b"""
        <h1>About</h1>
        <a href="../home.html">Home</a>
        <a href="contact.html">Contact</a>
        <a href="http://example.net/../home.html">External</a>
        <script src="../vendor/jquery/jquery.min.js"></script>
        <link rel="stylesheet" href="../vendor/bootstrap/css/bootstrap.min.css">
    """
    node = nodes.Node(site, text, current='https://example.com/pages/about.html')
    results = node.process()
    assert results == {
        'checksum': '94a6bd23a18f0cb18f49ef0f69bc5516',
        'encoding': 'ascii',
        'links': {
            'https://example.com/home.html',
            'https://example.com/pages/contact.html',
            'https://example.com/vendor/jquery/jquery.min.js',
        }
    }


def test_html_form_action(site):
    text = b"""
        <form action="contact.php" method="GET">
            <label for="field">Field value:</label>
            <input type="text" id="field" name="field">
            <input type="submit" value="Submit">
        </form>
        <form action="/contact2.php" method="POST">
            <label for="field">Field value:</label>
            <input type="text" id="field" name="field">
            <input type="submit" value="Submit">
        </form>
        <form action="../contact3.php" method="GET">
            <label for="field">Field value:</label>
            <input type="text" id="field" name="field">
            <input type="submit" value="Submit">
        </form>
    """
    node = nodes.Node(site, text, current='https://example.com/pages/contact.html')
    results = node.process()
    assert results == {
        'checksum': '342adbdb08d4677d6f2b05bb7dfe5e76',
        'encoding': 'ascii',
        'links': {
            'https://example.com/contact2.php',
            'https://example.com/contact3.php',
            'https://example.com/pages/contact.php',
        }
    }


def test_html_href_ignore_other_protocols(site):
    text = b"""
        <a href="mailto:test@example.com">
        <a href="tel:555555551">
        <a href="callto:555555552">
        <a href="/">
        <a href="sms:555555553">
        <a href="fax:555555554">
    """
    node = nodes.Node(site, text, current='https://example.com/pages/about.html')
    results = node.process()
    assert results == {
        'checksum': 'f0a9dfc704377cca6207f3f204c49fd6',
        'encoding': 'ascii',
        'links': {
            'https://example.com/',
        }
    }


def test_html_no_quotes(site):
    text = b"""
        <a href=pages/about.html>About</a>
        <script src=https://example.com/vendor/jquery/jquery.min.js></script>
        <script src=//example.com/vendor/jquery/jquery.js></script>
        <script src=//example.net/vendor/jquery/jquery.js></script>
    """
    node = nodes.Node(site, text)
    results = node.process()
    assert results == {
        'checksum': '278c75659ec8d5a6b493664e608faf68',
        'encoding': 'ascii',
        'links': {
            'https://example.com/pages/about.html',
            'https://example.com/vendor/jquery/jquery.js',
            'https://example.com/vendor/jquery/jquery.min.js',
        }
    }
