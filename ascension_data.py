import requests
from bs4 import BeautifulSoup
import json
import re

def get_chara_link():
    url_ROOT = "https://genshin-impact.fandom.com/wiki/Category:Playable_Characters"
    res = requests.get(url_ROOT)
    sp = BeautifulSoup(res.content, 'html.parser')

    chara_links = []
    for link in sp.select('.category-page__member-link'):
        href = link.get('href')
        chara_url = f"https://genshin-impact.fandom.com{href}"
        chara_links.append(chara_url)
    
    chara_links = chara_links[5:]
    return chara_links


def get_table_data(chara_links):
    
    res = requests.get(chara_links)
    sp_table = BeautifulSoup(res.content, 'html.parser')
    table_data = sp_table.select_one('table.wikitable.ascension-stats')
    chara_name= sp_table.select_one('h1.page-header__title').get_text(strip=True) if sp_table.select_one('h1.page-header__title') else "Unknown"
    if table_data is None:
        return []

    header_rw = table_data.find('tr')
    header = [th.find('span').get_text(separator="", strip=True) if th.find('span') else th.get_text(separator="", strip=True) for th in header_rw.find_all('th')]
    if len(header) < 6:
        return None
    
    bonus_stat_type = header[5] if len(header) > 5 else "Bonus Stat"
    bonus_stat_type = re.sub(r"[^A-Za-z\s]+","", bonus_stat_type).strip()

    ascension_data = []
    current_phase = None

    for row in table_data.find_all('tr')[1:]:
        td_w_colspan = row.find('td', attrs={'colspan': True})
        if td_w_colspan:
            continue

        cells = row.find_all('td')
        if not cells:
            continue

        if cells[0].get('rowspan'):
            current_phase = cells[0].get_text(separator=" ", strip=True)
            cell_txts = [cells[0].get_text(separator=" ", strip=True)]
            cell_txts.extend(cell.get_text(separator=" ", strip=True) for cell in cells[1:])
        else:
            cell_txts = [current_phase]
            cell_txts.extend(cell.get_text(separator=" ", strip=True) for cell in cells)

        if len(cell_txts) < 6:
            continue

        ph, lvl, bs_hp, bs_atk, bs_def, bns_val = cell_txts[:6]
        ph = re.sub(r"[^\d]", "", ph)
        bns_val = bns_val.replace("\u2014", "0%")

        row_dict={
            "AscensionPhase": ph,
            "Level": lvl,
            "BaseHP": bs_hp,
            "BaseAtk": bs_atk,
            "BaseDef": bs_def,
            bonus_stat_type: bns_val
        }
        ascension_data.append(row_dict)

    return {"name": chara_name, "ascension_data": ascension_data}

def get_ascension_data():
    char_link = get_chara_link()
    ascension_data = []

    for link in char_link:
        table_data = get_table_data(link)
        if table_data:
            ascension_data.append(table_data)

    return ascension_data

if __name__ == "__main__":
    # test_link = "https://genshin-impact.fandom.com/wiki/Traveler"
    # test_table = get_table_data(test_link)
    # print(json.dumps(test_table,indent=2))

    ascensions_data = get_ascension_data()
    
    try:
        with open("ascension_data.json", 'w', encoding='utf-8') as f:
            json.dump(ascensions_data, f, indent=2, ensure_ascii=False)
        print("Done !")
    except Exception as e:
        print(e)