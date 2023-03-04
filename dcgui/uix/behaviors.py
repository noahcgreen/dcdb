from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty

from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from dcgui.util import option_name


__all__ = ['HoverBehavior', 'CardObserverBehavior', 'CardOptionMenuBehavior']


class HoverBehavior(EventDispatcher):

    hovering = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_hover_start')
        self.register_event_type('on_hover_end')

        def _check_pos(window, pos):
            collision = self.collide_point(*self.to_widget(*pos))
            if not self.hovering and collision:
                self.hovering = True
            elif self.hovering and not collision:
                self.hovering = False

        Window.bind(mouse_pos=_check_pos)

    def on_hovering(self, instance, value):
        if value:
            self.dispatch('on_hover_start')
        else:
            self.dispatch('on_hover_end')

    def on_hover_start(self):
        pass

    def on_hover_end(self):
        pass


class CardObserverBehavior(EventDispatcher):

    __last_card = ObjectProperty(allownone=True)
    card = ObjectProperty(allownone=True)

    def on_card(self, instance, value):
        if self.__last_card:
            self.__last_card.deregister(self)
        self.__last_card = self.card
        if self.card:
            self.card.register(self)


class CardOptionMenuBehavior(ButtonBehavior, CardObserverBehavior):

    options = ListProperty()
    selection = ObjectProperty()
    dropdown = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        super(ButtonBehavior, self).__init__(**kwargs)
        self.register_event_type('on_select_option')
        self.dropdown = DropDown(on_select=self._select_option)

    def on_select_option(self, option):
        pass

    def _select_option(self, dropdown, option):
        self.selection = option
        self.dispatch('on_select_option', self.selection)

    def on_card(self, instance, value):
        super().on_card(instance, value)

    def on_options(self, instance, value):
        self.dropdown.clear_widgets()
        for option in value:
            button = Button(
                text=option_name(option),
                size_hint_y=None,
                height='20dp',
                on_press=lambda button: self.dropdown.select(option)
            )
            self.dropdown.add_widget(button)

    def observe_options(self, card):
        self.options = card.options

    def on_release(self):
        if not self.dropdown.parent and self.options:
            self.dropdown.open(self)
