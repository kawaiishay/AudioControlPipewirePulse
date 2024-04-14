# Import StreamController modules

try:
    from GtkHelper.GtkHelper import ScaleRow
except ImportError:
    from ..internal.ScaleRow import ScaleRow

try:
    from GtkHelper.GtkHelper import SwitchRow
except ImportError:
    from ..internal.SwitchRow import SwitchRow

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

    #
    # OVERRIDDEN
    #

    def on_ready(self):
        settings = self.get_settings()
        volume = self.get_settings().get("volume_change")
        self.set_volume_label(settings.get("display"), volume)
        self.set_image(volume)

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])

        # Device Dropdown
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.adjust-vol.combo.title"),
                                   model=self.device_model)

        # Volume Slider
        self.scale_row = ScaleRow(title=self.plugin_base.lm.get("actions.adjust-vol.scale.title"), value=0, min=-25, max=25, step=1, text_left="-25", text_right="+25")

        self.switch_row = SwitchRow(title="Display Volume Change")

        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)
        self.scale_row.scale.connect("value-changed", self.on_volume_change)
        self.switch_row.switch.connect("notify::active", self.on_switch_change)

        self.load_config_settings()

        return [self.device_row, self.scale_row, self.switch_row]

    def on_key_down(self):
        settings = self.get_settings()
        device_name = settings.get("device")
        volume_change = settings.get("volume_change")

        if None in (device_name, volume_change):
            self.show_error(1)
            return

        with pulsectl.Pulse("volume-changer-va-key") as pulse:
            for sink in pulse.sink_list():
                proplist = sink.proplist
                name = self.filter_proplist_for_name(proplist)

                if name != device_name:
                    continue

                pulse.volume_change_all_chans(sink, volume_change * 0.01)
                # volumes = [max(vol + volume_change * 0.01, 0) for vol in sink.volume.values]
                #self.plugin_base.pulse.volume_set(sink, pulsectl.PulseVolumeInfo(volumes, len(volumes)))
                break

    #
    # CUSTOM EVENTS
    #

    def on_volume_change(self, scale):
        volume = scale.get_value()
        settings = self.get_settings()
        settings["volume_change"] = volume
        volume_text = ("+" if volume > 0 else "") + str(volume)
        scale.set_tooltip_text(volume_text)
        self.set_settings(settings)
        self.set_image(volume)
        self.set_volume_label(settings.get("display"), volume)

    def on_device_change(self, combo_box, *args):
        name = self.device_model[combo_box.get_active()][0]
        settings = self.get_settings()
        settings["device"] = name
        self.set_settings(settings)

    def on_switch_change(self, switch, gstate):
        state = switch.get_active()
        settings = self.get_settings()
        settings["display"] = state
        self.set_settings(settings)
        self.set_volume_label(state, settings.get("volume_change"))

    #
    # HELPER FUNCTIONS
    #

    # Get all current sinks and append the names for the dropdowns
    def load_device_model(self):
        self.device_model.clear()
        device_name = self.get_settings().get("device")
        with pulsectl.Pulse("volume-changer-va-device") as pulse:
            for sink in pulse.sink_list():
                name = self.filter_proplist_for_name(sink.proplist)

                if name is None:
                    continue
                self.device_model.append([name])

    # Loads the Config into the UI
    def load_config_settings(self):
        settings = self.get_settings()
        device_name = settings.get("device")
        volume_change = settings.get("volume_change")
        display = settings.get("display")

        for i, device in enumerate(self.device_model):
            if device[0] == device_name:
                self.device_row.combo_box.set_active(i)
                break

        if device_name is None:
            self.device_row.combo_box.set_active(-1)
        if volume_change is not None:
            self.scale_row.scale.set_value(volume_change)
        if display is not None:
            self.switch_row.switch.set_active(display)

        self.set_volume_label(display, volume_change)

    def filter_proplist_for_name(self, proplist) -> [str, None]:
        name = proplist.get("node.name")

        if name is None or "alsa" in name:
            name = proplist.get("device.product.name", proplist.get("device.description"))

        return name

    def set_image(self, vol_change):
        if vol_change is None: return

        if vol_change >= 0:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "vol_up.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "vol_down.png"))

    def set_volume_label(self, display, volume):
        if display is not None and display:
            self.set_bottom_label(("+" if volume > 0 else "") + str(volume))
        else:
            self.set_bottom_label("")