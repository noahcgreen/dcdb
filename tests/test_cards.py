from dcdb.game import Game


def test_jonn_jonnz(Driver, datadir, script_dir):
    game = Game(datadir / 'Jonn Jonzz.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    driver = Driver(game)
    driver.start()

    ras = game.sv_stack[0]
    j = driver.play('J\'onn J\'onnz')
    assert game.power == 3
    assert ras not in p1.in_play
    assert game.sv_stack[0] == ras
    driver.end_turn()
    assert game.sv_stack[0] == ras
    for player in game.players:
        assert ras.is_visible_to(player)


def test_jonn_jonnz_sv_invisible(Driver, datadir, script_dir):
    game = Game(datadir / 'Jonn Jonzz.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    driver = Driver(game)
    driver.start()

    for _ in range(4):
        driver.play('Kick')
    driver.buy('Ra\'s al Ghul')

    driver.play('J\'onn J\'onnz')
    assert game.power == 0


def test_riddler(Driver, datadir, script_dir):
    game = Game(datadir / 'Riddler.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    driver = Driver(game)
    driver.start()

    driver.play('Kick')
    driver.play('Kick')
    driver.play('The Riddler')
    card = game.main_deck[0]
    driver.select(lambda selection: selection == 'Yes')
    assert card in p1.discard
    assert game.power == 1
