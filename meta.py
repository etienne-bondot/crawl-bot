def extractMeta(soup):
    metatags = soup.find_all('meta')
    metadata = {
        'description': '',
        'keywords': '',
    }

    print(metatags)

    for tag in metatags:
        if tag.get('name') == 'description':
            metadata['description'] = tag.get('content')
        elif tag.get('name') == 'keywords':
            metadata['keywords'] = tag.get('content').split(',')

    return metadata
