

'''
returns title, author. Strips whitespace before returning
Assumptions:
1. That the title is stored in the div class 'col'
2. Format of the retrieved text is <title> by <author>
'''

def get_title_and_author(soup):
    title_and_author_container = soup.find_all('div', class_='col')
    return title_and_author_container[0].text.split('by')[0].strip(), title_and_author_container[0].text.split('by')[1].strip()

'''
Returns a dict containing all relevant statistics in the fiction page
'''
def get_stats(soup):
    stats = {}
    stats['overall_score'] = soup.find('span', {'data-original-title': 'Overall Score'}).attrs['data-content']
    stats['style_score'] = soup.find('span', {'data-original-title': 'Style Score'}).attrs['data-content']
    stats['story_score'] = soup.find('span', {'data-original-title': 'Story Score'}).attrs['data-content']
    stats['grammar_score'] = soup.find('span', {'data-original-title': 'Grammar Score'}).attrs['data-content']
    stats['character_score'] = soup.find('span', {'data-original-title': 'Character Score'}).attrs['data-content']
    # Relevant info is in the second list element ('li') on the page
    numerical_stats = soup.find_all('div', class_='col-sm-6')[1].find_all('li')
    stat_keys = [x.text.replace(':', ' ').strip().replace(' ', '_').lower() for x in numerical_stats[::2]]
    stat_values = [x.text.strip().replace(',', '') for x in numerical_stats[1::2]]
    for idx, key in enumerate(stat_keys):
        stats[key] = stat_values[idx]

    return stats
    
            




