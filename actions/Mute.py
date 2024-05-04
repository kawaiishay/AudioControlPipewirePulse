# Import StreamController modules
from .VolumeAction import VolumeAction

try:
    from GtkHelper.GtkHelper import ScaleRow
except ImportError:
    from ..internal.ScaleRow import ScaleRow

from GtkHelper.GtkHelper import ComboRow
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

class Mute(VolumeAction):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.has_configuration = True
        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent", callback=self.on_sink_change)

    #
    # OVERRIDDEN
    #

    def on_ready(self):
        super().on_ready()

        # LOAD VALUES FROM SETTINGS
        # device, show-info

        self.device_name = self.get_settings().get("device")
        self.show_info = self.get_settings().get("show-info") or False

        self.sink_index = -1
        self.sink_name = None  # Used for faster Lookups / Less Code

        # Sets Mute Image and sets the other default vars
        self.load_initial_data()

    def get_config_rows(self) -> list:
        # Create Model for Combo Row
        self.device_model = Gtk.ListStore.new([str])

        # Create ComboRow
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.mute.combo.title"),
                                   model=self.device_model)

        # Set Combo Row Renderer
        self.device_cell_renderer = Gtk.CellRendererText()
        self.device_row.combo_box.pack_start(self.device_cell_renderer, True)
        self.device_row.combo_box.add_attribute(self.device_cell_renderer, "text", 0)

        self.info_switch = Adw.SwitchRow(title="Show Information")  # Todo: Change with translations

        self.load_device_model()

        self.device_row.combo_box.connect("changed", self.on_device_change)
        self.info_switch.connect("notify::active", self.on_switch_change)

        self.load_config_settings()

        return [self.device_row, self.info_switch]

    def on_key_down(self):
        settings = self.get_settings()
        device_name = settings.get("device")

        if device_name is None:
            self.show_error(1)
            return

        with pulsectl.Pulse("volume-changer-mute-key") as pulse:
            for sink in pulse.sink_list():
                proplist = sink.proplist
                name = self.filter_proplist(proplist)

                if name != device_name:
                    continue

                mute_state = 1 if sink.mute == 0 else 0

                pulse.mute(sink, mute_state)
                self.set_image(mute_state)
                break

    #
    # CUSTOM EVENTS
    #

    def on_device_change(self, combo_box, *args):
        settings = self.get_settings()
        self.device_name = self.device_model[combo_box.get_active()][0]

        for sink in self.plugin_base.pulse.sink_list():
            name = self.filter_proplist(sink.proplist)

            if name == self.device_name:
                self.sink_index = sink.index
                self.sink_name = sink.name

                self.set_image(sink.mute)
                break

        self.update_labels()

        settings["device"] = self.device_name
        self.set_settings(settings)

    def on_switch_change(self, *args, **kwargs):
        settings = self.get_settings()

        switch_state = self.info_switch.get_active()
        self.show_info = switch_state
        self.update_labels()

        settings["show-info"] = switch_state
        self.set_settings(settings)

    async def on_sink_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if event.index == self.sink_index:
            with pulsectl.Pulse("volume-changer-mute-event") as pulse:
                for sink in pulse.sink_list():
                    if sink.index == self.sink_index:
                        self.set_image(sink.mute)
                        break

    #
    # MODELS
    #

    def load_device_model(self):
        self.device_model.clear()
        for sink in self.plugin_base.pulse.sink_list():
            device_name = self.filter_proplist(sink.proplist)

            if device_name is None:
                continue
            self.device_model.append([device_name])

    #
    # LOAD SETTINGS
    #

    def load_config_settings(self):
        # Sets the Values in the UI
        for i, device in enumerate(self.device_model):
            if device[0] == self.device_name:
                self.device_row.combo_box.set_active(i)
                break

        self.info_switch.set_active(self.show_info)

        if self.device_name is None:
            self.device_row.combo_box.set_active(-1)

    def load_initial_data(self):
        """
        Loads the Initial Values used by the Action
        """

        # Sets the Mute Image based on the Device Name
        if self.device_name:
            for sink in self.plugin_base.pulse.sink_list():
                name = self.filter_proplist(sink.proplist)

                if name == self.device_name:
                    # Sets the Sink Index and Sink Name
                    self.sink_index = sink.index
                    self.sink_name = sink.name

                    self.set_image(sink.mute)
                    break

        # Displays Specified Information on Labels
        self.update_labels()

    #
    # MISC
    #

    def set_image(self, mute_state):
        if mute_state == 1:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "mute.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "audio.png"))