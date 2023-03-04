from dcdb.game import Game


def test_batman(Driver, datadir, script_dir):
    game = Game(datadir / 'Character.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Batman')
    driver = Driver(game)
    driver.start()
    driver.play('Utility Belt')
    assert game.power == 3
    driver.play('Utility Belt')
    assert game.power == 6


def test_superman(Driver, datadir, script_dir):
    game = Game(datadir / 'Character.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Superman')
    driver = Driver(game)
    driver.start()

    driver.play('Kick')
    assert game.power == 3
    driver.play('Kick')
    assert game.power == 5
    driver.play('Super Strength')
    assert game.power == 11


def test_wonder_woman(Driver, datadir, script_dir):
    game = Game(datadir / 'Character.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Wonder Woman')
    p2 = game.add_player('BS.Wonder Woman')
    driver = Driver(game)
    driver.start()

    driver.play('Super Strength')
    driver.buy('Harley Quinn')
    driver.buy('Harley Quinn')
    driver.end_turn()
    assert len(p1.hand) == 7

    driver.play('Super Strength')
    driver.buy('Harley Quinn')
    driver.end_turn()
    assert len(p2.hand) == 6

    driver.end_turn()
    assert len(p1.hand) == 5


def test_cyborg(Driver, datadir, script_dir):
    game = Game(datadir / 'Character.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Cyborg')
    driver = Driver(game)
    driver.start()
    driver.play('Kick')
    assert game.power == 3
    driver.play('Utility Belt')
    assert len(p1.hand) == 4


def test_green_lantern(Driver, datadir, script_dir):
    game = Game(datadir / 'Character.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Green Lantern')
    driver = Driver(game)
    driver.start()

    driver.play('Super Strength')
    driver.play('Kick')
    driver.play('Kick')
    assert game.power == 9
    driver.play('Utility Belt')
    assert game.power == 14
    driver.play('Utility Belt')
    assert game.power == 16


def test_aquaman(Driver, datadir, script_dir):
    game = Game(datadir / 'Character.yml', seed=1, shuffle=False, script_dir=script_dir)
    game.auto_resolution_order = False
    p1 = game.add_player('BS.Aquaman')
    driver = Driver(game)
    driver.start()

    driver.play('Super Strength')
    driver.play('Kick')
    driver.play('Kick')
    driver.play('Utility Belt')
    hq1 = driver.buy('Harley Quinn')
    driver.select(lambda option: option)
    assert hq1 == p1.deck[0]
    hq2 = driver.buy('Harley Quinn')
    driver.cancel()
    assert hq2 in p1.discard
    ss = driver.buy('Super Strength')
    assert ss in p1.discard


def test_martian_manhunter(Driver, datadir, script_dir):
    game = Game(datadir / 'Martian.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Martian Manhunter')
    driver = Driver(game)
    driver.start()

    driver.play('Catwoman')
    assert game.power == 2
    driver.play('Catwoman')
    assert game.power == 7
    driver.play('Catwoman')
    assert game.power == 9
    driver.play('Gorilla Grodd')
    driver.play('Gorilla Grodd')
    assert game.power == 18


def test_flash(Driver, datadir, script_dir):
    game = Game(datadir / 'Flash.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.The Flash')
    driver = Driver(game)
    driver.start()

    driver.play('The Watchtower')
    driver.play('Catwoman')
    assert len(p1.hand) == 5
    driver.play('Kid Flash')
    assert len(p1.hand) == 5
    driver.end_turn()
    assert len(p1.hand) == 5
