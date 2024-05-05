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

# Import gtk modules - used for the config rows
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk


class VolumeDisplay(VolumeAction):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.has_configuration = True
        self.plugin_base.connect_to_event("com_gapls_AudioControl::PulseSinkEvent", self.on_sink_change)

    #
    # OVERRIDDEN
    #

    def on_ready(self):
        settings = self.get_settings()

        self.device_name = settings.get("device")

        self.sink_index = -1
        self.sink_name = None
        self.show_info = True

        self.load_initial_data()

    def get_config_rows(self) -> list:
        self.device_model = Gtk.ListStore.new([str])  # First Column: Name,
        self.device_row = ComboRow(title=self.plugin_base.lm.get("actions.vd.combo.title"),
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
        settings = self.get_settings()

        self.device_name = self.device_model[combo_box.get_active()][0]

        for sink in self.plugin_base.pulse.sink_list():
            name = self.filter_proplist(sink.proplist)

            if name == self.device_name:
                self.sink_index = sink.index
                self.sink_name = sink.name
                self.update_volume_info(sink)
                break

        self.update_labels()

        settings["device"] = self.device_name
        self.set_settings(settings)

    def on_sink_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if event.index == self.sink_index:
            with pulsectl.Pulse("volume-display-event") as pulse:
                try:
                    sink = pulse.get_sink_by_name(self.sink_name)
                    self.update_volume_info(sink)
                    self.update_labels()
                except:
                    self.show_error(1)

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
        for i, device in enumerate(self.device_model):
            if device[0] == self.device_name:
                self.device_row.combo_box.set_active(i)
                break

        if self.device_name is None:
            self.device_row.combo_box.set_active(-1)

    def set_volume_text(self, volumes):
        volumes = [int(vol * 100) for vol in volumes]
        if len(volumes) <= 0:
            self.text = ""
        else:
            self.text = f'{volumes[0]}%'

    def load_initial_data(self):
        if self.device_name:
            with pulsectl.Pulse("initial-data-load") as pulse:
                for sink in pulse.sink_list():
                    name = self.filter_proplist(sink.proplist)

                    if name == self.device_name:
                        self.sink_index = sink.index
                        self.sink_name = sink.name
                        self.update_volume_info(sink)
                        break

        self.update_labels()

    def update_volume_info(self, sink):
        volumes = self.get_volumes_from_sink(sink)
        if len(volumes) > 0:
            self.info = str(int(volumes[0]))
        else:
            self.info = ""