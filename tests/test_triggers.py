from dcdb.game import Game


def test_hth_look_behind(Driver, datadir, script_dir):
    game = Game(datadir / 'HTH.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Kick')
    assert game.power == 2
    driver.play('High-Tech Hero')
    assert game.power == 5


def test_hth_look_ahead(Driver, datadir, script_dir):
    game = Game(datadir / 'HTH.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('High-Tech Hero')
    assert game.power == 1
    driver.play('Kick')
    assert game.power == 5


def test_fos_look_ahead(Driver, datadir, script_dir):
    game = Game(datadir / 'FoS.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Fortress of Solitude')
    driver.play('Kick')
    assert len(p1.hand) == 4


def test_fos_second_played(Driver, datadir, script_dir):
    game = Game(datadir / 'FoS.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Kick')
    driver.play('Fortress of Solitude')
    driver.play('Kick')
    assert len(p1.hand) == 2


def test_max_uses(Driver, datadir, script_dir):
    game = Game(datadir / 'FoS.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Fortress of Solitude')
    driver.play('Kick')
    driver.play('Kick')
    assert len(p1.hand) == 3


def test_does_not_trigger_on_foes_turn(Driver, datadir, script_dir):
    game = Game(datadir / 'FoS.yml', seed=2, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Fortress of Solitude')
    driver.end_turn()
    driver.play('Kick')
    assert len(p1.hand) == 5
    assert len(p2.hand) == 4


def test_fos_reset(Driver, datadir, script_dir):
    game = Game(datadir / 'FoS.yml', seed=2, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()

    driver.play('Fortress of Solitude')
    driver.play('Kick')
    assert len(p1.hand) == 4
    driver.end_turn()
    driver.end_turn()
    driver.play('Kick')
    assert len(p1.hand) == 5


def test_dark_knight_no_catwoman(Driver, datadir, script_dir):
    game = Game(datadir / 'DK.yml', seed=2, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Dark Knight')
    assert len(p1.discard) == 3


def test_dark_knight_look_behind(Driver, datadir, script_dir):
    game = Game(datadir / 'DK.yml', seed=2, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Catwoman')
    driver.buy('Weakness')
    driver.play('Dark Knight')
    weakness = driver.select(lambda card: card and card.name == 'Weakness')
    assert weakness in p1.hand


def test_dark_knight_look_ahead(Driver, datadir, script_dir):
    game = Game(datadir / 'DK.yml', seed=2, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Dark Knight')
    driver.play('Catwoman')
    belt = driver.select(lambda card: card and card.name == 'Utility Belt')
    assert belt in p1.hand


def test_emerald_knight(Driver, datadir, script_dir):
    game = Game(datadir / 'EK.yml', seed=2, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Emerald Knight')
    kick = driver.select(lambda card: card.name == 'Kick')
    assert game.power == 2
    driver.end_turn()
    assert kick in game.line_up
    assert kick.owner is None


def test_solomon_grundy(Driver, datadir, script_dir):
    game = Game(datadir / 'SG.yml', seed=2, shuffle=True, script_dir=script_dir)
    game.auto_resolution_order = False
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Doomsday')
    driver.play('Doomsday')
    driver.play('Doomsday')
    driver.play('Doomsday')
    card = driver.buy('Solomon Grundy')
    driver.select(lambda option: option)
    assert p1.deck[0] == card
    card = driver.buy('Solomon Grundy')
    driver.cancel()
    assert card in p1.discard


def test_parallax(Driver, datadir, script_dir):
    game = Game(datadir / 'Parallax.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Superman')
    driver = Driver(game)
    driver.start()

    driver.play('High-Tech Hero')
    driver.play('Parallax')
    assert game.power == 2
    driver.play('Kick')
    assert game.power == 12
    driver.play('Clayface')
    driver.select(lambda card: card.name == 'Parallax')
    assert game.power == 24
    driver.play('High-Tech Hero')
    assert game.power == 36
