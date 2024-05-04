# Import StreamController modules
import asyncio
import threading

import pulsectl

from src.backend.PluginManager.EventHolder import EventHolder
from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.VolumeAdjust import VolumeAdjust
from .actions.SetVolume import SetVolume
from .actions.Mute import Mute
from .actions.VolumeDisplay import VolumeDisplay
from .internal.PulseEventListener import PulseEvent


class AudioControl(PluginBase):
    def __init__(self):
        super().__init__()
        self.init_vars()

        ## Register actions
        self.volume_adjust_action_holder = ActionHolder(
            plugin_base=self,
            action_base=VolumeAdjust,
            action_id="com_gapls_AudioControl::AdjustVolume", # Change this to your own plugin id
            action_name=self.lm.get("actions.adjust-vol.name"),
        )
        self.add_action_holder(self.volume_adjust_action_holder)

        self.set_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=SetVolume,
            action_id="com_gapls_AudioControl::SetVolume",  # Change this to your own plugin id
            action_name=self.lm.get("actions.set-vol.name"),
        )
        self.add_action_holder(self.set_volume_action_holder)

        self.mute_action_holder = ActionHolder(
            plugin_base=self,
            action_base=Mute,
            action_id="com_gapls_AudioControl::Mute",  # Change this to your own plugin id
            action_name="Mute",
        )
        self.add_action_holder(self.mute_action_holder)

        self.volume_display_action_holder = ActionHolder(
            plugin_base=self,
            action_base=VolumeDisplay,
            action_id="com_gapls_AudioControl::VolumeDisplay",  # Change this to your own plugin id
            action_name="Volume Display",
        )
        #self.add_action_holder(self.volume_display_action_holder)


        self.pulse_event_holder = PulseEvent(
            plugin_base=self,
            event_id="com_gapls_AudioControl::PulseEvent"
        )
        self.add_event_holder(self.pulse_event_holder)

        self.register()

    def init_vars(self):
        self.lm = self.locale_manager
        self.pulse = pulsectl.Pulse("audio-control-main")