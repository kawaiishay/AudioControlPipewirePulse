# Import StreamController modules
import pulsectl

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from data.plugins.AudioControlPlugin.actions.VolumeAdjust import VolumeAdjust
from data.plugins.AudioControlPlugin.actions.SetVolume import SetVolume
from data.plugins.AudioControlPlugin.actions.Mute import Mute

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

        # Register plugin
        self.register(
            plugin_name = "AudioControl",
            github_repo = "https://github.com/G4PLS/AudioControl",
            plugin_version = "1.0.0-alpha",
            app_version = "1.4.10-beta"
        )

    def init_vars(self):
        self.lm = self.locale_manager
        self.lm.set_to_os_default()
        self.pulse = pulsectl.Pulse("volume-controller")