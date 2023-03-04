import functools

from kivy.lang import Builder
from kivy.properties import ListProperty, ObjectProperty, StringProperty

from kivy.uix.modalview import ModalView


Builder.load_string('''\
<OptionMenu>:
    pos_hint: {'center_x': .5, 'center_y': .5}
    size_hint: None, None
    size: dp(300), dp(240)

    BoxLayout:
        orientation: 'vertical'
    
        Label:
            text: root.hint
            size_hint_y: None
            height: dp(80)
    
        RecycleView:
            id: recycle_view
            viewclass: 'Button'
            smooth_scroll_end: 10
            
            RecycleBoxLayout:
            
                orientation: 'vertical'
                default_size_hint: 1, None
                padding: dp(10)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
''')


class OptionMenu(ModalView):

    hint = StringProperty()
    options = ListProperty()
    auto_dismiss = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_event_type('on_select')

    def on_select(self, option):
        pass

    def on_options(self, instance, value):
        self.ids.recycle_view.data = [
            {
                'text': option.selection,
                'on_press': functools.partial(self.dispatch, 'on_select', option)
            }
            for option in self.options
        ]
