import cardsystem
from evennia.utils import evtable
import math


def carduser_desc(obj, looker=None):
    if obj.db.desc:
        desc = obj.db.desc
    else:
        desc = ""
    desctable = evtable.EvTable(table=[[desc]], border=None, header=False, width=50)
    stats = combat_stats(obj, looker)
    combined = evtable.EvTable(table=[[stats], [desctable]], border=None, header=False, valign="t")
    return combined


def pretty_list(items):
    start, last = items[:-1], items[-1]

    if start:
        return "{}, and {}".format(", ".join(start), last)
    else:
        return last

def pretty_list_objects(items):
    newlist = []
    for item in items:
        newlist.append(item.key)
    return pretty_list(newlist)

def get_card_data(cardstring):
    if not cardstring:
        return None
    cardsplit = cardstring.split('_')
    carddata = dict(cardsystem.CARDS[cardsplit[0]][cardsplit[1]][cardsplit[2]])
    if 'Inherits' in carddata.keys():
        temp_carddata = dict(get_card_data(carddata['Inherits']))
        for key in carddata.keys():
            temp_carddata[key] = carddata[key]
        carddata = temp_carddata
    carddata['Name'] = cardsplit[2]
    carddata['Rarity'] = cardsplit[1]
    carddata['Set'] = cardsplit[0]
    carddata['CardString'] = cardstring
    return carddata

def card_small(card):
    cardrarity = cardsystem.RARITIES[card['Rarity']]
    color = cardsystem.ELEMENTS[card['Element']]['Color']
    cardstats = evtable.EvTable(table=[[card['Effect']]],
                                border=None,
                                header=False,

                                )
    cardfmt = evtable.EvTable(card['Name'],
                              table=[[cardstats]],
                              width=24,
                              border='table',
                              corner_char=f'|{color}+|n',
                              border_left_char=f"|{color}{cardrarity['left_border']}|n",
                              border_right_char=f"|{color}{cardrarity['right_border']}|n",
                              border_top_char=f"|{color}{cardrarity['top_border']}|n",
                              border_bottom_char=f"|{color}{cardrarity['bottom_border']}|n",
                              align="c",
                              )
    return cardfmt

def card_detail(card):
    keys = list(card.keys())
    keys.sort()
    cardrarity = cardsystem.RARITIES[card['Rarity']]
    color = cardsystem.ELEMENTS[card['Element']]['Color']
    cardstats = [evtable.EvColumn(align='r'),evtable.EvColumn(align='l')]
    for key in keys:
        if key not in ['Effect', 'Detail', 'Name', 'Inherits', 'AI', 'CardString', 'Loot', 'Create', 'AttackMultiplier', 'DefenseMultiplier']:
            cardstats[0].add_rows(key)
            cardstats[1].add_rows(card[key])

    cardstatsdisplay = evtable.EvTable(table=cardstats, border='incols', header=False, width=23)
    effect = card.get('Detail', card.get('Effect', ''))
    cardeffect = evtable.EvTable(table=[[f"|hEffect: |n{effect}"]],
                                border=None,
                                header=False,
                                 width=24,
                                )
    cardinterior = evtable.EvTable(header=False, table=[[cardstatsdisplay],[cardeffect]], border='incols')
    cardfmt = evtable.EvTable(card['Name'],
                              table=[[cardinterior]],
                              width=55,
                              pad_width=0,
                              border='cells',
                              corner_char=f'|{color}+|n',
                              border_left_char=f"|{color}{cardrarity['left_border']}|n",
                              border_right_char=f"|{color}{cardrarity['right_border']}|n",
                              border_top_char=f"|{color}{cardrarity['top_border']}|n",
                              border_bottom_char=f"|{color}{cardrarity['bottom_border']}|n",
                              align='c'
                              )
    return cardfmt

def card_small_multiple(cardlist, width=79, title="Your Deck"):
    colcount = int(width/26)
    rows = []
    for i in range(0,colcount):
        rows.append([])
    for i in range(0, len(cardlist)):
        row = int(math.fmod(i, colcount))
        card = get_card_data(cardlist[i])
        cardformat = card_small(card)
        rows[row].append(cardformat)
    cardmultiple = evtable.EvTable("", f'{title}', "", border=None, table=rows, align="c", valign="t")
    return cardmultiple

def card_brief(card):
    color = cardsystem.ELEMENTS[card['Element']]['Color']
    cardrarity = cardsystem.RARITIES[card['Rarity']]
    return f"|{color}{cardrarity['top_border']} {card['Name']}|n"

def combat_stats(combatant, looker=None):
    if not looker:
        looker = combatant
    deck = len(combatant.deck)
    hand = len(combatant.hand)
    discard = len(combatant.discardpile)
    played = combatant.played
    statstrings = []
    for stat in sorted(list(combatant.db.stats.keys())):
        statcur, statmax = combatant.get_stat(stat)
        statpct = statcur/statmax
        color = 'c'
        if statpct < .25:
            color = 'r'
        elif statpct < .5:
            color = 'y'
        elif statpct > 1:
            color = 'G'
        statstrings.append(f'{stat}: |{color}{statcur}|n|h/{statmax}|n')
    table = statstrings + [f"Deck Size: {deck}", f"Hand Size: {hand}", f"Discard Size: {discard}"]
    for card in played:
        cardinfo = get_card_data(card)
        table.append(card_brief(cardinfo))
    display = evtable.EvTable(f"|c{combatant.get_display_name(looker)}|n", border='table', table=[table], width=25, align='c')
    return display

def combat_stats_multiple(characters, width=79, title="Combat Stats"):
    colcount = int(width/27)
    rows = []
    for i in range(0,colcount):
        rows.append([])
    for i in range(0, len(characters)):
        row = int(math.fmod(i, colcount))
        stats = combat_stats(characters[i])
        rows[row].append(stats)
    statmultiple = evtable.EvTable("", f'{title}', "", border=None, table=rows, align="c", valign="t")
    return statmultiple

def find_card(holder, cardstring, pools=[]):
    for pool in pools:
        searchpool = list(holder.attributes.get(key=pool))
        for i in range(len(searchpool)):
            if searchpool[i] == cardstring:
                return pool, i
    return None, None
