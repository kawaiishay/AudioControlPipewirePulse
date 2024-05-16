import gi

from GtkHelper.GtkHelper import ScaleRow
from data.plugins.AudioControl.actions.DeviceBase import DeviceBase

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw


class SetVolume(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.volume_change: int = 0
        self.extend_volume: bool = False

    def get_config_rows(self):
        self.extend_volume_switch = Adw.SwitchRow(title=self.plugin_base.lm.get("action.set-volume.extend-volume"))

        self.volume_scale = ScaleRow(title=self.plugin_base.lm.get("action.set-volume.volume"),
                                     value=0,
                                     min=0,
                                     max=100,
                                     step=1,
                                     text_left="0",
                                     text_right="100"
                                     )
        self.volume_scale.scale.set_draw_value(True)

        base = super().get_config_rows()

        base.append(self.extend_volume_switch)
        base.append(self.volume_scale)

        return base

    #
    # BASE SETTINGS LOADER
    #

    def load_essential_settings(self):
        settings = self.get_settings()
        self.volume_change = settings.get("volume", 0)
        self.extend_volume = settings.get("volume-extend", False)

        super().load_essential_settings()

    def load_ui_settings(self):
        self.extend_volume_switch.set_active(self.extend_volume)

        if self.extend_volume:
            self.volume_scale.adjustment.set_upper(150)
            self.volume_scale.label_right.set_label("150")

        self.volume_scale.scale.set_value(self.volume_change)

        super().load_ui_settings()

    #
    # EVENTS
    #

    def connect_events(self):
        super().connect_events()

        self.extend_volume_switch.connect("notify::active", self.on_extend_volume_changed)
        self.volume_scale.scale.connect("value-changed", self.on_volume_changed)

    def disconnect_events(self):
        super().disconnect_events()

        self.extend_volume_switch.disconnect_by_func(self.on_extend_volume_changed)
        self.volume_scale.scale.disconnect_by_func(self.on_volume_changed)

    def on_extend_volume_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.extend_volume = self.extend_volume_switch.get_active()

        extended_volume = 150 if self.extend_volume else 100

        self.volume_scale.adjustment.set_upper(extended_volume)
        self.volume_scale.label_right.set_label(str(extended_volume))

        if not self.extend_volume and self.volume_scale.scale.get_value() > 100:
            self.volume_scale.scale.set_value(100)

        settings["volume-extend"] = self.extend_volume
        self.set_settings(settings)

    def on_volume_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_change = self.volume_scale.scale.get_value()

        self.display_info()

        settings["volume"] = self.volume_change
        self.set_settings(settings)

    def on_key_down(self):
        if None in (self.pulse_device_name, self.volume_change):
            self.show_error(1)
            return

        try:
            device = self.get_device(self.pulse_filter)
            self.plugin_base.pulse.volume_set_all_chans(device, self.volume_change * 0.01)
        except:
            self.show_error(1)

    #
    # DISPLAY
    #

    def display_info(self):
        self.info = str(self.volume_change)
        super().display_info()
