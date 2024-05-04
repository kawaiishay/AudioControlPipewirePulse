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

class SetVolume(VolumeAction):
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
        self.show_info = settings.get("show-info")
        self.volume_change = settings.get("volume-change")

        self.sink_name = None

        self.load_initial_data()

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])  # First Column: Name,
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.set-vol.combo.title"),
                                   model=self.device_model)

        self.scale_row = ScaleRow(title=self.plugin_base.lm.get("actions.set-vol.scale.title"), value=0, min=0, max=100, step=1, text_left="0", text_right="100")
        self.scale_row.scale.set_draw_value(True)

        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.info_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.set-vol.switch.title"))

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)
        self.scale_row.scale.connect("value-changed", self.on_volume_change)
        self.info_switch.connect("notify::active", self.on_switch_change)

        self.load_config_settings()

        return [self.device_row, self.scale_row, self.info_switch]

    def on_key_down(self):
        if None in (self.device_name, self.volume_change):
            self.show_error(1)
            return

        sink = self.plugin_base.pulse.get_sink_by_name(self.sink_name)
        self.plugin_base.pulse.volume_set_all_chans(sink, self.volume_change * 0.01)

    #
    # CUSTOM EVENTS
    #

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

    def on_volume_change(self, scale):
        settings = self.get_settings()

        self.volume_change = scale.get_value()
        scale.set_tooltip_text(str(self.volume_change))

        self.info = str(int(self.volume_change or 0) or "0")
        self.update_labels()

        settings["volume-change"] = self.volume_change
        self.set_settings(settings)

    def on_switch_change(self, *args, **kwargs):
        settings = self.get_settings()

        switch_state = self.info_switch.get_active()
        self.show_info = switch_state
        self.update_labels()

        settings["show-info"] = switch_state
        self.set_settings(settings)

    #
    # HELPER FUNCTIONS
    #

    def load_device_model(self):
        self.device_model.clear()

        for sink in self.plugin_base.pulse.sink_list():
            device_name = self.filter_proplist(sink.proplist)

            if device_name is None:
                continue
            self.device_model.append([device_name])

    def load_config_settings(self):

        if self.device_name is not None:
            for i, device in enumerate(self.device_model):
                if device[0] == self.device_name:
                    self.device_row.combo_box.set_active(i)
                    break
        else:
            self.device_row.combo_box.set_active(-1)

        if self.volume_change is not None:
            self.scale_row.scale.set_value(self.volume_change or 0)

        if self.show_info:
            self.info_switch.set_active(self.show_info or False)

    def load_initial_data(self):
        if self.device_name:
            for sink in self.plugin_base.pulse.sink_list():
                name = self.filter_proplist(sink.proplist)

                if name == self.device_name:
                    self.sink_name = sink.name

        self.info = str(int(self.volume_change or 0) or "0")

        self.update_labels()