import os

from GtkHelper.GtkHelper import ComboRow
from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.PluginBase import PluginBase
from .VolumeAction import VolumeAction
import pulsectl

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw

class MicMute(VolumeAction):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.has_configuration = True

        self.plugin_base.connect_to_event("com_gapls_AudioControl::PulseSourceEvent", self.on_source_change)

    def on_ready(self):
        settings = self.get_settings()

        self.device_name = settings.get("device")
        self.show_device = settings.get("show-device") or False
        self.show_volume = settings.get("show-volume") or False

        self.source_index = -1
        self.source_name = None

        self.show_info = (self.show_device or self.show_volume) or False

        self.load_initial_data()

    def get_config_rows(self) -> "list[Adw.PreferencesRow]":
        # Create Model for Combo Row
        self.device_model = Gtk.ListStore.new([str])

        # Create ComboRow
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.mic-mute.combo.title"),
                                   model=self.device_model)

        # Set Combo Row Renderer
        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.device_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.mic-mute.device.switch.title"))
        self.volume_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("actions.mic-mute.volume.switch.title"))

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)
        self.device_switch.connect("notify::active", self.on_switch_change)
        self.volume_switch.connect("notify::active", self.on_switch_change)

        self.load_config_settings()

        return [self.device_row, self.device_switch, self.volume_switch]

    def on_key_down(self):
        if self.device_name is None or not self.source_name:
            self.show_error(1)
            return

        source = self.plugin_base.pulse.get_source_by_name(self.source_name)

        mute_state = 1 if source.mute == 0 else 0

        self.plugin_base.pulse.mute(source, mute_state)
        self.set_image(mute_state)

    def on_device_change(self, *args, **kwargs):
        settings = self.get_settings()
        self.device_name = self.device_model[self.device_row.combo_box.get_active()][0]

        for source in self.plugin_base.pulse.source_list():
            if source.description.__contains__("Monitor"):
                continue

            device_name = self.filter_proplist(source.proplist)

            if device_name == self.device_name:
                self.source_index = source.index
                self.source_name = source.name
                self.device_name = device_name
                self.set_image(source.mute)
                break

        self.update_labels()

        settings["device"] = self.device_name
        self.set_settings(settings)

    def on_switch_change(self, *args, **kwargs):
        settings = self.get_settings()

        self.show_device = self.device_switch.get_active()
        self.show_volume = self.volume_switch.get_active()

        self.show_info = (self.show_device or self.show_volume) or False
        self.update_labels()

        settings["show-device"] = self.show_device
        settings["show-volume"] = self.show_volume
        self.set_settings(settings)

    async def on_source_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if event.index == self.source_index:
            with pulsectl.Pulse("mic-mute-event") as pulse:
                try:
                    source = pulse.get_source_by_name(self.source_name)
                    self.set_image(source.mute)
                    self.update_labels()
                except:
                    self.show_error(1)

    #
    # LOADS
    #

    def load_device_model(self):
        self.device_model.clear()
        for source in self.plugin_base.pulse.source_list():
            if source.description.__contains__("Monitor"):
                continue

            device_name = self.filter_proplist(source.proplist)

            if device_name is None:
                continue
            self.device_model.append([device_name])

    def load_config_settings(self):
        for i, device in enumerate(self.device_model):
            if device[0] == self.device_name:
                self.device_row.combo_box.set_active(i)
                break

        self.device_switch.disconnect_by_func(self.on_switch_change)
        self.volume_switch.disconnect_by_func(self.on_switch_change)

        self.device_switch.set_active(self.show_device)
        self.volume_switch.set_active(self.show_volume)

        self.device_switch.connect("notify::active", self.on_switch_change)
        self.volume_switch.connect("notify::active", self.on_switch_change)

        if self.device_name is None:
            self.device_row.combo_box.set_active(-1)


    def load_initial_data(self):
        if self.device_name:
            with pulsectl.Pulse("initial-data-load") as pulse:
                for source in pulse.source_list():
                    if source.description.__contains__("Monitor"):
                        continue

                    name = self.filter_proplist(source.proplist)

                    if name == self.device_name:
                        self.source_index = source.index
                        self.source_name = source.name
                        self.set_image(source.mute)
                        break
        self.update_labels()

    #
    # MISC
    #

    def update_volume_info(self, source):
        volumes = self.get_volumes_from_source(source)
        if len(volumes) > 0:
            self.info = str(int(volumes[0]))
        else:
            self.info = ""

    def update_labels(self):
        if self.show_device:
            self.set_top_label(self.device_name)
        else:
            self.set_top_label("")

        try:
            source = self.plugin_base.pulse.get_source_by_name(self.source_name)
            self.update_volume_info(source)
        except:
            self.show_error(1)

        if self.show_volume:
            self.set_bottom_label(self.info)
        else:
            self.set_bottom_label("")

    def set_image(self, mute_state):
        # TODO: REPLACE WITH MIC ICON

        if mute_state == 1:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "mute.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "audio.png"))