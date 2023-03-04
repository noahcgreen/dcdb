from kivy.animation import Animation
from kivy.lang import Builder
from kivy.properties import AliasProperty, ObjectProperty, StringProperty

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.recycleview import RecycleView

from dcgui import paths
from dcgui.uix.behaviors import HoverBehavior
from dcgui.util import option_name


Builder.load_string('''
<CardInfoModal>:
    size_hint: None, None
    size: image.texture_size
    pos_hint: {'center_x': .5, 'center_y': .5}

    Image:
        id: image
        source: root.image_path
''')


class CardInfoModal(ModalView):

    card = ObjectProperty()
    image_path = StringProperty()


Builder.load_string('''
#:import image_path dcgui.paths.image_path

<CardOptionButton>:
    size_hint_y: None
    height: self.texture_size[1]

<CardListItem>:
    Image:
        source: root.image_path
        size: root.size
        pos: root.pos
    
    BoxLayout:
        id: options
        opacity: 0.7
        orientation: 'vertical'
        pos: root.pos
        padding: dp(2)
        spacing: dp(2)

<CardList>:
    viewclass: 'CardListItem'
    smooth_scroll_end: 10
    
    RecycleBoxLayout:
        default_size_hint: None, None
        default_size: (5/7) * (self.height - dp(20)), self.height - dp(20)
        size_hint_x: None
        width: self.minimum_width
        padding: dp(10)
        spacing: dp(10)
''')


class CardOptionButton(Button):
    pass


class CardListItem(ButtonBehavior, FloatLayout, HoverBehavior):

    card = ObjectProperty()
    image_path = StringProperty()
    _opacity_animation = ObjectProperty()

    def _get_options(self):
        return self.card.options if self.card else []

    options = AliasProperty(_get_options, bind=['card'])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_select_option')

    def _select_option(self, option):
        self.dispatch('on_select_option', option)

    def on_select_option(self, option):
        pass

    def on_card(self, instance, value):
        self.card.register(self)
        self.image_path = str(paths.image_path(self.card))

    def observe_options(self, card):
        self.property('options').dispatch(self)

    def on_options(self, instance, value):
        self.ids.options.clear_widgets()
        for option in self.card.options:
            name = option_name(option)
            button = CardOptionButton(
                text=name,
                on_press=lambda _: self._select_option(option)
            )
            self.ids.options.add_widget(button)

    def on_hover_start(self):
        if self._opacity_animation:
            self._opacity_animation.cancel(self.ids.options)
        self._opacity_animation = Animation(opacity=1, duration=0.2)
        self._opacity_animation.start(self.ids.options)

    def on_hover_end(self):
        if self._opacity_animation:
            self._opacity_animation.cancel(self.ids.options)
        self._opacity_animation = Animation(opacity=0.5, duration=0.2)
        self._opacity_animation.start(self.ids.options)

    def on_press(self):
        if self.last_touch.button == 'right':
            modal = CardInfoModal(card=self.card, image_path=self.image_path)
            modal.open()


class CardList(RecycleView):

    pass
