Base plugins directory: `~/.var/app/com.core447.StreamController/data/plugins`

You'll need to allow flatpak access to the host for StreamController for this plugin to talk to pactrl

```
flatpak override --user --talk-name=org.freedesktop.Flatpak com.core447.StreamController
```