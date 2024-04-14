# Import StreamController modules
try:
    from GtkHelper.GtkHelper import ScaleRow
except ImportError:
    from ..internal.ScaleRow import ScaleRow

from GtkHelper.GtkHelper import ComboRow
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase
import pulsectl

# Import python modules
import os

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class VolumeDisplay(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    #
    # OVERRIDDEN
    #

    def on_ready(self):
        device_name = self.get_settings().get("device")
        self.sink_index = -1
        self.text = ""
        self.plugin_base.observer.add_observer(self.on_sink_change)

        if device_name is None:
            return

        # Needed so that pulse doesnt throw an error
        with pulsectl.Pulse("volume-controller-volume-display") as pulse:
            for sink in pulse.sink_list():
                name = self.filter_proplist(sink.proplist)

                if name == device_name:
                    self.sink_index = sink.index
                    self.set_volume_text(sink.volume.values)
                    break

    def on_tick(self):
        self.set_bottom_label(self.text)
        self.set_top_label(self.get_settings().get("device"))

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])  # First Column: Name,
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.set-vol.combo.title"),
                                   model=self.device_model)

        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)

        self.load_config_settings()

        return [self.device_row]

    #
    # CUSTOM EVENTS
    #

    def on_device_change(self, combo_box, *args):
        device_name = self.device_model[combo_box.get_active()][0]
        settings = self.get_settings()
        settings["device"] = device_name
        self.set_settings(settings)

        with pulsectl.Pulse("volume-controller-vd-device") as pulse:
            for sink in pulse.sink_list():
                name = self.filter_proplist(sink.proplist)

                if name == device_name:
                    self.sink_index = sink.index
                    break

    def on_sink_change(self, event):
        if event.index == self.sink_index:
            with pulsectl.Pulse("volume-changer-vd-event") as pulse:
                for sink in pulse.sink_list():
                    if sink.index == self.sink_index:
                        self.set_volume_text(sink.volume.values)
                        break

    #
    # HELPER FUNCTIONS
    #

    def load_device_model(self):
        self.device_model.clear()
        with pulsectl.Pulse("volume-changer-vd-model") as pulse:
            for sink in pulse.sink_list():
                proplist = sink.proplist
                device_name = self.filter_proplist(proplist)

                if device_name is None:
                    continue
                if device_name == self.get_settings().get("device"):
                    self.sink_index = sink.index
                self.device_model.append([device_name])

    def load_config_settings(self):
        settings = self.get_settings()
        device_name = settings.get("device")
        for i, device in enumerate(self.device_model):
            if device[0] == device_name:
                self.device_row.combo_box.set_active(i)
                break

        if device_name is None:
            self.device_row.combo_box.set_active(-1)

    def filter_proplist(self, proplist) -> [str, None]:
        name = proplist.get("node.name")

        if name is None or "alsa" in name:
            name = proplist.get("device.product.name", proplist.get("device.description"))
        return name

    def set_volume_text(self, volumes):
        volumes = [int(vol * 100) for vol in volumes]
        self.text = str(volumes)