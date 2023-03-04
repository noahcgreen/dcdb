from kivy.lang import Builder
from kivy.properties import AliasProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.modalview import ModalView
from kivy.uix.relativelayout import RelativeLayout

from dcgui import paths
from dcgui.uix.card_list import CardList

Builder.load_string('''
<PlayerDeck>:
    orientation: 'vertical'

    Image:
        source: root.image_path

    Label:    
        font_size: sp(20)
        text: str(root.count)
        size_hint_y: .2
''')


class PlayerDeck(BoxLayout):
    cards = ObjectProperty()
    count = NumericProperty()
    empty_image_path = StringProperty(str(paths.IMAGE_DIR / 'Card Back.jpeg'))
    top_image_path = StringProperty(str(paths.IMAGE_DIR / 'Card Back.jpeg'))

    def _get_image_path(self):
        return self.top_image_path if self.cards else self.empty_image_path

    image_path = AliasProperty(_get_image_path)

    def on_cards(self, instance, value):
        self.cards.register(self)

    def observe_length(self, cards):
        self.count = len(self.cards)
        self.property('image_path').dispatch(self)


Builder.load_string('''
<PlayerDiscard>:
    orientation: 'vertical'

    Image:
        source: root.image_path

    Label:    
        font_size: sp(20)
        text: str(root.count)
        size_hint_y: .2
''')


class PlayerDiscard(ButtonBehavior, BoxLayout):
    game = ObjectProperty()
    cards = ObjectProperty()
    top_card = ObjectProperty(allownone=True)
    count = NumericProperty()
    empty_image_path = StringProperty(str(paths.IMAGE_DIR / 'Card Back.jpeg'))
    modal = ObjectProperty()
    card_list = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modal = ModalView(size_hint=(.8, .2), pos_hint={'center_x': .5, 'center_y': .5})
        self.card_list = CardList()
        self.modal.add_widget(self.card_list)

    def _get_image_path(self):
        if self.top_card:
            return str(paths.image_path(self.top_card))
        else:
            return self.empty_image_path

    image_path = AliasProperty(_get_image_path, bind=['top_card'])

    def on_cards(self, instance, value):
        self.cards.register(self)

    def observe_insert(self, cards, index, card):
        self.card_list.data.insert(index, {
            'card': card,
            'on_select_option': lambda option: self.game.process(option)
        })

    def observe_delete(self, cards, index):
        del self.card_list.data[index]

    def observe_length(self, cards):
        self.top_card = cards[-1] if cards else None
        self.count = len(cards)

    def on_press(self):
        self.modal.open()


Builder.load_string('''
<PlayerHand>:
    canvas:
        Color:
            rgba: .5, .5, .5, .5
        Rectangle:
            size: self.size
            pos: 0, 0

        Color:
            rgba: 1, 1, 1, 1
        Line:
            rectangle: 0, 0, self.width, self.height

    Label:
        text: 'HAND'
        font_size: dp(60)
        color: 1, 1, 1, .4
        pos_hint: {'center_x': .5, 'center_y': .5}

    CardList:
        id: card_list
''')


class PlayerHand(RelativeLayout):

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


Builder.load_string('''
<PlayerInPlay>:
    canvas:
        Color:
            rgba: .5, .5, .5, .5
        Rectangle:
            size: self.size
            pos: 0, 0

        Color:
            rgba: 1, 1, 1, 1
        Line:
            rectangle: 0, 0, self.width, self.height

    Label:
        text: 'IN PLAY'
        font_size: dp(60)
        color: 1, 1, 1, .4
        pos_hint: {'center_x': .5, 'center_y': .5}

    CardList:
        id: card_list
''')


class PlayerInPlay(RelativeLayout):

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


Builder.load_string('''
<PlayerCharacterList>:
    Image:
        source: root.image_path
''')


class PlayerCharacterList(RelativeLayout):

    characters = ListProperty()

    def _get_image_path(self):
        if self.characters:
            return str(paths.image_path(self.characters[0]))

    image_path = AliasProperty(_get_image_path, bind=['characters'])


Builder.load_string('''
<PlayerField>:
    mc_list: mc_list
    deck: deck
    discard: discard
    in_play: in_play
    hand: hand

    orientation: 'horizontal'
    padding: dp(10)
    spacing: dp(10)

    canvas:
        Color:
            rgba: .5, .5, .5, .2
        Rectangle:
            size: self.size
            pos: self.pos

        Color:
            rgba: 1, 1, 1, 1
        Line:
            rectangle: self.x, self.y, self.width, self.height
    
    PlayerCharacterList:
        id: mc_list
        size_hint_x: .2

    BoxLayout:
        orientation: 'vertical'
        spacing: dp(10)
        size_hint_x: .6

        PlayerInPlay:
            id: in_play

        PlayerHand:
            id: hand

    BoxLayout:
        orientation: 'horizontal'
        spacing: dp(10)
        size_hint_x: .2

        PlayerDeck:
            id: deck

        PlayerDiscard:
            id: discard
''')


class PlayerField(BoxLayout):

    game = ObjectProperty()
    player = ObjectProperty()
    player_name = StringProperty()

    def on_game(self, instance, value):
        self.hand.game = self.game
        self.discard.game = self.game
        self.in_play.game = self.game

    def on_player(self, instance, value):
        self.deck.cards = self.player.deck
        self.discard.cards = self.player.discard
        self.hand.cards = self.player.hand
        self.in_play.cards = self.player.in_play
        self.mc_list.characters = self.player.characters
