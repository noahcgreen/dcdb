from pathlib import Path

from dcdb.types import Card


ROOT_DIR = Path(__file__).absolute().parent
RESOURCE_DIR = ROOT_DIR / 'resources'
IMAGE_DIR = RESOURCE_DIR / 'images'


def image_path(card: Card) -> Path:
    return IMAGE_DIR.joinpath(*card.id.split('.')).with_suffix('.jpeg')


def card_back_path():
    return IMAGE_DIR / 'Card Back.jpeg'
