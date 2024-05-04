# Import StreamController modules
from .VolumeAction import VolumeAction

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

class VolumeAdjust(VolumeAction):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.has_configuration = True

    #
    # OVERRIDDEN
    #

    def on_ready(self):
        settings = self.get_settings()

        self.device_name = settings.get("device")
        self.volume_adjust = settings.get("volume-adjust") or 0
        self.show_device: bool = settings.get("show-device") or False
        self.show_volume: bool = settings.get("show-adjust") or False

        self.show_info = (self.show_device or self.show_volume) or False

        self.sink_name = None

        self.load_initial_data()

        #self.set_volume_label(settings.get("display"), volume)
        #self.set_image(volume)

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])

        # Device Dropdown
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.adjust-vol.combo.title"),
                                   model=self.device_model)
        # Volume Slider
        self.scale_row = ScaleRow(title=self.plugin_base.lm.get("actions.adjust-vol.scale.title"), value=0, min=-25, max=25, step=1, text_left="-25", text_right="+25")
        self.scale_row.scale.set_draw_value(True)

        self.device_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.adjust-vol.device-switch.title"))
        self.volume_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.adjust-vol.volume-switch.title"))

        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)
        self.scale_row.scale.connect("value-changed", self.on_volume_change)
        self.device_switch.connect("notify::active", self.on_switch_change)
        self.volume_switch.connect("notify::active", self.on_switch_change)

        self.load_config_settings()

        return [self.device_row, self.scale_row, self.device_switch, self.volume_switch]

    def on_key_down(self):
        if None in (self.device_name, self.volume_adjust) or not self.sink_name:
            self.show_error(1)
            return

        sink = self.plugin_base.pulse.get_sink_by_name(self.sink_name)
        self.plugin_base.pulse.volume_change_all_chans(sink, self.volume_adjust * 0.01)

    #
    # CUSTOM EVENTS
    #

    def on_volume_change(self, scale):
        settings = self.get_settings()

        self.volume_adjust = scale.get_value()

        self.info = ("+" if self.volume_adjust > 0 else "") + str(self.volume_adjust)
        scale.set_tooltip_text(self.info)

        self.update_labels()
        self.set_image()

        settings["volume-adjust"] = self.volume_adjust
        self.set_settings(settings)

    def on_device_change(self, combo_box, *args):
        settings = self.get_settings()

        self.device_name = self.device_model[combo_box.get_active()][0]

        for sink in self.plugin_base.pulse.sink_list():
            device_name = self.filter_proplist(sink.proplist)

            if device_name == self.device_name:
                self.sink_name = sink.name
                self.device_name = device_name
                break

        self.update_labels()

        settings["device"] = self.device_name
        self.set_settings(settings)

    def on_switch_change(self, switch, gstate):
        settings = self.get_settings()
        state = switch.get_active()

        self.show_device = self.device_switch.get_active()
        self.show_volume = self.volume_switch.get_active()

        self.show_info = (self.show_device or self.show_volume) or False
        self.update_labels()

        settings["show-device"] = self.show_device
        settings["show-adjust"] = self.show_volume
        self.set_settings(settings)

    #
    # HELPER FUNCTIONS
    #

    # Get all current sinks and append the names for the dropdowns
    def load_device_model(self):
        self.device_model.clear()

        for sink in self.plugin_base.pulse.sink_list():
            name = self.filter_proplist(sink.proplist)

            if name is None:
                continue
            self.device_model.append([name])

    # Loads the Config into the UI
    def load_config_settings(self):
        for i, device in enumerate(self.device_model):
            if device[0] == self.device_name:
                self.device_row.combo_box.set_active(i)
                break

        self.scale_row.scale.set_value(self.volume_adjust)

        self.device_switch.disconnect_by_func(self.on_switch_change)
        self.volume_switch.disconnect_by_func(self.on_switch_change)

        self.device_switch.set_active(self.show_device)
        self.volume_switch.set_active(self.show_volume)

        self.device_switch.connect("notify::active", self.on_switch_change)
        self.volume_switch.connect("notify::active", self.on_switch_change)

        if self.device_name is None:
            self.device_row.combo_box.set_active(-1)

    def set_image(self):
        if self.volume_adjust is None: return

        if self.volume_adjust >= 0:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "vol_up.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "vol_down.png"))

    def load_initial_data(self):
        if self.device_name:
            with pulsectl.Pulse("initial-data-load") as pulse:
                for sink in pulse.sink_list():
                    name = self.filter_proplist(sink.proplist)

                    if name == self.device_name:
                        self.sink_name = sink.name

        self.info = ("+" if self.volume_adjust > 0 else "") + str(self.volume_adjust)
        self.set_image()

        self.update_labels()


    def update_labels(self):
        if self.show_device:
            self.set_top_label(self.device_name)
        else:
            self.set_top_label("")

        if self.show_volume:
            self.set_bottom_label(self.info)
        else:
            self.set_bottom_label("")