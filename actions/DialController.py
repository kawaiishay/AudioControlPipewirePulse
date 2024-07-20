import os

from src.backend.PluginManager.ActionBase import ActionBase
from ..actions.DeviceBase import DeviceBase
import pulsectl
from GtkHelper.GtkHelper import ScaleRow


# noinspection PyInterpreter
class DialController(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)
        self.volume_adjust: int = 1
        self.volume_bounds: int = 100

    def on_ready(self):
        super().on_ready()
        self.update_mute_image()

    def get_config_rows(self):
        self.volume_adjust_scale = ScaleRow(title=self.plugin_base.lm.get("action.adjust-volume.volume-adjust"),
                                            value=0,
                                            min=1,
                                            max=50,
                                            step=1,
                                            text_left="1",
                                            text_right="50"
                                            )

        self.volume_adjust_scale.scale.set_draw_value(True)

        self.volume_bound_scale = ScaleRow(title=self.plugin_base.lm.get("action.adjust-volume.volume-bounds"),
                                           value=100,
                                           min=0,
                                           max=150,
                                           step=1,
                                           text_left="0",
                                           text_right="150")
        self.volume_bound_scale.scale.set_draw_value(True)

        base = super().get_config_rows()

        base.append(self.volume_adjust_scale)
        base.append(self.volume_bound_scale)

        return base

    #
    # BASE SETTINGS LOADER
    #

    def load_essential_settings(self):
        settings = self.get_settings()

        self.volume_adjust = settings.get("volume-adjust", 1)
        self.volume_bounds = settings.get("volume-bounds", 100)

        super().load_essential_settings()

    def load_ui_settings(self):
        self.volume_adjust_scale.scale.set_value(self.volume_adjust)
        self.volume_bound_scale.scale.set_value(self.volume_bounds)

        super().load_ui_settings()

    #
    # EVENTS
    #

    def connect_events(self):
        super().connect_events()

        self.volume_adjust_scale.scale.connect("value-changed", self.on_volume_adjust_changed)
        self.volume_bound_scale.scale.connect("value-changed", self.on_volume_bounds_changed)

    def disconnect_events(self):
        super().disconnect_events()

        self.volume_adjust_scale.scale.disconnect_by_func(self.on_volume_adjust_changed)
        self.volume_bound_scale.scale.disconnect_by_func(self.on_volume_bounds_changed)

    def on_volume_adjust_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_adjust = self.volume_adjust_scale.scale.get_value()

        settings["volume-adjust"] = self.volume_adjust
        self.set_settings(settings)

    def on_volume_bounds_changed(self, *args, **kwargs):
        settings = self.get_settings()

        self.volume_bounds = self.volume_bound_scale.scale.get_value()

        settings["volume-bounds"] = self.volume_bounds
        self.set_settings(settings)

    def on_device_changed(self, *args, **kwargs):
        super().on_device_changed(*args, **kwargs)
        self.update_mute_image()

    async def on_pulse_device_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if event.index == self.device_index:
            with pulsectl.Pulse("mute-event") as pulse:
                try:
                    device = self.get_device(self.pulse_filter)
                    self.display_mute_image(device.mute)
                    self.display_info()
                except:
                    self.show_error(1)

    def on_dial_down(self):
        if self.pulse_device_name is None:
            self.show_error(1)
            return

        try:
            device = self.get_device(self.pulse_filter)

            mute_state = 1 if device.mute == 0 else 0

            self.plugin_base.pulse.mute(device, mute_state)
            self.display_mute_image(mute_state)
        except:
            self.show_error(1)

    def on_dial_turn(self, direction: int):
        if self.pulse_device_name is None:
            self.show_error(1)
            return

        try:
            device = self.get_device(self.pulse_filter)

            # Decreasing Volume
            if direction < 0:
                self.plugin_base.pulse.volume_change_all_chans(device, -self.volume_adjust * 0.01)
                return

            volumes = self.get_volumes_from_device()
            if len(volumes) > 0 and volumes[0] < self.volume_bounds:
                if volumes[0] + self.volume_adjust > self.volume_bounds and direction > 0:
                    self.plugin_base.pulse.volume_set_all_chans(device, self.volume_bounds * 0.01)
                else:
                    self.plugin_base.pulse.volume_change_all_chans(device, self.volume_adjust * 0.01)
        except:
            self.show_error(1)

    #
    # MISC
    #

    def display_info(self):
        volumes = self.get_volumes_from_device()
        if len(volumes) > 0:
            self.info = str(int(volumes[0]))
        super().display_info()

    def update_mute_image(self):
        try:
            device = self.get_device(self.pulse_filter)
            self.display_mute_image(device.mute)
        except:
            self.show_error(1)

    def display_mute_image(self, mute_state):
        if mute_state == 1:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "mute.png"))
        else:
            self.set_media(media_path=os.path.join(self.plugin_base.PATH, "assets", "audio.png"))