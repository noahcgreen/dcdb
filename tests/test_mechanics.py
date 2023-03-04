from dcdb.game import Game


def test_ongoings_stay_in_play(Driver, datadir, script_dir):
    game = Game(datadir / 'Ongoings.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    location = driver.play('Arkham Asylum')
    kick = driver.play('Kick')
    driver.end_turn()
    assert location in p1.in_play
    assert kick not in p1.in_play


def test_empty_deck_shuffle(Driver, datadir, script_dir):
    game = Game(datadir / 'Ongoings.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Arkham Asylum')
    driver.play('Arkham Asylum')
    driver.end_turn()
    driver.end_turn()
    assert len(p1.hand) == 5
    assert len(p1.discard) == 3
    deck = list(p1.deck)
    driver.end_turn()
    driver.end_turn()
    assert all(card in p1.hand for card in deck)
    assert len(p1.hand) == 5
    assert len(p1.deck) == 3


def test_shuffle_on_index(Driver, datadir, script_dir):
    game = Game(datadir / 'Shuffle.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.end_turn()
    driver.end_turn()
    driver.play('Poison Ivy')
    assert len(p2.deck) == 4
    assert len(p2.discard) == 2


def test_destroy(Driver, datadir, script_dir):
    game = Game(datadir / 'Destroy.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.end_turn()
    driver.end_turn()
    driver.play('King of Atlantis')
    card = driver.select(lambda card: card and card.name == 'King of Atlantis')
    assert card not in p1.discard
    assert card in game.destroyed_pile


def test_starvp(Driver, datadir, script_dir):
    game = Game(datadir / 'StarVP.yml', seed=2, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Green Arrow')
    driver.buy('Kid Flash')
    driver.end_turn()
    assert game.is_over
    assert p1.vp == 19
    assert p2.vp == 18


def test_mera_static_power(Driver, datadir, script_dir):
    game = Game(datadir / 'Power.yml', seed=2, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Mera')
    assert game.power == 4
    driver.end_turn()
    driver.end_turn()
    driver.play('Mera')
    assert game.power == 2


def test_gain_multiple(Driver, datadir, script_dir):
    game = Game(datadir / 'Gain.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Princess Diana of Themyscira')
    assert len(game.line_up) == 0
    assert len(p1.discard) == 5


def test_gain_to_hand(Driver, datadir, script_dir):
    game = Game(datadir / 'Gain.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Supergirl')
    driver.select(lambda selection: selection == 'Yes')
    assert len(p1.discard) == 0
    driver.play('Kick')
    assert game.power == 2


def test_move_to_deck(Driver, datadir, script_dir):
    game = Game(datadir / 'Move.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.end_turn()
    driver.end_turn()
    driver.play('Zatanna Zatara')
    assert len(p1.deck) == 0
    c1 = driver.select(lambda card: card and card.name == 'Zatanna Zatara')
    c2 = driver.select(lambda card: card and card.name == 'Zatanna Zatara')
    assert p1.deck[-2] == c1
    assert p1.deck[-1] == c2


def test_opponents_played_card_returns_after_turn(Driver, datadir, script_dir):
    game = Game(datadir / 'Move.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Starro')
    assert game.power == 1
    driver.end_turn()
    assert len(p2.discard) == 1


def test_replay(Driver, datadir, script_dir):
    game = Game(datadir / 'Replay.yml', seed=2, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Kick')
    driver.play('Clayface')
    assert game.power == 4
    assert len(p1.in_play) == 2


def test_attack(Driver, datadir, script_dir):
    game = Game(datadir / 'Attack.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Bane')
    punch = driver.select(lambda card: card.name == 'Punch')
    assert punch in p2.discard
    assert game.active_player == p1
    driver.play('Harley Quinn')
    assert p2.deck[0] == punch
    assert game.power == 3


def test_defense(Driver, datadir, script_dir):
    game = Game(datadir / 'Defense.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('Bane')
    driver.select(lambda option: option)
    assert len(p2.hand) == 5


def test_xray_vision_chain(Driver, datadir, script_dir):
    game = Game(datadir / 'Play.yml', seed=1, shuffle=True, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    p3 = game.add_player()
    driver = Driver(game)
    driver.start()
    driver.play('X-Ray Vision')
    c1 = driver.select(lambda card: card.owner == p2)
    c2 = driver.select(lambda card: card.owner == p3)
    c3 = driver.select(lambda card: card.owner == p2)
    c4 = driver.select(lambda card: card.owner == p3)
    c5 = driver.select(lambda card: card.owner == p2)
    c6 = driver.select(lambda card: card.owner == p3)
    assert game.power == 2
    assert p2.deck[:3] == [c1, c3, c5]
    assert p3.deck[:3] == [c2, c4, c6]


def test_faa(Driver, datadir, script_dir):
    game = Game(datadir / 'FAA.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player()
    p2 = game.add_player()
    p3 = game.add_player()
    driver = Driver(game)
    driver.start()
    monitor = game.sv_stack[1]
    for player in game.players:
        assert not monitor.is_visible_to(player)
    driver.play('Blue Beetle')
    driver.play('Blue Beetle')
    driver.play('Blue Beetle')
    driver.buy('Ra\'s al Ghul')
    driver.end_turn()
    for player in game.players:
        assert monitor.is_visible_to(player)
    assert len(p1.hand) == 5
    driver.select(lambda option: option)
    assert len(p2.hand) == 5
    driver.cancel()
    assert len(game.options) == 4
    card = driver.select(lambda card: card and card.name == 'Kick')
    assert card in game.line_up
    driver.cancel()
    assert len(game.options) == 5
    card = driver.select(lambda card: card and card.name == 'Blue Beetle')
    assert card in game.line_up

    assert game.active_player == p2


def test_flip(Driver, datadir, script_dir):
    game = Game(datadir / 'Flip.yml', seed=1, shuffle=False, script_dir=script_dir)
    p1 = game.add_player('BS.Cyborg')
    p2 = game.add_player('BS.Superman')
    driver = Driver(game)
    driver.start()

    driver.play('Super Strength')
    driver.play('Super Strength')
    driver.buy('Ra\'s al Ghul')
    driver.end_turn()

    driver.play('Super Strength')
    driver.play('Super Strength')
    assert game.power == 10
    driver.buy('Captain Cold')
    assert game.power == 1
    driver.play('Super Strength')
    assert game.power == 7
