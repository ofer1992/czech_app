from lxml import html
import requests
import json
from tqdm import tqdm

OVERLOADED_STRING = "Some other request from your IP address is still evaluated"
class ServerOverloaded(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "server overloaded... word: "+repr(self.value)

def get_declension_table(word):
    """
    scrapes declension table from site, returns dict of
    case: [singular, plural]
    """
    page = requests.get('http://prirucka.ujc.cas.cz/en/?id='+word)
    tree = html.fromstring(page.content)
    if OVERLOADED_STRING in tree.text_content():
        raise ServerOverloaded(word)
    table = tree.xpath('//table[@class="para"]')[0]
    rows = table.getchildren()
    d = {}
    for i, r in enumerate(rows[1:]):
        cells = [c.text_content() for c in r.getchildren()]
        case = cells[0]
        sg = cells[1]
        pl = cells[2]
        d[case] = [sg, pl]

    return d


if __name__ == "__main__":
    with open('processed.txt') as f:
        words = f.readlines()
        words = [w.split() for w in words]
    to_json = {}
    failed_words = {}
    for w in tqdm(words):
        cz = w[0]
        en = w[1]
        to_json[cz] = {"en": en}
        try:
            dec = get_declension_table(cz)
            to_json[cz]["declension"] = dec
        except (IndexError, requests.ConnectTimeout) as e:
            failed_words[cz] = e
            print cz
        except ServerOverloaded as e:
            print e
            print "terminating"
            break
    with open("db.json", 'w') as f:
        json.dump(to_json, f)
    print failed_words 
    if failed_words:
        with open("failed.txt", 'w') as f:
            f.write(failed_words.keys())

