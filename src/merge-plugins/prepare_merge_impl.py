from typing import List, Dict, Tuple

import mobase
try:
    from PyQt6.QtCore import qInfo
except ImportError:
    from PyQt5.QtCore import qInfo

PluginMapping = List[Tuple[int, str, int, str]]


class PrepareMergeException(Exception):
    def __init__(self, plugin):
        self.plugin = plugin


def create_plugin_mapping_impl(organizer: mobase.IOrganizer) -> PluginMapping:
    pluginlist = organizer.pluginList()
    modlist = organizer.modList()

    data: PluginMapping = []

    for plugin in pluginlist.pluginNames():
        mod = pluginlist.origin(plugin)
        priority = pluginlist.priority(plugin)
        priority_mod = modlist.priority(mod)
        data.append((priority, plugin, priority_mod, mod))

    return data


def activate_plugins_impl(
    organizer: mobase.IOrganizer, plugins: List[str], plugin_to_mod: Dict[str, str]
):
    modlist = organizer.modList()
    pluginlist = organizer.pluginList()

    # Disable all mods
    modlist.setActive(modlist.allMods(), active=False)

    enabled_plugins = set()
    enabled_mods = set()

    try:

        mods = [plugin_to_mod[p] for p in plugins]
        # Enable mods with selected plugins
        modlist.setActive(mods, active=True)

        # Enable only selected plugins
        def enable_plugins(plugins_to_enable):
            for p in pluginlist.pluginNames():
                if p in plugins_to_enable:
                    pluginlist.setState(p, mobase.PluginState.ACTIVE)
                else:
                    pluginlist.setState(p, mobase.PluginState.INACTIVE)

        # Enable no plugins (except mandatory)
        enable_plugins([])
        mandatory_plugins = [
            p
            for p in pluginlist.pluginNames()
            if pluginlist.state(p) == mobase.PluginState.ACTIVE
        ]

        # Enable missing masters
        plugins_and_masters = set(mandatory_plugins)
        plugins_and_masters_to_check = set(plugins)

        # Checking masters of plugins (and their masters, and so on)
        while len(plugins_and_masters_to_check) > 0:
            plugins_and_masters.update(plugins_and_masters_to_check)

            # Extract all masters of plugins in the current loop
            for p in plugins_and_masters_to_check.copy():
                masters = pluginlist.masters(p)
                plugins_and_masters_to_check.update(masters)

            # Remove all masters that were already checked in a previous loop
            plugins_and_masters_to_check.difference_update(plugins_and_masters)

            # Missing masters found -> enable mods and do another round checking them for masters
            if len(plugins_and_masters_to_check) > 0:
                additional_mods = set(
                    [plugin_to_mod[p] for p in plugins_and_masters_to_check]
                )
                qInfo(
                    f"Enabling {additional_mods} containing missing masters {plugins_and_masters_to_check}".encode(
                        'ascii', 'replace').decode('ascii')
                )
                modlist.setActive(list(additional_mods), active=True)
                enabled_mods.update(additional_mods)

    except KeyError as e:
        raise PrepareMergeException(e.args[0])

    # Enable only target plugins and their masters
    # Not other plugins inside the same mod
    enable_plugins(plugins_and_masters)

    enabled_plugins.update(plugins_and_masters)
    enabled_plugins.difference_update(mandatory_plugins)

    # Place plugins at end of load order
    max_priority = len(pluginlist.pluginNames()) - 1
    for p in plugins:
        pluginlist.setPriority(p, max_priority)

    return list(enabled_plugins), list(enabled_mods)
