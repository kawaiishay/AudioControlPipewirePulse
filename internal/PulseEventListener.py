import threading

import pulsectl
from src.backend.PluginManager.EventHolder import EventHolder


class PulseEvent(EventHolder):
    def __init__(self, plugin_base: "PluginBase", event_id: str, *masks):
        super().__init__(plugin_base=plugin_base, event_id=event_id)
        self.pulse_sink_thread = threading.Thread(target=self._start_loop)
        self.pulse_sink_thread.daemon = True
        self.pulse_sink_thread.start()

        self.masks = masks

    def _start_loop(self):
        self._loop()

    def _loop(self):
        with pulsectl.Pulse("pulse-sink-event-loop") as pulse:
            pulse.event_mask_set(*self.masks)
            pulse.event_callback_set(lambda event: self.trigger_event(event))
            while True:
                pulse.event_listen()