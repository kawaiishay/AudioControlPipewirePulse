# Import StreamController modules
import pulsectl

from src.backend.PluginManager.PluginBase import PluginBase
from src.backend.PluginManager.ActionHolder import ActionHolder

# Import actions
from plugins.AudioControl.actions.VolumeAdjust import VolumeAdjust
from plugins.AudioControl.actions.SetVolume import SetVolume
from plugins.AudioControl.actions.VolumeDisplay import VolumeDisplay

class PluginTemplate(PluginBase):
    def __init__(self):
        super().__init__()
        self.init_vars()

        ## Register actions
        self.volume_adjust_action_holder = ActionHolder(
            plugin_base=self,
            action_base=VolumeAdjust,
            action_id="com_gapls_AudioControl::AdjustVolume", # Change this to your own plugin id
            action_name="Volume Adjust",
        )
        self.add_action_holder(self.volume_adjust_action_holder)

        self.set_volume_action_holder = ActionHolder(
            plugin_base=self,
            action_base=SetVolume,
            action_id="com_gapls_AudioControl::SetVolume",  # Change this to your own plugin id
            action_name="Set Volume",
        )
        self.add_action_holder(self.set_volume_action_holder)

        #self.volume_display_action_holder = ActionHolder(
        #    plugin_base=self,
        #    action_base=VolumeDisplay,
        #    action_id="com_gapls_AudioControl::VolumeDisplay",  # Change this to your own plugin id
        #    action_name="Display Volume",
        #)
        #self.add_action_holder(self.volume_display_action_holder)

        # Register plugin
        self.register(
            plugin_name = "AudioControl",
            github_repo = "https://github.com/G4PLS/AudioControl",
            plugin_version = "1.0.0-alpha",
            app_version = "1.4.9-beta"
        )

    def init_vars(self):
        self.pulse = pulsectl.Pulse("volume-controller", threading_lock=True)

