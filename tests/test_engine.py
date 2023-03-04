import pytest

import random

from dcdb.game import Game
from dcdb.input import EndTurnInput, SelectionInput
from dcdb.scripting.cutil import ScriptError


def test_random(Driver, datadir, script_dir):
    game = Game(datadir / 'Random.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    p3 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.buy('Weakness')
    driver.end_turn()
    driver.cancel()
    driver.cancel()
    driver.process(lambda option: isinstance(option, SelectionInput))
    driver.select(lambda card: card.name == 'Punch')
    driver.select(lambda card: card.name == 'Vulnerability')
    driver.select(lambda card: card.name == 'Kick')
    driver.select(lambda card: card.name == 'Weakness')
    for player in game.players:
        assert len(player.hand) == 5


@pytest.mark.skip(reason='Recursion error not fixed')
def test_long_game(Driver, datadir, script_dir):
    """
    This test is designed to catch as many random errors as possible by progressing a game randomly.
    """
    game = Game(datadir / 'BS.yml', shuffle=False, script_dir=script_dir)
    game.add_player()
    game.add_player()
    driver = Driver(game)
    driver.start()

    while not game.is_over:
        option = random.choice(game.options)
        try:
            game.process(option)
        except (ScriptError, RecursionError) as e:
            print(e)
            break


@pytest.mark.skip(reason='Recursion error not fixed')
def test_long2(Driver, datadir, script_dir):
    game = Game(datadir / 'Long.yml', shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    driver = Driver(game)
    driver.start()

    for i in range(117):
        while p1.hand:
            driver.play('Kick')
        driver.end_turn()

    # This input causes game to crash with max recursion error
    driver.play('Kick')


def test_reentrant(Driver, datadir, script_dir):
    game1 = Game(datadir / 'BS.yml', script_dir=script_dir)
    game2 = Game(datadir / 'BS.yml', script_dir=script_dir)

    g1_p1 = game1.add_player('BS.Cyborg')
    g2_p1 = game2.add_player('BS.Cyborg')

    assert g1_p1.characters[0] != g2_p1.characters[0]
