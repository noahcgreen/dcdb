from dcdb.game import Game


def test_ga_bow(Driver, datadir, script_dir):
    game = Game(datadir / 'Bow.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()

    driver.play('Super Strength')
    driver.play('Green Arrow\'s Bow')
    driver.buy('Ra\'s al Ghul')
    assert game.power == 1
    driver.end_turn()

    driver.play('Green Arrow\'s Bow')
    driver.play('Green Arrow\'s Bow')
    driver.buy('Ra\'s al Ghul')
    assert game.power == 0
