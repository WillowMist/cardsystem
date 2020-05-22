import random
from evennia import DefaultScript, create_script, Command
from evennia.utils.evmenu import EvMenu
from cardsystem import helper
from cardsystem.typeclasses import CardCharacter, NPC
from typeclasses.characters import Character
import types

class CombatHandler(DefaultScript):
    """
    This implements the combat handler.
    """

    def at_script_creation(self):
        "Called when script is first created"

        self.key = "combat_handler_%i" % random.randint(1, 1000)
        self.desc = "handles combat"
        self.interval = 60
        self.start_delay = True
        self.persistent = True

        self.db.characters = {}
        self.db.turn_actions = {}
        self.db.action_count = {}
        self.db.disconnected_turns = {}
        self.db.combat_results = {0: ''}
        self.db.last_round = 0

    def _init_character(self, character):
        """
        This initializes handler back-reference
        """
        character.ndb.combat_handler = self

    def _cleanup_character(self, character):
        """
        Remove character from handler and clean it of
        the back-reference
        """
        dbref = character.id
        del self.db.characters[dbref]
        del self.db.turn_actions[dbref]
        del self.db.action_count[dbref]
        del self.db.disconnected_turns[dbref]
        del character.ndb.combat_handler

    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this combat handler to
        all characters as well as re-assign the cmdset.
        """
        for character in self.db.characters.values():
            self._init_character(character)

    def at_stop(self):
        "Called just before the script is stopped/destroyed."
        for character in list(self.db.characters.values()):
            # note: the list() call above disconnects list from database
            self._cleanup_character(character)

    def at_repeat(self):
        """
        This is called every self.interval seconds (turn timeout) or
        when force_repeat is called (because everyone has entered their
        commands). We know this by checking the existence of the
        `normal_turn_end` NAttribute, set just before calling
        force_repeat.

        """
        if self.ndb.normal_turn_end:
            # we get here because the turn ended normally
            # (force_repeat was called) - no msg output
            del self.ndb.normal_turn_end
        else:
            # turn timeout
            self.msg_all("Turn timer timed out. Continuing.")
        self.end_turn()

    def target_opponent(self, character):
        pass

    # Combat-handler methods

    def add_character(self, character):
        "Add combatant to handler"
        dbref = character.id
        self.db.characters[dbref] = character
        self.db.action_count[dbref] = 0
        self.db.disconnected_turns[dbref] = 0
        self.db.turn_actions[dbref] = [{'card': None, 'character': character, 'target': [None]}]
        # set up back-reference
        self._init_character(character)
        if character in CardCharacter.objects.all() or character in Character.objects.all():
            EvMenu(character, 'cardsystem.combat_handler', startnode='combat_menu', cmd_on_exit=None)
        elif character in NPC.objects.all():
            character.combat_action()

    def remove_character(self, character):
        "Remove combatant from handler"
        if character.id in self.db.characters:
            self._cleanup_character(character)
        if not self.db.characters:
            # if no more characters in battle, kill this handler
            self.stop()

    def msg_all(self, message):
        "Send message to all combatants"
        for character in self.db.characters.values():
            character.msg(message)

    def add_action(self, card, character, target):
        """
        Called by combat commands to register an action with the handler.

         action - string identifying the card to be played
         character - the character performing the action
         target - the target character or None, or "NPCs", or "PCs"

        actions are stored in a dictionary keyed to each character, each
        of which holds a list of max 2 actions. An action is stored as
        a tuple (character, action, target).
        """
        dbref = character.id
        count = self.db.action_count[dbref]
        if 0 <= count < 1:  # only allow 1 action
            self.db.turn_actions[dbref][count] = {'card': card, 'character': character, 'target': target}
        else:
            # report if we already used too many actions
            return False
        self.db.action_count[dbref] += 1
        return True

    def check_end_turn(self):
        """
        Called by the command to eventually trigger
        the resolution of the turn. We check if everyone
        has added all their actions; if so we call force the
        script to repeat immediately (which will call
        `self.at_repeat()` while resetting all timers).
        """
        if all(count > 0 for count in self.db.action_count.values()):
            self.ndb.normal_turn_end = True
            self.force_repeat()

    def end_turn(self):
        """
        This resolves all actions by calling the rules module.
        It then resets everything and starts the next turn. It
        is called by at_repeat().
        """
        self.resolve_combat()

        if len(self.db.characters) < 2:
            # less than 2 characters in battle, kill this handler
            self.msg_all("Combat has ended")
            self.stop()
        else:
            # reset counters before next turn
            for character in self.db.characters.values():
                self.db.characters[character.id] = character
                self.db.action_count[character.id] = 0
                self.db.turn_actions[character.id] = [{'card': None, 'character': character, 'target': [None]}]
                if character in CardCharacter.objects.all() or character in Character.objects.all():
                    try:
                        if character.nattributes.get('_menutree'):
                            character.ndb._menutree.close_menu()
                    except:
                        pass
                    self.msg_all("Next turn begins ...")
                    if character.has_account:
                        EvMenu(character, 'cardsystem.combat_handler', startnode='combat_menu', cmd_on_exit=None)
                    else:
                        self.db.disconnected_turns[character.id] += 1
                        if self.db.disconnected_turns[character.id] > 3:
                            self.remove_character(character)
            for character in self.db.characters.values():
                if character in NPC.objects.all():
                    character.combat_action()

    def resolve_combat(self):
        """
        Process combat results.
        """
        combat_results = ''
        for key, character in self.db.characters.items():
            charname = character.key
            for action in self.db.turn_actions[key]:
                if action['card']:
                    carddata = helper.get_card_data(action['card'])
                    target = action['target']
                    targets = helper.pretty_list_objects(target)
                    combat_results += f'{charname} played {carddata["Name"]} targeting {targets}.\n'
                    pool, cardindex = helper.find_card(character, action['card'], pools=['card_hand'])
                    if cardindex:
                        character.play(cardindex)
                else:
                    combat_results += f'{charname} played nothing.\n'
            self.db.last_round += 1
            self.db.combat_results[self.db.last_round] = combat_results

    def get_groups(self, obj):
        phandler = obj.ndb.party_handler
        group = {'Friend': [], 'Foe': []}
        for characterid in self.db.characters.keys():
            if characterid == obj.id:
                group['Friend'].append(self.db.characters[characterid])
            elif phandler and characterid in phandler.characters.keys():
                group['Friend'].append(self.db.characters[characterid])
            else:
                group['Foe'].append(self.db.characters[characterid])
        return group

class CmdAttack(Command):
    """
    initiates combat

    Usage:
      attack <target>

    This will initiate combat with <target>. If <target is
    already in combat, you will join the combat.
    """
    key = "attack"
    help_category = "General"

    def func(self):
        "Handle command"
        if not self.args:
            self.caller.msg("Usage: attack <target>")
            return
        target = self.caller.search(self.args)
        if not target:
            return
        # set up combat
        if target.ndb.combat_handler:
            # target is already in combat - join it
            target.ndb.combat_handler.add_character(self.caller)
            target.ndb.combat_handler.msg_all("%s joins combat!" % self.caller)
        else:
            # create a new combat handler
            chandler = create_script("cardsystem.combat_handler.CombatHandler")
            self.caller.msg("You attack %s! You are in combat." % target)
            target.msg("%s attacks you! You are in combat." % self.caller)
            chandler.add_character(self.caller)
            chandler.add_character(target)


def combat_menu(caller):
    chandler = caller.ndb.combat_handler
    caller.draw(caller.db.hand_size - len(caller.db.card_hand))
    text = ""
    if chandler.db.last_round:
        text += f'Last Round Results:\n{chandler.db.combat_results[chandler.db.last_round]}\n'
    text += str(helper.card_small_multiple(caller.db.card_hand, title="Your Hand"))
    options = []
    for card in caller.db.card_hand:
        cardname = helper.card_brief(helper.get_card_data(card))
        options.append({'desc': f'Play {cardname}', 'goto': ('checktargets', {'card': card})})
    options.append({'key': 'flee', 'desc': 'Run from combat', 'goto': 'fleecombat'})
    return text, options




def checktargets(caller, raw_string, **kwargs):
    text = ''
    options = []
    card = kwargs.get('card', None)
    chandler = caller.ndb.combat_handler
    phandler = caller.ndb.party_handler
    if card:
        card_details = helper.get_card_data(card)
        cardname = helper.card_brief(card_details)
        group = chandler.get_groups(caller)
        target = None
        if card_details['Type'] == 'Attack' or card_details['Type'] == 'Debuff':
            if len(group['Foe']) == 1:
                target = group['Foe']
                chandler.add_action(card, caller, target)
            elif card_details.get('Target') == 'Group':
                target = group['Foe']
                chandlder.add_action(card, caller, target)
            else:
                text = "Choose a target"
                options = []
                for option in group['Foe']:
                    options.append({'desc': option.key, 'goto': ('selecttarget', {'card': card, 'target': option, 'cardname': cardname})})
        elif card_details['Type'] == 'Heal' or card_details['Type'] == 'Buff':
            if len(group['Friend']) == 1:
                target = group['Friend']
                chandler.add_action(card, caller, target)
            elif card_details('Target') == 'Group':
                target = group['Friend']
                chandler.add_action(card, caller, target)
            else:
                text = "Choose a target"
                options = []
                for option in group['Friend']:
                    options.append({'desc': option.key, 'goto': ('selecttarget', {'card': card, 'target': option, 'cardname': cardname})})
        else:
            target = [caller]
            chandler.add_action(card, caller, target)
        if target:
            targetname = helper.pretty_list(target)
            if target == [caller]:
                targetname = 'yourself'
            caller.msg(f'You play {cardname} targeting {targetname}.')
            chandler.check_end_turn()
            return
        else:
            return text, options
    else:
        pass

def selecttarget(caller, raw_string, **kwargs):
    chandler = caller.ndb.combat_handler
    cardname = kwargs.get('cardname')
    card = kwargs.get('card')
    target = [kwargs.get('target')]
    targetname = target[0].key
    if target[0] == caller:
        targetname = 'yourself'
    chandler.add_action(card, caller, target)
    caller.msg(f'You play {cardname} targeting {targetname}')
    chandler.check_end_turn()

def fleecombat(caller, raw_string, **kwargs):
    chandler = caller.ndb.combat_handler
    chandler.remove_character(caller)
    caller.msg("You flee combat.")
