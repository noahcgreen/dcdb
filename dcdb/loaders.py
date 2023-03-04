from __future__ import annotations

from pathlib import Path
import typing as t

import yaml

from dcdb.types import *

if t.TYPE_CHECKING:
    from .types import Card, Character
    from .engine import Engine, PathLike


class YMLua(t.NamedTuple):

    front_matter: t.Dict[str, t.Any]
    script: str

    @classmethod
    def parse(cls, path: PathLike) -> YMLua:
        with open(path) as f:
            docs = f.read().split('---\n')
        front_matter = docs[1]
        # Add blank lines so script errors report the correct line number
        front_matter_length = len(front_matter.split('\n')) + 1
        script = '\n' * front_matter_length + docs[2]
        front_matter = yaml.safe_load(front_matter)
        return cls(front_matter, script)


class EntityLoader:

    extension: str = '.ymlua'

    engine: Engine
    script_dir: Path

    def __init__(self, engine: Engine, script_dir: PathLike) -> None:
        self.engine = engine
        self.script_dir = Path(script_dir)

    def script_path(self, id: str) -> PathLike:
        return self.script_dir.joinpath(*id.split('.')).with_suffix(self.extension)

    def build_card(self, id: str) -> Card:
        self.engine.logger.debug('Building card %s', id)
        path = self.script_path(id)
        front_matter, script = YMLua.parse(path)
        name = front_matter['name']
        type_name = front_matter['type'].upper()
        try:
            type = CardType[type_name]
        except KeyError as e:
            raise ValueError(f'Invalid card type: {type_name}') from e
        color_name = front_matter['color'].upper()
        try:
            color = Color[color_name]
        except KeyError as e:
            raise ValueError(f'Invalid color: {color_name}') from e
        cost = int(front_matter['cost'])
        vp = int(front_matter['vp'])
        card = Card(self.engine, id, name, type, color, cost, vp)
        initialize = self.engine.interpreter.initializer(script, str(path))
        initialize(card)
        self.engine.logger.debug('Finished building card %s', id)
        return card

    def build_character(self, id: str) -> Character:
        self.engine.logger.debug('Building character %s', id)
        path = self.script_path(id)
        front_matter, script = YMLua.parse(path)
        name = front_matter['name']
        type_name = front_matter['type'].upper()
        try:
            type = CharacterType[type_name]
        except KeyError as e:
            raise ValueError(f'Invalid character type: {type_name}') from e
        character = Character(self.engine, id, name, type)
        initialize = self.engine.interpreter.initializer(script, str(path))
        initialize(character)
        self.engine.logger.debug('Finished building character %s', id)
        return character


class SetLoader:

    set: t.Mapping
    engine: Engine
    entity_loader: EntityLoader

    def __init__(self, engine: Engine, set_path: PathLike, script_dir: PathLike) -> None:
        with open(set_path) as f:
            self.set = yaml.safe_load(f)
        self.engine = engine
        self.entity_loader = EntityLoader(self.engine, script_dir)

    def build(self, key: str) -> t.List[Card]:
        cards = []
        for card_id, count in self.set[key].items():
            for _ in range(count):
                cards.append(self.entity_loader.build_card(card_id))
        return cards

    def build_starters(self) -> t.Iterable[Card]:
        return self.build('starters')

    def build_main_deck(self) -> t.Iterable[Card]:
        return self.build('main_deck')

    def build_kicks(self) -> t.Iterable[Card]:
        return self.build('kicks')

    def build_weaknesses(self) -> t.Iterable[Card]:
        return self.build('weaknesses')

    def build_sv_top(self) -> t.Iterable[Card]:
        cards = []
        try:
            for card_id, count in self.set['super_villains']['top'].items():
                for _ in range(count):
                    cards.append(self.entity_loader.build_card(card_id))
        except KeyError:
            pass
        return cards

    def build_sv_middle(self) -> t.Iterable[Card]:
        cards = []
        try:
            for card_id, count in self.set['super_villains']['middle'].items():
                for _ in range(count):
                    cards.append(self.entity_loader.build_card(card_id))
        except KeyError:
            pass
        return cards

    def build_character(self, id: str) -> Character:
        return self.entity_loader.build_character(id)
