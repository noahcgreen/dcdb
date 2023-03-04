from dcdb.types import Card, Character

from .libs import abilitylib, cardlib, characterlib


@abilitylib.property('owner')
def ability_owner(state):
    ability = abilitylib.check(state, 1)
    if isinstance(ability.owner, Card):
        cardlib.create(state, ability.owner)
    elif isinstance(ability.owner, Character):
        characterlib.create(state, ability.owner)
    else:
        raise TypeError
    return 1
