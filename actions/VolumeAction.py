from src.backend.DeckManagement.DeckController import DeckController
from src.backend.PageManagement.Page import Page
from src.backend.PluginManager.ActionBase import ActionBase
from src.backend.PluginManager.PluginBase import PluginBase

from pulsectl import PulseSinkInfo

class VolumeAction(ActionBase):
    def __init__(self, action_id: str, action_name: str,
                 deck_controller: DeckController, page: Page, coords: str, plugin_base: PluginBase):
        super().__init__(action_id=action_id, action_name=action_name,
            deck_controller=deck_controller, page=page, coords=coords, plugin_base=plugin_base)

        self.device_name: str = None
        self.info: str = None
        self.show_info: bool = False

    def update_labels(self):
        if self.show_info:
            self.set_top_label(self.device_name or "")
            self.set_bottom_label(self.info or "")
        else:
            self.set_top_label("")
            self.set_bottom_label("")

    def filter_proplist(self, proplist) -> [str, None]:
        '''
        Alsa:
        device.nick
        device.vendor.name
        device.description

        Non Alsa:
        node.name
        Then same stuff as Alsa
        '''

        name = proplist.get("node.name")

        if name is None or "alsa" in name:
            name = proplist.get("device.product.name", proplist.get("device.description"))
        return name

    def get_volumes_from_sink(self, sink: PulseSinkInfo) -> list[int]:
        sink_volumes = sink.volume.values

        volumes = [int(vol * 100) for vol in sink_volumes]

        return volumes