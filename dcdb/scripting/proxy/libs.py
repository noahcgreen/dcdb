from dcdb.event.types import *

from ..cutil import TypeBuilder

__all__ = ['abilitylib', 'attacklib', 'cardlib', 'card_typelib', 'card_type_typelib', 'characterlib', 'colorlib',
           'color_typelib', 'eventlibs', 'inputlib', 'event_typelib', 'event_type_typelib',
           'funclib', 'gamelib', 'handlelib', 'locationlib', 'location_typelib', 'pilelib', 'playerlib',
           'regionlib', 'region_typelib', 'statemachinelib', 'turnlib', 'zonelib', 'zone_typelib',

           'all_libs', 'build_all']


abilitylib = TypeBuilder('dcdb.ability')
attacklib = TypeBuilder('dcdb.attack')
cardlib = TypeBuilder('dcdb.card')
card_type_typelib = TypeBuilder('dcdb.card_type_type')
card_typelib = TypeBuilder('dcdb.card_type')
characterlib = TypeBuilder('dcdb.character')
colorlib = TypeBuilder('dcdb.color')
color_typelib = TypeBuilder('dcdb.color_type')
inputlib = TypeBuilder('dcdb.input')
event_typelib = TypeBuilder('dcdb.event_type')
event_type_typelib = TypeBuilder('dcdb.event_type_type')
funclib = TypeBuilder('dcdb.func')
gamelib = TypeBuilder('dcdb.game')
handlelib = TypeBuilder('dcdb.handle')
locationlib = TypeBuilder('dcdb.location')
location_typelib = TypeBuilder('dcdb.location_type')
pilelib = TypeBuilder('dcdb.pile')
playerlib = TypeBuilder('dcdb.player')
region_typelib = TypeBuilder('dcdb.region_type')
regionlib = TypeBuilder('dcdb.region')
statemachinelib = TypeBuilder('dcdb.statemachine')
turnlib = TypeBuilder('dcdb.turn')
zonelib = TypeBuilder('dcdb.zone')
zone_typelib = TypeBuilder('dcdb.zone_type')

# TODO: Dynamically via EventType?
eventlibs = {
    MoveEvent: TypeBuilder('dcdb.move_event'),
    RevealEvent: TypeBuilder('dcdb.reveal_event'),
    GainEvent: TypeBuilder('dcdb.gain_event'),
    BuyEvent: TypeBuilder('dcdb.buy_event'),
    DestroyEvent: TypeBuilder('dcdb.destroy_event'),
    DiscardEvent: TypeBuilder('dcdb.discard_event'),
    DiscardToDeckEvent: TypeBuilder('dcdb.discard_to_deck_event'),
    DrawEvent: TypeBuilder('dcdb.draw_event'),
    PlayEvent: TypeBuilder('dcdb.play_event'),
    AttackIndividualEvent: TypeBuilder('dcdb.attack_individual_event'),
    AttackGroupEvent: TypeBuilder('dcdb.attack_group_event'),
    AttackEvent: TypeBuilder('dcdb.attack_event'),
    PowerEvent: TypeBuilder('dcdb.power_event'),
    AbilityEvent: TypeBuilder('dcdb.ability_event'),
    TurnStartEvent: TypeBuilder('dcdb.turn_start_event'),
    TurnEndEvent: TypeBuilder('dcdb.turn_end_event'),
    GameEndEvent: TypeBuilder('dcdb.game_end_event')
}


all_libs = [
    abilitylib,
    attacklib,
    cardlib,
    card_typelib,
    card_type_typelib,
    characterlib,
    colorlib,
    color_typelib,
    event_typelib,
    event_type_typelib,
    *eventlibs.values(),
    funclib,
    gamelib,
    handlelib,
    inputlib,
    locationlib,
    location_typelib,
    pilelib,
    playerlib,
    region_typelib,
    regionlib,
    statemachinelib,
    turnlib,
    zonelib,
    zone_typelib,
]


def build_all(state):
    for lib in all_libs:
        lib.build(state)
