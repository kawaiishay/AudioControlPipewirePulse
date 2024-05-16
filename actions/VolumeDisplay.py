import pulsectl

from data.plugins.AudioControl.actions.DeviceBase import DeviceBase


class VolumeDisplay(DeviceBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.plugin_base.connect_to_event(event_id="com_gapls_AudioControl::PulseEvent",
                                          callback=self.on_pulse_device_change)

    async def on_pulse_device_change(self, *args, **kwargs):
        if len(args) < 2:
            return

        event = args[1]

        if event.index == self.device_index:
            with pulsectl.Pulse("mute-event") as pulse:
                try:
                    device = self.get_device(self.pulse_filter)
                    self.display_info()
                except:
                    self.show_error(1)

    def display_info(self):
        volumes = self.get_volumes_from_device()
        if len(volumes) > 0:
            self.info = str(int(volumes[0]))
        super().display_info()
