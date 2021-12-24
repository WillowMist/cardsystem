import random
from evennia import DefaultScript, create_script
from evennia.commands.default.muxcommand import MuxCommand
from evennia.utils.evmenu import EvMenu
from cardsystem import helper
from cardsystem.typeclasses import CardCharacter, NPC
from typeclasses.characters import Character
from evennia.utils import logger

class CombatHandler(DefaultScript):
    """
    This implements the combat handler.
    """

    def at_script_creation(self):
        """Called when script is first created"""

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
        try:
            character.cleareffects()
            if character.nattributes.get('_menutree'):
                character.ndb._menutree.close_menu()
        except:
            pass

    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this combat handler to
        all characters as well as re-assign the cmdset.
        """
        for character in self.db.characters.values():
            self._init_character(character)

    def at_stop(self):
        """Called just before the script is stopped/destroyed."""
        for character in list(self.db.characters.values()):
            # note: the list() call above disconnects list from database
            self.msg_all("Combat has ended")
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
        """Add combatant to handler"""
        dbref = character.id
        self.db.characters[dbref] = character
        self.db.action_count[dbref] = 0
        self.db.disconnected_turns[dbref] = 0
        self.db.turn_actions [dbref] = [{'card': None, 'character': character, 'target': [None]}]
        # set up back-reference
        self._init_character(character)
        if character in CardCharacter.objects.all() or character in Character.objects.all():
            EvMenu(character, 'cardsystem.combat_handler', startnode='combat_menu', cmd_on_exit=None)
        elif character in NPC.objects.all() and len(self.db.characters) > 1:
            character.combat_action()

    def remove_character(self, character):
        """Remove combatant from handler"""
        if character.id in self.db.characters:
            self._cleanup_character(character)
        if len(self.db.characters):
            # if no more characters in battle, kill this handler
            self.stop()

    def msg_all(self, message):
        """Send message to all combatants"""
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
        # Check to see if any NPCs have not acted
        for char in self.db.characters.values():
            if char in NPC.objects.all() and self.db.action_count[char.id] < 1:
                self.msg_all(f'{char.key} going.')
                char.combat_action()
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

            self.stop()
        else:
            # reset counters before next turn
            for character in self.db.characters.values():
                self.db.characters[character.id] = character
                self.db.action_count[character.id] = 0
                self.db.turn_actions[character.id] = [{'card': None, 'character': character, 'target': [None]}]
                character.countdowneffects()
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
                if character in NPC.objects.all() and len(self.db.characters) > 1:
                    self.msg_all(f'{character.key} going.')
                    character.combat_action()

    def resolve_combat(self):
        """
        Process combat results.
        """
        combat_results = ''
        effects = {}
        attacks = {}
        for key, character in self.db.characters.items():
            charname = character.key
            self.msg_all(f"{charname} - {self.db.turn_actions[key]}")
            for action in self.db.turn_actions[key]:
                if action['card']:
                    carddata = helper.get_card_data(action['card'])
                    # Calculate Damage and Block/Dodge
                    target = action['target']
                    for t in list(target):
                        if not t:
                            target.remove(t)
                    if target:
                        targets = helper.pretty_list_objects(target)
                        pool, cardindex = helper.find_card(character, action['card'], pools=['card_hand'])
                        if pool:
                            character.play(cardindex)
                            if carddata['Type'] in ['Defend', 'Buff', 'Debuff', 'Weapon', 'Armor', 'Item']:
                                if character not in effects.keys():
                                    effects[character] = []
                                combat_results += f'{charname} played {carddata["Name"]} targeting {targets}.\n'
                                if carddata['Type'] == 'Defend':
                                    stat = carddata.get('TargetStat', 'Health')
                                    usestat = carddata.get('UseStat', 'Strength')
                                    defendmult = character.get_stat(usestat)[0] / 10
                                    self.msg_all(f'Defend: {stat}, {usestat}, {defendmult}, {carddata["Defense"]}')
                                    effect = {'Defend': stat, 'Amount': int(carddata['Defense'] * defendmult), 'Element': carddata['Element']}
                                    effects[character].append(effect)
                                if carddata['Type'] in ['Buff', 'Debuff']:
                                    stat = carddata.get('TargetStat', 'Strength')
                                    usestat = carddata.get('UseStat', 'Intelligence')
                                    buffmult = character.get_stat(usestat)[0] / 10
                                    amount = int(carddata.get('Amount', 1) * buffmult)
                                    duration = carddata.get('Duration', -1)
                                    if carddata['Type'] == 'Debuff':
                                        amount = 0 - amount
                                    for tgt in target:
                                        tgt.addeffect(stat, amount, duration=duration, source=character)
                            elif carddata['Type'] in ['Attack']:
                                if character in attacks.keys():
                                    attacks[character].append(action)
                                else:
                                    attacks[character] = [action]
                else:
                    combat_results += f'{charname} played nothing.\n'
        self.msg_all(f'Before Attack: {effects}')
        for character, actionlist in attacks.items():
            for action in actionlist:
                carddata = helper.get_card_data(action['card'])
                cardname = helper.card_brief(carddata)
                for tgt in action['target']:
                    basedamage = carddata["Damage"]
                    usestat = carddata.get('UseStat', 'Strength')
                    statmult = character.get_stat(usestat)[0] / 10
                    damage = int(basedamage * statmult)
                    if carddata.get('Requires', None):
                        itemfound = False
                        for itemcard in character.db.card_played:
                            itemcarddata = helper.get_card_data(itemcard)
                            if itemcarddata['Type'] == carddata.get('Requires'):
                                itemfound = True
                                itemmult = itemcarddata.get('AttackMultiplier', 1)
                                continue
                        if itemfound:
                            damage = int(damage * itemmult)
                        else:
                            combat_results += (f'{character.key} played an unplayable card.')
                            continue
                    self.msg_all(f'Base: {basedamage}, Stat: {usestat}, Mult: {statmult}, Damage: {damage}')
                    tgteffects = effects.get(tgt, [])
                    for effect in tgteffects:
                        if 'Defend' in effect.keys() and carddata.get('TargetStat', 'Health') == effect['Defend']:
                            damage -= effect['Amount']
                    # TODO: Calculate actual damage with buffs, debuffs, etc.
                    damage -= tgt.defense
                    damage = 0-max(0, damage)
                    self.msg_all('Stuff 1')
                    tgt.modify_stat('Health', damage)
                    self.msg_all('Stuff 2')
                    combat_results += (f'{character.key} attacks {tgt.key} with {cardname} for {abs(damage)} damage.\n')
        self.db.last_round += 1
        self.db.combat_results[self.db.last_round] = combat_results

    def get_groups(self, obj):
        phandler = obj.ndb.party_handler
        group = {'Friend': [], 'Foe': []}
        for characterid in self.db.characters.keys():
            if characterid == obj.id:
                group['Friend'].append(self.db.characters[characterid])
            elif phandler and characterid in phandler.db.characters.keys():
                group['Friend'].append(self.db.characters[characterid])
            else:
                group['Foe'].append(self.db.characters[characterid])
        return group

class CmdAttack(MuxCommand):
    """
    initiates combat

    Usage:
      attack <target>

    This will initiate combat with <target>. If <target> is
    already in combat, you will join the combat.
    """
    key = "attack"
    help_category = "General"
    arg_regex = r"\s|$"

    def func(self):
        """Handle command"""
        caller = self.caller
        if not self.args:
            self.caller.msg("Usage: attack <target>")
            return
        target = caller.search(self.args)
        if not target:
            return
        if target.ndb.party_handler and player.ndb.party_handler == target.ndb.party_handler:
            self.caller.msg("You cannot attack someone in your party!")
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
            for member in chandler.db.characters.values():
                if member.ndb.party_handler:
                    party_handler = self.caller.ndb.party_handler
                    for character in party_handler.db.characters.values():
                        if character != member and character.id not in chandler.db.characters.keys():
                            chandler.add_character(character)
                            chandler.msg_all("%s joins combat!" % character)


def combat_menu(caller, raw_string, **kwargs):

    chandler = caller.ndb.combat_handler
    group = chandler.get_groups(caller)
    caller.draw(caller.db.hand_size - len(caller.db.card_hand))
    text = ""
    if 'hand' in kwargs.keys():
        text += str(helper.card_small_multiple(caller.db.card_hand, title="Your Hand"))
    elif 'details' in kwargs.keys():
        carddata = helper.get_card_data(kwargs['details'])
        text += str(helper.card_detail(carddata))
    elif 'stats' in kwargs.keys():
        combat_stats = helper.combat_stats_multiple(list(group['Friend']) + list(group['Foe']))
        text += str(combat_stats)
    else:
        if chandler.db.last_round:
            text += f'Last Round Results:\n{chandler.db.combat_results[chandler.db.last_round]}\n'
    options = []
    for card in caller.db.card_hand:
        cardname = helper.card_brief(helper.get_card_data(card))
        options.append({'desc': f'Play {cardname}', 'goto': ('checktargets', {'card': card})})
    for index in range(0, len(caller.db.card_hand)):
        carddata = helper.get_card_data(caller.db.card_hand[index])
        options.append({'key': f'x{index+1}', 'desc': f'Examine {helper.card_brief(carddata)}', 'goto': ('combat_menu', {'details': carddata['CardString']})})
    options.append({'key': 'hand', 'desc': 'View your hand', 'goto': ('combat_menu', {'hand': True})})
    options.append({'key': 'stats', 'desc': 'View combat stats', 'goto': ('combat_menu', {'stats': True})})
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
        chandler.msg_all(group)
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
