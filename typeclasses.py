from evennia import DefaultCharacter, DefaultObject
import random
import cardsystem
from cardsystem import helper
from evennia.prototypes import spawner
from evennia.utils import is_iter
from collections import defaultdict
from evennia.utils.utils import list_to_string


class CardUserMixin(object):
    def at_object_creation(self):
        super(CardUserMixin, self).at_object_creation()
        self.db.card_deck = []
        self.db.card_hand = []
        self.db.card_discard = []
        self.db.card_played = []
        self.db.stats = {'Strength': {'Max': 10, 'Cur': 10},
                         'Reflexes': {'Max': 10, 'Cur': 10},
                         'Health': {'Max': 10, 'Cur': 10},
                         }

    def shuffle(self, withdiscard=True):
        if withdiscard:
            self.db.card_deck.extend(self.db.card_discard)
            self.db.card_discard = []
        random.shuffle(self.db.card_deck)

    @property
    def deck(self):
        return self.db.card_deck

    @property
    def hand(self):
        return self.db.card_hand

    @property
    def played(self):
        return self.db.card_played

    @property
    def discardpile(self):
        return self.db.card_discard

    @property
    def defense(self):
        basedefense = self.db.stats['Strength']['Cur']
        defense = int(basedefense)
        for card in self.db.card_played:
            carddata = helper.get_card_data(card)
            if carddata.get("DefenseMult"):
                defense = defense * carddata['DefenseMult']
        defense = int(defense/10)
        return defense

    def fill_deck(self):
        """ Remove this """
        for i in range(20):
            rarity = random.choice(['Common', 'Common', 'Common', 'Uncommon', 'Common', 'Common', 'Common', 'Uncommon', 'Common', 'Common', 'Common', 'Rare'])
            cardtitle = random.choice(list(cardsystem.CARDS['Base'][rarity].keys()))
            card = f'Base_{rarity}_{cardtitle}'
            self.db.card_deck.append(card)

    def draw(self, cardcount):
        for i in range(0, cardcount):
            if len(self.db.card_deck) == 0:
                self.msg('Shuffling discard back into deck.')
                self.shuffle()
            self.db.card_hand.append(self.db.card_deck.pop(0))

    def discard(self, index):
        self.db.card_discard.append(self.db.card_hand.pop(index))

    def play(self, index, fromzone='card_hand'):
        from_zone = self.attributes.get(fromzone)
        carddata = helper.get_card_data(from_zone[index])
        if carddata['Type'] in ['Attack', 'Defend', 'Buff', 'Debuff']:
            # Insert card effects here
            self.db.card_discard.append(from_zone.pop(index))
        else:
            for index in range(0, len(self.db.card_played)):
                played_carddata = helper.get_card_data(self.db.card_played[index])
                if played_carddata['Type'] == carddata['Type']:
                    self.msg(f"Removing {played_carddata['Name']} from play.")
                    self.leaveplay(index)
            self.msg(f'Playing {carddata["Name"]}')
            self.db.card_played.append(from_zone.pop(index))
        if carddata.get('Create', None):
            for card in carddata['Create']:
                self.db.card_deck.append(card)
            self.shuffle(withdiscard=False)
            self.calculate_stats()

    def leaveplay(self, index):
        carddata = helper.get_card_data(self.db.card_played[index])
        if carddata.get('Create', None):
            for card in carddata['Create']:
                self.remove_card(card)
        self.db.card_discard.append(self.db.card_played.pop(index))

    def calculate_stats(self):
        for key in self.db.stats.keys():
            stat = self.db.stats[key]
            statdif = stat['Max'] - stat['Cur']
            self.db.stats[key]['Max'] = 10
            self.db.stats[key]['Cur'] = 10 - statdif
            for card in self.all_cards():
                cardinfo = helper.get_card_data(card)
                cardmod = cardinfo.get(key, 0)
                if cardmod:
                    self.db.stats[key]['Max'] += cardmod
                    self.db.stats[key]['Cur'] += cardmod

    def modify_stat(self, stat, amount, buff=False):
        if stat in self.db.stats.keys():
            mystat = self.db.stats[stat]
            mystat['Cur'] += amount
            if not buff:
                mystat['Cur'] = min(mystat['Max'], mystat['Cur'])
            self.check_stats()

    def check_stats(self):
        if self.db.stats['Health']['Cur'] <= 0:
            if chandler := self.ndb.combat_handler:
                chandler.msg_all(f'COMBAT: {self.key} is knocked out.')
                chandler.remove_character(self)
            self.die()

    def die(self):
        self.location.msg_contents(f'GAME: {self.key} dies.  If you\'re seeing this, this typeclass has not been set up properly.')

    def all_cards(self):
        allcards = list(self.db.card_deck) + list(self.db.card_hand) + list(self.db.card_discard) + list(self.db.card_played)
        return allcards

    def remove_card(self, cardstring):
        cardpool, index = helper.find_card(self, cardstring, pools=['card_deck', 'card_hand', 'card_discard', 'card_played'])
        if cardpool:
            self.attributes.get(cardpool).remove(cardstring)
            return True
        return False

    def return_appearance(self, looker, **kwargs):
        """
        This formats a description. It is the hook a 'look' command
        should call.
        Args:
            looker (Object): Object doing the looking.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).
        """
        if not looker:
            return ""
        # get and identify all objects
        visible = (con for con in self.contents if con != looker and con.access(looker, "view"))
        exits, users, things = [], [], defaultdict(list)
        for con in visible:
            key = con.get_display_name(looker)
            if con.destination:
                exits.append(key)
            elif con.has_account:
                users.append("|c%s|n" % key)
            else:
                # things can be pluralized
                things[key].append(con)
        # get description, build string
        string = ""
        # string = "|c%s|n\n" % self.get_display_name(looker)
        desc = helper.carduser_desc(self, looker)

        if desc:
            string += "%s" % desc
        if exits:
            string += "\n|wExits:|n " + list_to_string(exits)
        if users or things:
            # handle pluralization of things (never pluralize users)
            thing_strings = []
            for key, itemlist in sorted(things.items()):
                nitem = len(itemlist)
                if nitem == 1:
                    key, _ = itemlist[0].get_numbered_name(nitem, looker, key=key)
                else:
                    key = [item.get_numbered_name(nitem, looker, key=key)[1] for item in itemlist][
                        0
                    ]
                thing_strings.append(key)

            string += "\n|wYou see:|n " + list_to_string(users + thing_strings)

        return string


class CardCharacter(CardUserMixin, DefaultCharacter):
    """

    """
    def at_object_creation(self):
        super(CardCharacter, self).at_object_creation()
        self.db.hand_size = 4

    def die(self):
        self.location.msg_contents(f'{self.key} is unconscious.')
        # TODO: Add cmdset to remove basic commands like move.

class CardObject(DefaultObject):
    """

    """
    def at_object_creation(self):
        super(CardObject, self).at_object_creation()
        self.db.card_combatok = False
        self.db.card = None
        self.db.component = None


class NPC(CardUserMixin, DefaultCharacter):
    """

    """
    def at_object_creation(self):
        super(NPC, self).at_object_creation()
        self.db.card_combatok = True
        self.db.hand_size = 3
        self.db.death_message = 'died.'
        self.db.card_equipped = []

    def basetype_posthook_setup(self):
        super(NPC, self).basetype_posthook_setup()
        self.execute_cmd('say Test')
        for count in range(0, len(self.db.card_equipped)):
            self.play(0, fromzone='card_equipped')
        self.calculate_stats()
        self.shuffle()


    def consider_invite(self):
        if self.ndb.party_invite:
            invite = self.ndb.party_invite
            accept = random.choice([True, False])
            if accept:
                invite.add_character(self)
                invite.msg_all(f'PARTY: {self.key} has joined the party.')
            else:
                invite.uninvite_character(character=self)
                invite.db.party_leader.msg(f'{self.key} has declined your party invite.')


    def spawn_loot(self, cardstring):
        carddata = helper.get_card_data(cardstring)
        if loot := carddata.get("Loot"):
            loot['location'] = self
            spawner.spawn(loot)


    def die(self):
        for i in range(0, len(self.db.card_hand)):
            self.discard(0)
        for i in range(0, len(self.db.card_played)):
            self.leaveplay(0)
        self.shuffle()
        self.spawn_loot(self.db.card_deck[0])
        self.for_contents(self.drop)
        if is_iter(self.db.death_message):
            death_message = random.choice(self.db.death_message)
        else:
            death_message = self.db.death_message
        self.location.msg_contents(f'{self.key} {death_message}')
        self.delete()

    def drop(self, obj, **kwargs):
        obj.move_to(self.location, quiet=True)
        self.location.msg_contents(f'{self.key} dropped {obj.get_numbered_name(1, self)[0]}.')

    def combat_action(self):
        drawcount = self.db.hand_size - len(self.db.card_hand)
        self.draw(drawcount)
        chandler = self.ndb.combat_handler
        group = chandler.get_groups(self)
        card = self.db.card_hand[0] # Add logic here to choose card.
        card_details = helper.get_card_data(card)


        if card_details['Type'] in ['Attack', 'Debuff']:
            if len(group['Foe']) == 1:
                target = group['Foe']
                chandler.add_action(card, self, target)
            elif card_details.get('Target') == 'Group':
                target = group['Foe']
                chandlder.add_action(card, self, target)
            else:
                target = [group['Foe'][0]] # Add logic here to choose target.
                chandler.add_action(card, self, target)
        elif card_details['Type'] in ['Heal', 'Buff']:
            if len(group['Friend']) == 1:
                target = group['Friend']
                chandler.add_action(card, self, target)
            elif card_details.get('Target') == 'Group':
                target = group['Friend']
                chandler.add_action(card, self, target)
            else:
                target = [group['Friend'][0]] # Add logic here to choose target.
                chandler.msg_all(target)
                chandler.add_action(card, self, target)
                chandler.msg_all(target)

        else:
            target = [self]
            chandler.add_action(card, self, target)
        chandler.check_end_turn()