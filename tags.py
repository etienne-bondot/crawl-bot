def extractTags(soup):
    tags = {
        'h1_headings': '',
        'h2_headings': ''
    }
    tags['h1_headings'] = [heading.text.strip()
                           for heading in soup.find_all('h1')]
    tags['h2_headings'] = [heading.text.strip()
                           for heading in soup.find_all('h2')]

    return tags
