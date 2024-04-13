from gi.repository import Gtk, Adw

class ScaleRow(Adw.PreferencesRow):
    def __init__(self, title, value: float, min: float, max: float, step: float, text_right: str = "", text_left: str = "", **kwargs):
        super().__init__(title=title, **kwargs)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                margin_start=10, margin_end=10,
                                margin_top=10, margin_bottom=10)
        self.set_child(self.main_box)

        self.label = Gtk.Label(label=title, hexpand=True, xalign=0)
        self.main_box.append(self.label)

        self.adjustment = Gtk.Adjustment.new(value, min, max, step, 1, 0)

        self.scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.adjustment)
        self.scale.set_size_request(200, -1)  # Adjust width as needed
        self.scale.set_tooltip_text(str(value))

        def correct_step_amount(adjustment):
            value = adjustment.get_value()
            step = adjustment.get_step_increment()
            rounded_value = round(value / step) * step
            adjustment.set_value(rounded_value)

        self.adjustment.connect("value-changed", correct_step_amount)

        self.label_right = Gtk.Label(label=text_right, hexpand=False, xalign=0)

        self.label_left = Gtk.Label(label=text_left, hexpand=False, xalign=0)

        self.main_box.append(self.label_left)
        self.main_box.append(self.scale)
        self.main_box.append(self.label_right)