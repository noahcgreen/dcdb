from kivy.lang.builder import Builder
from kivy.uix.screenmanager import Screen


Builder.load_string('''
<MainMenu>:

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(20)
        padding: dp(100)

        Widget:

        Button:
            text: 'New Game'
            pos_hint: {'center_x': .5}
            on_press: root.manager.current = 'New Game'

        Button:
            text: 'Active Games'
            pos_hint: {'center_x': .5}

        Button:
            text: 'Set Browser'
            pos_hint: {'center_x': .5}

        Widget:
''')


class MainMenu(Screen):
    pass
