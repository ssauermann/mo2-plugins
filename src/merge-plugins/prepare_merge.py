import typing
from collections import defaultdict
from typing import List, Dict, Set, Tuple
import os

import mobase

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import PyQt5.QtCore as QtCore

from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import Qt, QModelIndex

from PyQt5.QtCore import qDebug, qCritical, qWarning, qInfo


# from PyQt5.QtCore import QCoreApplication

class PrepareMergeException(Exception):
    pass


class PrepareMergeSettings:
    plugin_mapping: List[Tuple[int, str, int, str]] = []
    selected_main_profile: str = ""


class PrepareMergeTableModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []
    _header = ("Priority\n(Plugin)", "Plugin Name", "Priority\n(Mod)", "Mod Name")
    _alignments = (Qt.AlignCenter, Qt.AlignLeft, Qt.AlignCenter, Qt.AlignLeft)

    def __init__(self):
        super().__init__()

    def init_data(self, data):
        self._data = data

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._header[section]

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.TextAlignmentRole:
            return self._alignments[index.column()]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 4

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)


class PrepareMergeWindow(QtWidgets.QDialog):
    def __tr(self, name: str):
        return QApplication.translate("PrepareMergeWindow", name)

    def __init__(self, organizer: mobase.IOrganizer, settings: PrepareMergeSettings, parent=None):
        self.__organizer = organizer
        self._settings = settings

        super().__init__(parent)

        self._table_model = PrepareMergeTableModel()
        self._list_model = PrepareMergeTableModel()

        self._table_model_proxy = QtCore.QSortFilterProxyModel()
        self._table_model_proxy.setSourceModel(self._table_model)

        # self._table_model_proxy.setFilterKeyColumn(3)
        # self._table_model_proxy.setFilterFixedString("dog")
        # self._table_model_proxy.setFilterWildcard("do")
        # self._table_model_proxy.setFilterRegExp(QRegExp("do.*"))

        self.resize(800, 500)
        self.setWindowIcon(QtGui.QIcon())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Vertical Layout
        vertical_layout = QtWidgets.QVBoxLayout()
        horizontal_split = QtWidgets.QSplitter()

        self._table_widget = self.create_table_widget()
        horizontal_split.addWidget(self._table_widget)
        horizontal_split.addWidget(self.create_list_widget())

        vertical_layout.addWidget(horizontal_split)
        vertical_layout.addLayout(self.create_button_layout())

        # Vertical Layout
        self.setLayout(vertical_layout)

        # Resize splitter to 2:1 ratio
        split_width = horizontal_split.width()
        left_width = int(2 * split_width / 3)
        right_width = split_width - left_width
        horizontal_split.setSizes((left_width, right_width))

        # Build lookup dictionary of all profiles
        # self.__profileInfo = self.getProfileInfo()

        # Build lookup dictionary of mods in current profile
        # self.__modListInfo = self.getModListInfoByPath(
        #    os.path.join(self.__organizer.profilePath(), "modlist.txt")
        # )

    def create_list_widget(self):
        selected_plugins = QtWidgets.QListView()
        selected_plugins.setModel(self._list_model)
        selected_plugins.setModelColumn(3)

        selected_plugins.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        selected_plugins.setAcceptDrops(True)

        return selected_plugins

    def create_table_widget(self):
        # Vertical Layout -> Reference Plugin List
        table = QtWidgets.QTableView()
        table.setModel(self._table_model_proxy)

        # self.profileList.setColumnCount(4)
        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table_header = table.horizontalHeader()
        table_header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # Priority plugin
        # table_header.setSectionResizeMode(1, QtWidgets.QHeaderView.Interactive) # Plugin name
        table_header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)  # Priority mod
        # table_header.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)  # Mod name
        table_header.setCascadingSectionResizes(True)
        table_header.setStretchLastSection(True)

        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        table.setDragDropMode(QtWidgets.QAbstractItemView.DragOnly)

        # table.setContextMenuPolicy(Qt.CustomContextMenu)
        # table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # table.customContextMenuRequested.connect(self.openProfileMenu)

        return table

    def create_button_layout(self):
        button_layout = QtWidgets.QHBoxLayout()

        select_button = QtWidgets.QPushButton(self.__tr("&Select active profile as base"), self)
        select_button.clicked.connect(self.select_current_profile)
        button_layout.addWidget(select_button)

        close_button = QtWidgets.QPushButton(self.__tr("&Close"), self)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        return button_layout

    def update_table_view(self):
        self._table_model.init_data(self._settings.plugin_mapping)
        self._table_model.layoutChanged.emit()

        self._table_widget.sortByColumn(0, Qt.AscendingOrder)
        self._table_widget.resizeColumnToContents(1)
        self._table_widget.resizeColumnToContents(3)

    def select_current_profile(self):
        self._settings.selected_main_profile = self.__organizer.profile()
        self._settings.plugin_mapping = self.create_plugin_mapping()
        self.update_table_view()

    def create_plugin_mapping(self):
        pluginlist = self.__organizer.pluginList()
        modlist = self.__organizer.modList()

        data: List[Tuple[int, str, int, str]] = []

        for plugin in pluginlist.pluginNames():
            mod = pluginlist.origin(plugin)
            priority = pluginlist.priority(plugin)
            priority_mod = modlist.priority(mod)
            data.append((priority, plugin, priority_mod, mod))

        return data


class PrepareMerge(mobase.IPluginTool):
    NAME = "Prepare Merge"
    DESCRIPTION = "TODO"

    __organizer: mobase.IOrganizer
    _settings: PrepareMergeSettings

    def __tr(self, txt: str):
        return QApplication.translate("PrepareMerge", txt)

    def __init__(self):
        super().__init__()
        self.__window = None
        self.__organizer = None
        self.__parentWidget = None
        self._settings = PrepareMergeSettings()

    def init(self, organizer: mobase.IOrganizer):
        self.__organizer = organizer
        return True

    def display(self):
        self.__window = PrepareMergeWindow(self.__organizer, self._settings)
        self.__window.setWindowTitle(self.NAME)
        self.__window.exec_()

        # Refresh Mod Organizer mod list to reflect changes
        # current_profile = None

        modlist = self.__organizer.modList()
        pluginlist = self.__organizer.pluginList()
        # mods = [
        #    modlist.getMod(m) for m in modlist.allModsByProfilePriority(current_profile)
        # ]
        # mods = [m for m in mods if not m.isSeparator() and not m.isForeign()]

        # modlist.allModsByProfilePriority()

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
