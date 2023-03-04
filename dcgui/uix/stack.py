from kivy.lang import Builder
from kivy.properties import NumericProperty, ObjectProperty, StringProperty

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image

from dcgui import paths
from dcgui.uix.behaviors import CardObserverBehavior, CardOptionMenuBehavior


__all__ = ['StackView', 'OptionStackView']


Builder.load_string('''
<OptionStackView>:
    orientation: 'vertical'
    card: root.top_card
    
    OptionStackViewImage:
        source: root.image_path
        card: root.top_card
        on_select_option: root.option = self.selection
    
    Label:
        font_size: sp(20)
        text: str(root.count)
        size_hint_y: .2
''')


class StackView(CardObserverBehavior, BoxLayout):

    viewer = ObjectProperty()
    cards = ObjectProperty()
    empty_image_path = StringProperty()

    count = NumericProperty()
    image_path = StringProperty()
    top_card = ObjectProperty(allownone=True)

    def on_cards(self, instance, value):
        self.cards.register(self)
        self.observe_length(self.cards)

    def reload_image(self):
        if self.top_card:
            if self.top_card.is_visible_to(self.viewer):
                self.image_path = str(paths.image_path(self.top_card))
            else:
                self.image_path = str(paths.card_back_path())
        else:
            self.image_path = self.empty_image_path

    def on_top_card(self, instance, value):
        self.reload_image()

    def observe_length(self, cards):
        self.count = len(cards)
        self.top_card = cards[0] if cards else None

    def observe_visibility(self, card):
        self.reload_image()


class OptionStackViewImage(CardOptionMenuBehavior, Image):

    pass


class OptionStackView(StackView):

    option = ObjectProperty()
