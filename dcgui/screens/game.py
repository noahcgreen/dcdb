from __future__ import annotations
import typing as t

from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen

from dcdb.game import Game
from dcdb.input import EndTurnInput, SelectionInput

import dcgui.uix.opponent
from dcgui.uix.option_menu import OptionMenu


Builder.load_string('''
<GameScreen>:
    opponent_layout: opponent_layout

    BoxLayout:
        orientation: 'horizontal'
        size_hint: .9, .3
        pos_hint: {'center_x': .5, 'top': .95}
        
        OpponentsView:
            id: opponent_layout
            size_hint_x: .5
        
    BoxLayout:
        orientation: 'horizontal'
        size_hint: .9, .3
        pos_hint: {'center_x': .5, 'center_y': .5}
        padding: dp(10)
        spacing: dp(10)
        
        BoxLayout:
            spacing: dp(10)
            size_hint_x: .2
            
            OptionStackView:
                viewer: root.game.players[0]
                cards: root.game.main_deck
            
            OptionStackView:
                viewer: root.game.players[0]
                cards: root.game.weakness_stack
        
        BoxLayout:
            orientation: 'vertical'
            size_hint_x: .6
            
            BoxLayout:
                id: option_layout
                size_hint_y: .25
                
                Label:
                    id: hint_label
                    font_size: sp(20)
            
            LineUp:
                game: root.game
                cards: root.game.line_up
                size_hint_y: .5
            
            Label:
                text: 'Power: ' + str(root.power)
                font_size: sp(20)
                size_hint_y: .25
        
        BoxLayout:
            spacing: dp(10)
            size_hint_x: .2
            
            OptionStackView:
                viewer: root.game.players[0]
                cards: root.game.sv_stack
                on_option: root.process(self.option)
            
            OptionStackView:
                viewer: root.game.players[0]
                cards: root.game.kick_stack
                on_option: root.process(self.option)
        
    PlayerField:
        game: root.game
        player: root.game.players[0]
        player_name: root.player_names[0]
        size_hint: .9, .3
        pos_hint: {'center_x': .5, 'y': .05}
        player_name: 'Player 1'
''')


class GameScreen(Screen):

    game: Game = ObjectProperty()
    player_names: t.List[str] = ListProperty()
    turn_player_name: t.Optional[str] = StringProperty(allownone=True)
    power: int = NumericProperty()
    end_turn_button = ObjectProperty()
    option_menu = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.end_turn_button = Button(text='End Turn', on_press=lambda btn: self.process(0))
        self.option_menu = OptionMenu()
        self.option_menu.bind(on_select=self._on_menu_option)

        self.game.register(self)

        self.opponent_layout.players = self.game.players[1:]
        self.opponent_layout.names = self.player_names[1:]

        self.game.start()

    def _on_menu_option(self, menu, option):
        menu.dismiss()
        self.game.process(option)

    def process(self, option):
        self.game.process(option)

    def observe_options(self, game):
        try:
            end_turn = next(option for option in game.options if isinstance(option, EndTurnInput))
        except StopIteration:
            end_turn = None

        if end_turn and not self.end_turn_button.parent:
            self.ids.option_layout.add_widget(self.end_turn_button)
        elif not end_turn and self.end_turn_button.parent:
            self.ids.option_layout.remove_widget(self.end_turn_button)

        menu_options = [
            option for option in game.options
            if isinstance(option, SelectionInput) and isinstance(option.selection, str)
        ]
        if menu_options:
            self.option_menu.hint = self.game.hint
            self.option_menu.options = menu_options
            self.option_menu.open()

    def observe_power(self, game):
        self.power = game.power

    def observe_turn_player(self, game):
        if self.game.turn_player:
            self.turn_player_name = self.player_names[self.game.turn_player.index]
        else:
            self.turn_player_name = None

    def observe_hint(self, game):
        if self.game.hint:
            self.ids.hint_label.text = self.game.hint
        elif self.turn_player_name:
            self.ids.hint_label.text = self.turn_player_name
        else:
            self.ids.hint_label.text = ''
