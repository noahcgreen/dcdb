# DCDB
## Simulation Engine for the DC Deck-Building Game

This project contains a Python simulator and desktop GUI application for the DC Deck-Building Game by Cryptozoic Inc.

### Project Structure

There are two distinct projects in this repository.

**dcdb** is the core simulation library which handles game logic including game flow, card abilities, core types, the event stack, etc.

**dcdbgui** is a Kivy-based GUI application built on top of the core
simulation library. As of now, it supports two-player games on a
single console.

### Installation

**Note: some additional installation may be required for third-party
libraries such as Kivy. Please refer to those libraries' documentation.**

1. Install [Lua 5.3](https://www.lua.org/versions.html).
2. Install Cython and [Lupa](https://github.com/scoder/lupa) (note the install options):
    ```bash
    pip install cython
    pip install lupa --install-option="--with-cython" --install-option="--no-luajit"
    ```
3. Install DCDB and its remaining dependencies:
    ```bash
   pip install -e . 
   ```


### Usage

Before importing the `dcdb` library, there are two directories which
should be noted: `scripts` and `sets`. Paths to these must be handed
to the game instance as in the example below.

* `scripts` contains the Lua scripts used to define card abilities. Each card
is given an identifier based on its pathname; for example, `scripts/Common/Punch.lua` is identified in the game as `Common.Punch`. Each
card script contains a YAML front matter section followed by a Lua script. The Lua objects available in the script are described in `dcdb/scripting/proxy/`.
* `sets` contains files organizing the cards described in `scripts`
into playable sets. See `sets/BS.yml` for an example.

The primary interface of the core simulation library is the `dcdb.game.Game`
class. Through this class, you can configure and create a game instance,
execute actions, and query the game.

At any time, the available options are exposed as `game.options`. To
execute an option, pass it to `game.process`. This forwards the game state until another action is required, at which point `game.options` will be updated to reflect the new game state.

```python
from dcdb.game import Game

game = Game('./sets/BS.yml', script_dir='./scripts')
p1 = game.add_player('BS.Cyborg')
game.start()
print(game.options[1])
# PlayInput(card=<Card: Punch>)
game.process(game.options[1])
```

For a better look at the various options available, look through the
tests. The GUI application describes how to subscribe to game events
as they occur.

The GUI application can be run with
```bash
python -m dcgui
```

### Testing

Testing is handled by `pytest`. The test suite is fairly comprehensive
and is intended to verify that card abilities behave as expected
according to the official game rules, even in unusual scenarios.
