from kivy.lang.builder import Builder
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.screenmanager import Screen

from dcdb.game import Game

from dcgui.screens.game import GameScreen


Builder.load_string('''
<NewGameScreen>:

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        padding: dp(100)

        TextInput:
            size_hint_y: None
            height: dp(25)
            multiline: False
            text: 'Name'
        
        Button:
            text: 'Base Set'
            on_release: root.set_menu.open(self)
        
        BoxLayout:
            orientation: 'vertical'
            
            BoxLayout:
                Label:
                    text: 'Player 1'
                Button:
                    text: 'Character'
            
            BoxLayout:
                Label:
                    text: 'Player 2'
                Button:
                    text: 'Character'
            
            Button:
                text: 'Add player'

        Button:
            text: 'Start'
            pos_hint: {'center_x': .5}
            on_release: root.start_game()

        Widget:
''')


class NewGameScreen(Screen):

    set_names = ListProperty(['Base Set', 'Forever Evil'])
    set_menu = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_menu = DropDown()

    def on_set_menu(self, instance, value):
        value.bind(on_select=lambda menu, set_name: print(set_name))

        for set_name in self.set_names:
            button = Button(text=set_name, size_hint_y=None)
            button.bind(line_height=button.setter('height'))
            button.bind(on_release=lambda btn: value.select(btn.text))
            value.add_widget(button)

    def start_game(self):
        game = Game('sets/BS.yml', script_dir='scripts')
        game.add_player('BS.Cyborg')
        # game.add_player('BS.Batman')
        # game.add_player('BS.Aquaman')
        player_names = ['Player 1']#, 'Player 2', 'Player 3']
        game_screen = GameScreen(game=game, player_names=player_names, name='My Game')
        self.manager.switch_to(game_screen, direction='left')
