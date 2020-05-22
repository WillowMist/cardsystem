import cardsystem
from cardsystem import helper
from cardsystem.combat_handler import CmdAttack
from cardsystem.party_handler import CmdPartyCreate
from evennia import Command
from evennia import default_cmds, settings
from evennia.utils.evmenu import EvMenu


class ShowDeck(Command):
    key = 'showdeck'

    def func(self):
        decklist = helper.card_small_multiple(self.caller.db.card_deck, title="Your Deck", width=self.client_width())
        self.caller.msg(decklist)


class ShowHand(Command):
    key = 'showhand'
    def func(self):
        handlist = helper.card_small_multiple(self.caller.db.card_hand, title="Your Hand", width=self.client_width())
        self.caller.msg(handlist)


class ShowDiscard(Command):
    key = 'showdiscard'
    def func(self):
        discardlist = helper.card_small_multiple(self.caller.db.card_discard, title="Your Discard Pile", width=self.client_width())
        self.caller.msg(discardlist)


class ShowCard(Command):
    key = 'showcard'
    def func(self):
        args = self.args.split(' ')
        for arg in args:
            if arg and arg.isnumeric() and int(arg) > 0 and int(arg) <= len(self.caller.db.card_hand):
                card = helper.get_card_data(self.caller.db.card_hand[int(arg)-1])
                # self.caller.msg(('<h2>Card Detail</h2>',{'type': 'evcard'}), options=None)
                # self.caller.msg((helper.card_detail(card=card), {type: 'evcard'}), options=None)
                self.caller.msg(helper.card_detail(card=card))

class CombatStats(Command):
    key = 'combatstats'
    def func(self):
        self.caller.msg(helper.combat_stats(self.caller))


class CardCmdSet(default_cmds.CharacterCmdSet):
    key = "CardCharacter"
    def at_cmdset_creation(self):
        self.add(ShowDeck)
        self.add(ShowHand)
        self.add(ShowDiscard)
        self.add(ShowCard)
        self.add(CombatStats)
        self.add(CmdAttack)
        self.add(CmdPartyCreate)


