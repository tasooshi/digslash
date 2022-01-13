# digslash

> A site mapping and enumeration tool for Web applications analysis

Usage:

    >>> import asyncio
    >>> from digslash import sites
    >>> website = sites.Site('https://example.com', limit=50, deduplicate=False)
    >>> asyncio.run(website.crawl())

Output example:

    >>> dict(website.results)
    {
        'https://example.com/': {
            'checksum': '17913e89fe23ba03081f5f5b650c29a0',
            'encoding': 'utf-8',
            'source': ''
        },
        'https://example.com/js/script.js': {
            'checksum': '4cdad7e5affe29e1347343e126beea09',
            'encoding': 'ascii',
            'source': 'https://example.com/'
        },
        'https://example.com/pages/about.html': {
            'checksum': 'fad033d51adc628b17268ce2669543fd',
            'encoding': 'utf-8',
            'source': 'https://example.com/'
        },
        'https://example.com/pages/contact.html': {
            'checksum': 'b12c6a2fde381552564eea6a477030f0',
            'encoding': 'utf-8',
            'source': 'https://example.com/'
        },
        'https://example.com/pages/feedback.html': {
            'checksum': '9b0482107470956f7b64c833f1ef5e59',
            'encoding': 'utf-8',
            'source': 'https://example.com/'
        },
        'https://example.com/scripts/feedback.html': {
            'checksum': 'b92c8a06f3d4a9c22e8c11606bcbd2f7',
            'encoding': 'utf-8',
            'source': 'https://example.com/pages/feedback.html'
        }
    }
