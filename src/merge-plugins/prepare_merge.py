from typing import List
import os

import mobase

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import PyQt5.QtCore as QtCore

from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import Qt

from PyQt5.QtCore import qDebug, qCritical, qWarning, qInfo


# from PyQt5.QtCore import QCoreApplication

class PrepareMergeException(Exception):
    pass


class PrepareMergeWindow(QtWidgets.QDialog):
    def __tr(self, name: str):
        return QApplication.translate("PrepareMergeWindow", name)

    def __init__(self, organizer, parent=None):
        self.__modListInfo = {}
        self.__profilesInfo = {}
        self.__organizer = organizer

        super().__init__(parent)

        self.resize(500, 500)
        self.setWindowIcon(QtGui.QIcon())  # TODO: Add icon
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Vertical Layout
        verticalLayout = QtWidgets.QVBoxLayout()

        # Vertical Layout -> Merged Mod List (TODO: Better to use QTreeView and model?)
        self.profileList = QtWidgets.QTreeWidget()

        self.profileList.setColumnCount(1)
        self.profileList.setRootIsDecorated(False)

        self.profileList.header().setVisible(True)
        self.profileList.headerItem().setText(0, self.__tr("Profile name"))

        # self.profileList.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.profileList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # self.profileList.customContextMenuRequested.connect(self.openProfileMenu)

        # verticalLayout.addWidget(self.profileList)

        # Vertical Layout -> Button Layout
        # buttonLayout = QtWidgets.QHBoxLayout()

        # Vertical Layout -> Button Layout -> Refresh Button
        # refreshButton = QtWidgets.QPushButton(self.__tr("&Refresh"), self)
        # refreshButton.setIcon(QtGui.QIcon(":/MO/gui/refresh"))
        # refreshButton.clicked.connect(self.refreshProfileList)
        # buttonLayout.addWidget(refreshButton)

        # Vertical Layout -> Button Layout -> Close Button
        # closeButton = QtWidgets.QPushButton(self.__tr("&Close"), self)
        # closeButton.clicked.connect(self.close)
        # buttonLayout.addWidget(closeButton)

        # verticalLayout.addLayout(buttonLayout)

        # Vertical Layout
        # self.setLayout(verticalLayout)

        # Build lookup dictionary of all profiles
        # self.__profileInfo = self.getProfileInfo()

        # Build lookup dictionary of mods in current profile
        # self.__modListInfo = self.getModListInfoByPath(
        #    os.path.join(self.__organizer.profilePath(), "modlist.txt")
        # )


class PrepareMerge(mobase.IPluginTool):
    NAME = "Prepare Merge"
    DESCRIPTION = "TODO"

    __organizer: mobase.IOrganizer

    def __tr(self, txt: str):
        return QApplication.translate("PrepareMerge", txt)

    def __init__(self):
        super().__init__()
        self.__window = None
        self.__organizer = None
        self.__parentWidget = None

    def init(self, organizer: mobase.IOrganizer):
        self.__organizer = organizer
        return True

    def display(self):
        # self.__window = PrepareMergeWindow(self.__organizer)
        # self.__window.setWindowTitle(self.NAME)
        # self.__window.exec_()

        # Refresh Mod Organizer mod list to reflect changes
        # current_profile = None
        modlist = self.__organizer.modList()
        pluginlist = self.__organizer.pluginList()
        # mods = [
        #    modlist.getMod(m) for m in modlist.allModsByProfilePriority(current_profile)
        # ]
        # mods = [m for m in mods if not m.isSeparator() and not m.isForeign()]

        # plugin_to_mod = dict()
        # for plugin in pluginlist.pluginNames():
        #    mod = pluginlist.origin(plugin)
        #    plugin_to_mod[plugin] = mod

        # qDebug(str(plugin_to_mod))
        plugin_to_mod = {
            'Andromeda - Unique Standing Stones of Skyrim.esp': 'Andromeda - Unique Standing Stones of Skyrim',
            'Apocalypse - Magic of Skyrim.esp': 'Apocalypse - Magic of Skyrim',
            'Complete Crafting Overhaul_Remastered.esp': 'Complete Crafting Overhaul Remastered',
            'Dawnguard.esm': 'DLC: Dawnguard', 'Dragonborn.esm': 'DLC: Dragonborn',
            'HearthFires.esm': 'DLC: HearthFires', 'Skyrim.esm': 'data',
            'SL01AmuletsSkyrim.esp': 'Amulets of Skyrim SSE',
            'SL01AmuletsSkyrim_CCOR_Patch.esp': 'Amulets of Skyrim __ CCOR',
            'Unofficial Skyrim Special Edition Patch.esp': 'Unofficial Skyrim Special Edition Patch',
            'Update.esm': 'data',
            'Weapons Armor Clothing & Clutter Fixes.esp': 'Weapons Armor Clothing and Clutter Fixes'}

        # raise PrepareMergeException("Error")
        main_profile = self.__organizer.profile()
        plugins = ["SL01AmuletsSkyrim_CCOR_Patch.esp", "Apocalypse - Magic of Skyrim.esp"]

        # def find_by_plugin(plugin: str) -> str:
        #    origins = self.__organizer.getFileOrigins(plugin)
        #    if len(origins) > 1:
        #        qWarning(f"{self.name()} - Found more than one copy of the plugin: {plugin}")
        #    elif len(origins) == 0:
        #        raise PrepareMergeException(f"Plugin does not exist: {plugin}")
        #
        #    return origins[0]  # Return mod with highest priority

        # mods: List[str] = [find_by_plugin(p) for p in plugins]
        mods = [plugin_to_mod[p] for p in plugins]

        # Disable all mods
        modlist.setActive(modlist.allMods(), active=False)

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
        mandatory_plugins = [p for p in pluginlist.pluginNames() if pluginlist.state(p) == mobase.PluginState.ACTIVE]

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
                additional_mods = set([plugin_to_mod[p] for p in plugins_and_masters_to_check])
                qInfo(f"Enabling {additional_mods} containing missing masters {plugins_and_masters_to_check}")
                modlist.setActive(list(additional_mods), active=True)

        # Enable only target plugins and their masters
        # Not other plugins inside the same mod
        enable_plugins(plugins_and_masters)

        # Place plugins at end of load order
        max_priority = len(pluginlist.pluginNames()) - 1
        for p in plugins:
            pluginlist.setPriority(p, max_priority)

    def displayName(self):
        return self.__tr(self.NAME)

    def icon(self):
        return QtGui.QIcon()  # TODO: Add icon

    def tooltip(self):
        return self.__tr(self.DESCRIPTION)

    # IPlugin

    def author(self) -> str:
        return "ssauermann"

    def name(self) -> str:
        return self.NAME

    def localizedName(self) -> str:
        return self.__tr(self.NAME)

    def description(self) -> str:
        return self.__tr(self.DESCRIPTION)

    def version(self) -> mobase.VersionInfo:
        return mobase.VersionInfo(1, 0, 0, mobase.ReleaseType.FINAL)

    def isActive(self) -> bool:
        return self.__organizer.pluginSetting(self.name(), "enabled")

    def settings(self) -> List[mobase.PluginSetting]:
        return [mobase.PluginSetting("enabled", self.__tr("Enable this plugin"), True)]
