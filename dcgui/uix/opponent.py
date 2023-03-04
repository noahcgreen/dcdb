from kivy.lang import Builder
from kivy.properties import ListProperty, NumericProperty, ObjectProperty, StringProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader

from dcdb.types import Region


Builder.load_string('''
<OpponentField>:
    orientation: 'horizontal'
    padding: dp(10)
    spacing: dp(10)
    
    # canvas:
    #     Color:
    #         rgba: .5, .5, .5, .2
    #     Rectangle:
    #         size: self.size
    #         pos: self.pos
    #     
    #     Color:
    #         rgba: 1, 1, 1, 1
    #     Line:
    #         rectangle: self.x, self.y, self.width, self.height
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: .2
        spacing: dp(10)
        
        PlayerCharacterList:
            id: mc_list
            characters: root.player.characters
        
        Label:
            text: root.name
            font_size: min(sp(20), self.height)
            size_hint_y: .2
    
    BoxLayout:
        orientation: 'vertical'
        size_hint_x: .6
        spacing: dp(10)
        
        CardList:
            id: card_list
        
        BoxLayout:
            size_hint_y: .1
            spacing: dp(10)

            Label:
                text: 'Hand: ' + str(root.hand_count)

            Label:
                text: 'Deck: ' + str(root.deck_count)

    BoxLayout:
        orientation: 'vertical'
        size_hint_x: .2
        spacing: dp(10)

        Button:
            text: 'In Play'
            font_size: sp(10)

        Button:
            text: 'Discard'
            font_size: sp(10)
''')


class OpponentField(BoxLayout):

    player = ObjectProperty()
    name = StringProperty()
    hand_count = NumericProperty()
    deck_count = NumericProperty()

    def on_player(self, instance, value):
        self.player.hand.register(self)
        self.player.deck.register(self)

    def observe_length(self, pile):
        if pile.zone.region == Region.HAND:
            self.hand_count = len(pile)
        elif pile.zone.region == Region.DECK:
            self.deck_count = len(pile)


Builder.load_string('''
<OpponentsView>:
    id: tabbed_panel
    tab_pos: 'left_mid'
    do_default_tab: False
''')


class OpponentsView(TabbedPanel):

    players = ListProperty()
    names = ListProperty()

    def _set_children(self):
        self.clear_tabs()
        for player, name in zip(self.players, self.names):
            header = TabbedPanelHeader(text=name)
            header.content = OpponentField(player=player, name=name)
            self.add_widget(header)
        self.default_tab = self.tab_list[-1]

    def on_players(self, instance, value):
        if len(self.players) == len(self.names):
            self._set_children()

    def on_names(self, instance, value):
        if len(self.players) == len(self.names):
            self._set_children()
