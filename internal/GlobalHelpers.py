import os
import inspect
from src.backend.PluginManager.PluginBase import PluginBase

# Based off https://github.com/StreamController/StreamController

class GlobalHelpers(PluginBase):
    def __init__(self):
        super().__init__(use_legacy_locale=False)
        self.TOP_LEVEL_PATH = os.path.join(os.path.dirname(inspect.getfile(self.__class__)), "..")


def plugin_base_dir() -> str:
    return GlobalHelpers().TOP_LEVEL_PATH

def get_app_component_path(app_component_name: str, subdirs: list[str] = None, top_plugin_sub_folder: str = "internal") -> str:

    global_class = GlobalHelpers()

    if not subdirs:
        return os.path.join(global_class.TOP_LEVEL_PATH, top_plugin_sub_folder, app_component_name)
    subdir = os.path.join(*subdirs)
    if subdir != "":
        return os.path.join(global_class.TOP_LEVEL_PATH, top_plugin_sub_folder, subdir, app_component_name)
    return ""