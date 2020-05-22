import random
from evennia import DefaultScript, CmdSet, create_script, Command
from cardsystem.typeclasses import CardObject, CardCharacter
from typeclasses.characters import Character

class PartyHandler(DefaultScript):
    """
    This implements the party handler.
    """

    def at_script_creation(self):
        """Called when script is first created"""
        party_number = random.randint(1, 10000)
        self.key = "party_handler_%i" % party_number
        self.desc = "maintains party"
        self.persistent = True
        self.db.party_leader = None
        self.db.characters = {}
        self.db.invites = {}
        self.db.party_name = "Party %i" % party_number

    def _init_character(self, character):
        """
        This initializes handler back-reference
        """
        dbref = character.id
        if self.db.invites.get(dbref):
            del character.ndb.party_invite
            del self.db.invites[dbref]
        character.ndb.party_handler = self
        if character in Character.objects.all() or character in CardCharacter.objects.all():
            character.cmdset.add("cardsystem.party_handler.PartyCmdSet")

    def _init_invite(self, character):
        """
        This handles the adding of party invites
        """
        character.ndb.party_invite = self
        if character in CardObject.objects.all():
            character.consider_invite()
        elif character in Character.objects.all() or character in CardCharacter.objects.all():
            character.cmdset.add("cardsystem.party_handler.PartyInviteeCmdSet")

    def _uninvite_character(self, character):
        dbref = character.id
        del self.db.invites[dbref]
        if character in Character.objects.all() or character in CardCharacter.objects.all():
            character.cmdset.remove("cardsystem.party_handler.PartyInviteeCmdSet")
        del character.ndb.party_invite

    def _cleanup_character(self, character):
        """
        Remove character from handler and clean it of the
        back-reference
        """
        dbref = character.id
        if self.db.characters.get(dbref):
            del self.db.characters[dbref]
        if self.db.invites.get(dbref):
            self._uninvite_character(character)
        del character.ndb.party_handler
        if character in Character.objects.all() or character in CardCharacter.objects.all():
            character.cmdset.remove("cardsystem.party_handler.PartyCmdSet")

    def _make_leader(self, character):
        """
        Set character as party leader, removing previous party leader
        and commands from previous leader
        """
        success = False
        if character and (character in Character.objects.all() or character in CardCharacter.objects.all()):
            if self.db.party_leader:
                self.db.party_leader.cmdset.delete("cardsystem.party_handler.LeaderCmdSet")
            self.db.party_leader = character
            character.cmdset.add("cardsystem.party_handler.LeaderCmdSet")
            success = True
        return success

    def at_start(self):
        """
        This is called on first start but also when the script is restarted
        after a server reboot. We need to re-assign this party handler to
        all characters as well as re-assign the cmdset.
        """
        for character in self.db.characters.values():
            self._init_character(character)
        for character in self.db.invites.values():
            self._init_invite(character)
        if self.db.party_leader:
            self._make_leader(self.db.party_leader)

    def at_stop(self):
        """Called just before the script is stopped/destroyed."""
        for character in list(self.db.characters.values()):
            # note: the list() call above disconnects list from database
            self._cleanup_character(character)
        for character in list(self.db.invites.values()):
            self._cleanup_character(character)

    def add_character(self, character):
        """Add character to handler"""
        dbref = character.id
        self.db.characters[dbref] = character
        # set up back-reference
        self._init_character(character)

    def invite_character(self, character):
        """Invite character to party handler"""
        dbref = character.id
        self.db.invites[dbref] = character
        self._init_invite(character)

    def uninvite_character(self, character):
        """Removes invite from character"""
        dbref = character.id
        if character.id in self.db.invites:
            self._cleanup_character(character)

    def remove_character(self, character):
        """Remove character from handler"""
        if character.id in self.db.characters:
            self._cleanup_character(character)
        if not self.db.characters:
            # if no more characters in battle, kill this handler
            self.stop()
        else:
            self.msg_all(f'{character.key} has left the party.')

    def make_leader(self, character):
        """Change the party leader."""
        if self.db.party_leader != character:
            success = self._make_leader(character)
            if success:
                self.msg_all(f'PARTY: {character.key} is the new party leader.')
        else:
            success = True
        return success


    def msg_all(self, message):
        """Send message to all combatants"""
        if self.db.characters:
            for character in self.db.characters.values():
                character.msg(message)


class CmdPartyCreate(Command):
    """
    Create a party

    Usage:
        partycreate [<target>]

    This will start a party.  If you specify a <target>,
    they will be invited to the party.  Once created you
    can partyinvite <target> to add others to your party.
    """
    key = 'partycreate'
    help_category = 'party'

    def func(self):
        if self.caller.ndb.party_handler:
            self.caller.msg('You are already in a party.')
            return
        else:
            phandler = create_script("cardsystem.party_handler.PartyHandler")
            phandler.add_character(self.caller)
            self.caller.msg(f'PARTY: You created party: {phandler.db.party_name}')
            phandler.make_leader(self.caller)
        if self.args:
            target = self.caller.search(self.args)
            if not target:
                self.caller.msg('Target not found.')
                return
            if target.ndb.party_handler:
                self.caller.msg(f'{target.key} is already in a party.')
                return
            elif target.ndb.party_invite:
                self.caller.msg(f'{target.key} already has an active party invite.')
                return
            else:
                phandler.invite_character(target)
                target.msg(f'{self.caller.key} has invited you to a party.\nUse "partyaccept" or "partydecline".')


class CmdPartyInvite(Command):
    """
    Invite target to your party

    Usage:
        partyinvite <target>
    """
    key = 'partyinvite'
    help_category = 'party'

    def func(self):
        phandler = self.caller.ndb.party_handler
        if not self.args:
            self.caller.msg('Specify a target to invite.  Usage:  partyinvite <target>')
            return
        target = self.caller.search(self.args)
        if not target:
            self.caller.msg('Target not found.')
            return
        if target.ndb.party_handler:
            self.caller.msg(f'{target.key} is already in a party.')
            return
        elif target.ndb.party_invite:
            self.caller.msg(f'{target.key} already has an active party invite.')
            return
        else:
            phandler.invite_character(target)
            self.caller.msg(f'PARTY: You invited {target.key} to your party.')
            target.msg(f'{self.caller.key} has invited you to a party.\nUse "partyaccept" or "partydecline".')


class CmdPartyUninvite(Command):
    """
    Uninvite target from your party

    Usage:
        partyuninvite <target>
    """
    key = 'partyuninvite'
    help_category = 'party'

    def func(self):
        phandler = self.caller.ndb.party_handler

        if not self.args:
            self.caller.msg('Specify a target to uninvite.  Usage:  partyuninvite <target>')
            return
        target = self.caller.search(self.args)
        if not target:
            self.caller.msg('Target not found.')
            return
        if target.ndb.party_handler and target.ndb.party_handler == phandler:
            self.caller.msg(f'{target.key} is already in your party.')
            return
        elif target.ndb.party_invite and target.ndb.party_invite == phandler:
            phandler.uninvite_character(target)
            target.msg(f'{self.caller.key} has rescinded your party invitation.')
        else:
            self.caller.msg(f'{target.key} has not been invited to your party.')
            return


class CmdPartyRemove(Command):
    """
    Remove target from your party

    Usage:
        partyremove <target>
    """
    key = 'partyremove'
    help_category = 'party'

    def func(self):
        phandler = self.caller.ndb.party_handler
        if not self.args:
            self.caller.msg('Specify a target to remove.  Usage:  partyremove <target>')
            return
        target = self.caller.search(self.args)
        if not target:
            self.caller.msg('Target not found.')
            return
        if (target.ndb.party_handler and target.ndb.party_handler != phandler) or not target.ndb.party_handler:
            self.caller.msg(f'{target.key} is not in your party.')
            return
        elif target.ndb.party_handler and target.ndb.party_handler == phandler:
            phandler.remove_character(target)
            target.msg(f'PARTY: {self.caller.key} has removed you from the party.')
            phandler.msg_all(f'PARTY: {target.key} has been removed from the party.')


class CmdPartyAccept(Command):
    """
    Accept party invite

    Usage:
        partyaccept
    """
    key = 'partyaccept'
    help_category = 'party'

    def func(self):
        if self.caller.ndb.party_handler:
            self.caller.msg('You are already in a party.')
            return
        if self.caller.ndb.party_invite:
            phandler = self.caller.ndb.party_invite
            phandler.add_character(character=self.caller)
            phandler.msg_all(f'{self.caller.key} has joined the party.')


class CmdPartyDecline(Command):
    """
    Decline party invite

    Usage:
        partydecline
    """
    key = 'partydecline'
    help_category = 'party'

    def func(self):
        if self.caller.ndb.party_invite:
            phandler = self.caller.ndb.party_invite
            phandler.uninvite_character(character=self.caller)
            phandler.db.party_leader.msg(f'{self.caller.key} has declined your party invite.')


class CmdPartyLeave(Command):
    """
    Leave Party
    """
    key = "partyleave"
    help_category = "party"

    def func(self):
        phandler = self.caller.ndb.party_handler
        if self.caller == phandler.db.party_leader:
            party = dict(phandler.db.characters)
            del party[self.caller.id]
            pcs = {}
            for member in party.keys():
                if party[member] in Character.objects.all() or party[member] in CardCharacter.objects.all():
                    pcs[member] = party[member]
            if len(pcs) > 1:
                self.caller.msg("Please assign a new leader first.  Usage: partyleader <member>")
                return
            elif len(pcs) == 1:
                newleader = pcs[list(pcs.keys())[0]]
                success = phandler.make_leader(newleader)
                phandler.remove_character(self.caller)
                self.caller.msg('PARTY: You leave the party.')
            else:
                self.caller.msg('PARTY: You dissolve the party.')
                success = self.caller.ndb.party_handler._make_leader(None)
                self.caller.ndb.party_handler.remove_character(self.caller)
            if not success:
                phandler.msg_all('PARTY: No leader.  Party dissolving.')
                phandler.stop()

        else:
            if self.caller.ndb.party_handler:
                self.caller.ndb.party_handler.msg_all(f'PARTY: {self.caller.key} leaves the party.')
                self.caller.ndb.party_handler.remove_character(self.caller)


class CmdPartyLeader(Command):
    """
    Changes the party leader.

    Usage:
        partyleader <target>

    NOTE: NPCs can not be made party leader.
    """
    key = 'partyleader'
    help_category = 'party'

    def func(self):
        phandler = self.caller.ndb.party_handler
        if not self.args:
            self.caller.msg('No target specified.  Usage: partyleader <target>')
            return
        target = self.caller.search(self.args)
        if target:
            if target.ndb.party_handler == phandler:
                success = phandler.make_leader(target)
                if not success:
                    self.caller.msg('NPCs cannot be made party leader')
                    return



class CmdParty(Command):
    """
    Show Party Members and Invites

    Usage:
        party
    """
    key = "party"
    help_category = "party"

    def func(self):
        phandler = self.caller.ndb.party_handler
        text = '|hMembers:|n\n'
        for character in phandler.db.characters.values():
            text += f'\t{character.key}'
            if character == phandler.db.party_leader:
                text += ' (Leader)'
            text += '\n'
        if phandler.db.invites:
            text += '\n|hInvitees:|n\n'
            for character in phandler.db.invites.values():
                text += f'\t{character.key}\n'
        self.caller.msg(text)



class CmdPartySay(Command):
    """
    Speak in the party
    """

    key = "partysay "
    aliases = ["p ", "psay ", "'"]
    help_category = "party"

    def func(self):
        if not self.args:
            self.caller.msg("Nothing to say.")
            return
        self.caller.ndb.party_handler.msg_all(f'PARTY: {self.caller.key} says: {self.args}')


class PartyCmdSet(CmdSet):
    key = 'party_cmdset'
    mergetype = "Union"
    priority = 10

    def at_cmdset_creation(self):
        self.add(CmdPartyLeave())
        self.add(CmdPartySay())
        self.add(CmdParty())


class LeaderCmdSet(CmdSet):
    key = 'party_leader_cmdset'
    mergetype = "Union"
    priority = 11

    def at_cmdset_creation(self):
        self.add(CmdPartyInvite())
        self.add(CmdPartyUninvite())
        self.add(CmdPartyRemove())
        self.add(CmdPartyLeader())


class PartyInviteeCmdSet(CmdSet):
    key = 'party_invitee_cmdset'
    mergetype = "Union"
    priority = 10

    def at_cmdset_creation(self):
        self.add(CmdPartyAccept())
        self.add(CmdPartyDecline())
