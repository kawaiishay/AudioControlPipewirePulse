# Import StreamController modules
import asyncio
import threading

import pulsectl

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from .actions.VolumeAdjust import VolumeAdjust
from .actions.SetVolume import SetVolume
from .actions.Mute import Mute
from .actions.VolumeDisplay import VolumeDisplay
from .internal.Observer import Observer


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
        self.add_action_holder(self.volume_display_action_holder)

        # Register plugin
        self.register(
            plugin_name = "AudioControl",
            github_repo = "https://github.com/G4PLS/AudioControl",
            plugin_version = "1.1.0-alpha",
            app_version = "1.4.11-beta"
        )

    def init_vars(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()
        self.observer = Observer()

        pulse_event_loop = threading.Thread(target=self.start_event_loop)
        pulse_event_loop.daemon = True
        pulse_event_loop.start()

    def start_event_loop(self):
        self.loop()

    def loop(self):
        with pulsectl.Pulse("volume-controller-event-loop") as pulse:
            pulse.event_mask_set("sink")
            pulse.event_callback_set(lambda event: self.observer.notify_observers(event))
            while True:
                pulse.event_listen()