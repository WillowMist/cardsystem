RARITIES = {
    'Common': {
        'left_border': '||',
        'right_border': '||',
        'top_border': '-',
        'bottom_border': '-',
    },
    'Uncommon': {
        'left_border': '[',
        'right_border': ']',
        'top_border': '=',
        'bottom_border': '=',
    },
    'Rare': {
        'left_border': '*',
        'right_border': '*',
        'top_border': '*',
        'bottom_border': '*',
    },
    'NPC': {
        'left_border': '||',
        'right_border': '||',
        'top_border': '-',
        'bottom_border': '-',
    },
}

ELEMENTS = {
    'Light': {
        'Color': '550',
    },
    'Dark': {
        'Color': '202',
    },
    'Fire': {
        'Color': '500',
    },
    'Earth': {
        'Color': '220',
    },
    'Water': {
        'Color': '005'
    },
    'Neutral': {
        'Color': '333'
    }
}

CARDS = {
    'Temp':
        {
            'Common': {
                'Slash': {
                    'Element': 'Neutral',
                    'Type': 'Attack',
                    'Damage': 5,
                    'Effect': 'Edged Weapon Attack',
                    'Requires': 'Weapon',
                },
                'Jab': {
                    'Element': 'Neutral',
                    'Type': 'Attack',
                    'Damage': 4,
                    'Piercing': True,
                    'Effect': 'Edged Weapon Attack',
                    'Requires': 'Weapon',
                },
                'Crush': {
                    'Element': 'Neutral',
                    'Type': 'Attack',
                    'Damage': 5,
                    'Effect': 'Bashing Weapon Attack',
                    'Requires': 'Weapon',
                },
            }
        },
    'Base':
        {
            'Shared': {
                'Basic Attack': {
                    'Element': 'Neutral',
                    'Type': 'Attack',
                    'Damage': 2,
                    'Effect': 'Basic Attack',
                    'Health': 1
                },
                'Basic Block': {
                    'Element': 'Neutral',
                    'Type': 'Defend',
                    'Defense': 2,
                    'UseStat': 'Reflexes',
                    'Health': 1,
                    'Effect': 'Basic Block',
                },
                'Simple Weapon': {
                    'Element': 'Neutral',
                    'Type': 'Weapon',
                    'AttackMultiplier': 1,
                },

            },
            'Common': {
                'Punch': {
                    'Inherits': 'Base_Shared_Basic Attack',
                    'Damage': 3,
                    'Strength': 1,
                    'Detail': 'Attack one opponent with a simple punch, dealing DAMAGE damage.'
                },
                'Kick': {
                    'Inherits': 'Base_Shared_Basic Attack',
                    'Damage': 4,
                    'Reflexes': 1,
                    'Detail': 'Attack your opponent with a kick, dealing DAMAGE damage.'
                },
                'Chop': {
                  'Inherits': 'Base_Shared_Basic Attack',
                  'Damage': 3,
                  'Detail': 'A simple martial arts chop.',
                  'Reflexes': 1,
                },
                'Block': {
                    'Inherits': 'Base_Shared_Basic Block',
                    'Defense': 3,
                    'Effect': 'Basic Block',
                    'Health': 1,
                },
                'Rusty Knife': {
                    'Inherits': 'Base_Shared_Simple Weapon',
                    'Strength': 1,
                    'AttackMultiplier': 1.2,
                    'Effect': 'Simple Edged Weapon',
                    'Detail': 'A small, rusty knife.',
                    'Create': ['Temp_Common_Slash', 'Temp_Common_Jab', 'Temp_Common_Jab'],
                    'Loot': {
                        'prototype_parent': 'card-object',
                        'key': 'rusty knife',
                        'card': 'Base_Common_Rusty Knife',
                        'desc': 'A small, rusty knife.'
                    },
                },
                'Rusty Short Sword': {
                    'Inherits': 'Base_Shared_Simple Weapon',
                    'Strength': 1,
                    'AttackMultiplier': 1.3,
                    'Effect': 'Simple Sword',
                    'Detail': 'A rusty short sword.',
                    'Create': ['Temp_Common_Slash', 'Temp_Common_Slash', 'Temp_Common_Slash'],
                    'Loot': {
                        'prototype_parent': 'card-object',
                        'key': 'short sword',
                        'card': 'Base_Common_Short Sword',
                        'desc': 'A rusty short sword'
                    },
                },
                'Simple Club': {
                    'Inherits': 'Base_Shared_Simple Weapon',
                    'Strength': 2,
                    'AttackMultiplier': 1.25,
                    'Effect': 'Simple Bashing Weapon',
                    'Detail': 'A basic club, fashioned from a log.',
                    'Create': ['Temp_Common_Crush', 'Temp_Common_Crush', 'Temp_Common_Crush'],
                    'Loot': {
                        'prototype_parent': 'card-object',
                        'key': 'simple club',
                        'card': 'Base_Common_Simple Club',
                        'desc': 'A basic club, fashioned from a log.'
                    }
                },
                'Pitchfork': {
                    'Inherits': 'Base_Shared_Simple Weapon',
                    'Reflexes': 1,
                    'AttackMultiplier': 1.2,
                    'Effect': 'Simple Piercing Weapon',
                    'Detail': 'A farmer\'s pitchfork',
                    'Create': ['Temp_Common_Jab', 'Temp_Common_Jab', 'Temp_Common_Jab'],
                    'Loot': {
                        'prototype_parent': 'card-object',
                        'key': 'pitchfork',
                        'card': 'Base_Common_Pitchfork',
                        'desc': 'A farmer\'s pitchfork',
                    }
                }
            },
            'Uncommon': {
                'Ray of Light': {
                    'Element': 'Light',
                    'Type': 'Attack',
                    'Damage': 4,
                    'Health': 2,
                    'Effect': 'Damages opponent with light',
                },
                'Dark Fate': {
                    'Element': 'Dark',
                    'Type': 'Attack',
                    'Damage': 6,
                    'Health': -1,
                    'Effect': 'Corrupt opponent with dark magic',
                },
                'Fire Needle': {
                    'Element': 'Fire',
                    'Type': 'Attack',
                    'Damage': 5,
                    'Reflexes': -1,
                    'Effect': 'Sear opponent with fire',
                },
                'Surge of Earth': {
                    'Element': 'Earth',
                    'Type': 'Attack',
                    'Damage': 4,
                    'Strength': 1,
                    'Effect': 'Damages opponent with the ground',
                },
                'Water Splash': {
                    'Element': 'Water',
                    'Type': 'Attack',
                    'Damage': 4,
                    'Reflexes': 1,
                    'Effect': 'Blasts opponent with water',
                },
            },
            'Rare': {
                'Searing Light': {
                    'Type': 'Attack',
                    'Element': 'Light',
                    'Damage': 6,
                    'Health': 2,
                    'Effect': 'Damages opponent with light',
                },
                'Dark Urges': {
                    'Type': 'Attack',
                    'Element': 'Dark',
                    'Damage': 7,
                    'Health': -2,
                    'Effect': 'Corrupt opponent with dark magic',
                },
                'Fire Bolt': {
                    'Element': 'Fire',
                    'Type': 'Attack',
                    'Damage': 7,
                    'Strength': 2,
                    'Effect': 'Sear opponent with fire',
                },
                'Engulfing Stones': {
                    'Element': 'Earth',
                    'Type': 'Attack',
                    'Damage': 7,
                    'Strength': 2,
                    'Effect': 'Damages opponent with the ground',
                },
                'Water Blast': {
                    'Element': 'Water',
                    'Type': 'Attack',
                    'Damage': 6,
                    'Reflexes': 2,
                    'Effect': 'Blasts opponent with water',
                    'Detail': 'Summon a blast of water to pelt your opponent, doing DAMAGE damage.'
                },
            },
            'NPC': {
                'Claw': {
                    'Inherits': 'Base_Shared_Basic Attack',
                    'Damage': 3,
                    'Strength': 1,
                },
                'Bite': {
                    'Inherits': 'Base_Shared_Basic Attack',
                    'Damage': 3,
                    'Strength': 1,
                    'Reflexes': 1,
                },
                'Sting': {
                    'Inherits': 'Base_Shared_Basic Attack',
                    'Damage': 3,
                    'Reflexes': 2,
                },
                'Thick Hide': {
                    'Inherits': 'Base_Shared_Basic Block',
                    'Defense': 3,
                    'Health': 1,
                    'Loot': {
                        'prototype_parent': 'card-object',
                        'key': 'leather scrap',
                        'component': 'leather scrap_1',
                        'desc': 'A scrap of leathery hide.'
                    }
                }
            }
        }
}