import os

import gi
from GtkHelper.GtkHelper import ScaleRow
from data.plugins.AudioControl.actions.DeviceBase import DeviceBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


class AdjustVolume(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.volume_adjust: int = 0

    def get_config_rows(self):
        self.volume_adjust_scale = ScaleRow(title=self.plugin_base.lm.get("action.adjust-volume.volume-adjust"),
                                            value=0,
                                            min=-50,
                                            max=50,
                                            step=1,
                                            text_left="-50",
                                            text_right="50"
                                            )
        self.volume_adjust_scale.scale.set_draw_value(True)

        base = super().get_config_rows()
        base.append(self.volume_adjust_scale)

        return base

    #
    # BASE SETTINGS LOADER
    #

    def load_essential_settings(self):
        settings = self.get_settings()

        self.volume_adjust = settings.get("volume-adjust", 0)
        self.display_icon()

        super().load_essential_settings()

    def load_ui_settings(self):
        self.volume_adjust_scale.scale.set_value(self.volume_adjust)

        super().load_ui_settings()

    #
    # EVENTS
    #

    def connect_events(self):
        super().connect_events()

        self.volume_adjust_scale.scale.connect("value-changed", self.on_volume_adjust_changed)

    def disconnect_events(self):
        super().disconnect_events()

        self.volume_adjust_scale.scale.disconnect_by_func(self.on_volume_adjust_changed)

    def on_volume_adjust_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_adjust = self.volume_adjust_scale.scale.get_value()

        self.display_info()
        self.display_icon()

        settings["volume-adjust"] = self.volume_adjust
        self.set_settings(settings)

    def on_key_down(self):
        if None in (self.pulse_device_name, self.volume_adjust):
            self.show_error(1)
            return

        try:
            device = self.get_device(self.pulse_filter)
            self.plugin_base.pulse.volume_change_all_chans(device, self.volume_adjust * 0.01)
        except:
            self.show_error(1)

    #
    # DISPLAY
    #

    def display_info(self):
        self.info = str(self.volume_adjust)
        super().display_info()

    def display_icon(self):
        if self.volume_adjust is None:
            return

        if self.volume_adjust >= 0:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "vol_up.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "vol_down.png"))
