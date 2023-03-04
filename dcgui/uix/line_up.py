from kivy.lang import Builder
from kivy.properties import ObjectProperty

from kivy.uix.relativelayout import RelativeLayout

from dcgui.uix.card_list import CardList


Builder.load_string('''
<LineUp>:
    canvas:
        Color:
            rgba: .5, .5, .5, .5
        Rectangle:
            size: self.size
        
        Color:
            rgba: 1, 1, 1, 1
        Line:
            rectangle: 0, 0, self.width, self.height
    
    Label:
        text: 'LINE UP'
        font_size: dp(60)
        color: 1, 1, 1, .4
        pos_hint: {'center_x': .5, 'center_y': .5}
    
    CardList:
        id: card_list
''')


class LineUp(RelativeLayout):

    game = ObjectProperty()
    cards = ObjectProperty()

    def on_cards(self, instance, value):
        self.cards.register(self)

    def observe_insert(self, cards, index, card):
        self.ids.card_list.data.insert(index, {
            'card': card,
            'on_select_option': lambda option: self.game.process(option)
        })

    def observe_delete(self, cards, index):
        del self.ids.card_list.data[index]
