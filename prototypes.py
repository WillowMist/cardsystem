CARDOBJ = {
    'prototype_key': 'card-object',
    'prototype_desc': 'An object that may become a card.',
    'typeclass': 'cardsystem.typeclasses.CardObject',
    'card': None,
    'component': None
}

NPC = {
    'prototype_key': 'npc',
    'prototype_desc': 'A person or creature with cardsystem stats',
    'typeclass': 'cardsystem.typeclasses.NPC',
}

GOBLIN = {
    'key': "Goblin",
    'prototype_parent': "NPC",
    'card_deck': ['Base_Common_Kick', 'Base_NPC_Claw', 'Base_Common_Punch', 'Base_Common_Block', 'Base_Common_Kick', 'Base_NPC_Thick Hide'],
    'card_equipped': ['Base_Common_Rusty Knife'],
    'death_message': ['keels over.', 'bites the dust.', 'buys the farm.']
}

FARMER = {
    'key': "Farmer",
    'prototype_parent': "NPC",
    'card_deck': ['Base_Common_Punch', 'Base_Common_Punch', 'Base_Common_Punch', 'Base_Common_Kick'],
    'card_equipped': ['Base_Common_Pitchfork']
}