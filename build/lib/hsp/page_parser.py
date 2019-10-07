from bs4 import BeautifulSoup


def xpath_soup(element):
    components = []
    child = element if element.name else element.parent
    for parent in child.parents:
        siblings = parent.find_all(child.name, recursive=False)
        components.append(
            child.name
            if siblings == [child] else
            '%s[%d]' % (child.name, 1 + siblings.index(child))
            )
        child = parent
    components.reverse()
    return '/%s' % '/'.join(components)


def booking_button_xpath(page_source, course_id):
    soup = BeautifulSoup(page_source, "html.parser")
    booking_button = soup.find("a", {"id": course_id}).find_next_sibling()
    return xpath_soup(booking_button)
