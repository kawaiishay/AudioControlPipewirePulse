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

class VolumeAdjust(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])  # First Column: Name,
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.adjust-vol.combo.title"),
                                   model=self.device_model)

        self.scale_row = ScaleRow(title=self.plugin_base.lm.get("actions.adjust-vol.scale.title"), value=0, min=-25, max=25, step=1, text_left="-25", text_right="+25")

        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)
        self.scale_row.scale.connect("value-changed", self.on_volume_change)

        self.load_config_settings()

        return [self.device_row, self.scale_row]

    def filter_proplist(self, proplist) -> [str, None]:
        name = proplist.get("node.name")

        if name is None or "alsa" in name:
            name = proplist.get("device.product.name", proplist.get("device.description"))

        return name

    def load_device_model(self):
        self.device_model.clear()
        for sink in self.plugin_base.pulse.sink_list():
            proplist = sink.proplist
            name = self.filter_proplist(proplist)

            if name is None:
                continue
            self.device_model.append([name])

    def load_config_settings(self):
        settings = self.get_settings()
        device_name = settings.get("device")
        volume_change = settings.get("volume_change")
        for i, device in enumerate(self.device_model):
            if device[0] == device_name:
                self.device_row.combo_box.set_active(i)
                break

        if device_name is None:
            self.device_row.combo_box.set_active(-1)
        if volume_change is not None:
            self.scale_row.scale.set_value(volume_change)

    def on_device_change(self, combo_box, *args):
        name = self.device_model[combo_box.get_active()][0]
        settings = self.get_settings()
        settings["device"] = name
        self.set_settings(settings)

    def on_volume_change(self, scale):
        name = scale.get_value()
        settings = self.get_settings()
        settings["volume_change"] = name
        self.set_settings(settings)

    def on_key_down(self):
        settings = self.get_settings()
        device_name = settings.get("device")
        volume_change = settings.get("volume_change", 0)

        if None in (device_name, volume_change):
            self.show_error(1)
            return

        for sink in self.plugin_base.pulse.sink_list():
            proplist = sink.proplist
            name = self.filter_proplist(proplist)

            if name != device_name:
                continue

            volumes = [max(vol + volume_change * 0.01, 0) for vol in sink.volume.values]

            self.plugin_base.pulse.volume_set(sink, pulsectl.PulseVolumeInfo(volumes, len(volumes)))

            break