# Import StreamController modules

from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase
import pulsectl

# Import python modules

# Import gtk modules - used for the config rows
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk


# TODO: POSTBONED BECAUSE PULSE STUFF
class VolumeDisplay(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
                         deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    def on_ready(self):
        self.sink = None
        self.set_sink(self.get_settings().get("device"))

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])  # First Column: Name,
        self.device_row = ComboRow(title="Audio Device",
                                   model=self.device_model)

        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)

        self.load_config_settings()

        return [self.device_row]

    def filter_proplist(self, proplist) -> [str, None]:
        name = proplist.get("node.name")

        if name is None or "alsa" in name:
            name = proplist.get("device.product.name", proplist.get("device.description"))

        return name

    def load_device_model(self):
        self.device_model.clear()
        with pulsectl.Pulse() as pulse:
            for sink in pulse.sink_list():
                proplist = sink.proplist
                name = self.filter_proplist(proplist)

                if name is None:
                    continue
                self.device_model.append([name])
                self.sink = sink

    def load_config_settings(self):
        settings = self.get_settings()
        device_name = settings.get("device")
        for i, device in enumerate(self.device_model):
            if device[0] == device_name:
                self.device_row.combo_box.set_active(i)
                break

        if device_name is None:
            self.device_row.combo_box.set_active(-1)
            return

    def on_device_change(self, combo_box, *args):
        name = self.device_model[combo_box.get_active()][0]
        settings = self.get_settings()
        settings["device"] = name
        self.set_sink(name)
        self.set_settings(settings)

    def set_sink(self, device_name):
        with pulsectl.Pulse() as pulse:
            for sink in pulse.sink_list():
                proplist = sink.proplist
                name = self.filter_proplist(proplist)

                if name != device_name:
                    continue

                self.sink = sink
                break

    def on_tick(self):
        if self.sink is None:
            return
        print(self.sink)

        display = str(int(self.sink.volume.values[0] * 100)) + "%"

        self.set_bottom_label(display)