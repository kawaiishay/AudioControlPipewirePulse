from gi.repository import Gtk, Adw

class SwitchRow(Adw.PreferencesRow):
    x = True
    def __init__(self, title, state, **kwargs):
        super().__init__(title=title, **kwargs)
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL,
                                margin_start=10, margin_end=10,
                                margin_top=10, margin_bottom=10)
        self.set_child(self.main_box)

        self.label = Gtk.Label(label=title, hexpand=True, xalign=0)
        self.main_box.append(self.label)

        self.switch = Gtk.Switch()
        self.switch.set_active(state)
        self.main_box.append(self.switch)

    def connect(self, callback):
        self.switch.connect("notify::active", callback)