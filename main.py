# Import StreamController modules

import pulsectl
from src.backend.PluginManager.ActionHolder import ActionHolder
from src.backend.PluginManager.PluginBase import PluginBase

from .actions.AdjustVolume import AdjustVolume
from .actions.Mute import Mute
from .actions.SetVolume import SetVolume
from .actions.VolumeDisplay import VolumeDisplay
from .internal.PulseEventListener import PulseEvent


class AudioControl(PluginBase):
    def __init__(self):
        super().__init__()
        self.init_vars()

        self.mute_action_holder = ActionHolder(
            plugin_base=self,
            action_base=Mute,
            action_id="com_gapls_AudioControl::Mute",
            action_name=self.lm.get("action.name.mute")
        )
        self.add_action_holder(self.mute_action_holder)

        self.set_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=SetVolume,
            action_id="com_gapls_AudioControl::SetVolume",
            action_name=self.lm.get("action.name.set-volume")
        )
        self.add_action_holder(self.set_volume_action_holder)

        self.adjust_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=AdjustVolume,
            action_id="com_gapls_AudioControl::AdjustVolume",
            action_name=self.lm.get("action.name.adjust-volume")
        )
        self.add_action_holder(self.adjust_volume_action_holder)

        self.volume_display_action_holder = ActionHolder(
            plugin_base=self,
            action_base=VolumeDisplay,
            action_id="com_gapls_AudioControl::VolumeDisplay",
            action_name=self.lm.get("action.name.volume-display")
        )
        self.add_action_holder(self.volume_display_action_holder)

        # Events

        self.pulse_sink_event_holder = PulseEvent(
            self,
            "com_gapls_AudioControl::PulseEvent",
            "sink", "source"
        )
        self.add_event_holder(self.pulse_sink_event_holder)

        self.register()

    def init_vars(self):
        self.lm = self.locale_manager
        self.pulse = pulsectl.Pulse("audio-control-main")
