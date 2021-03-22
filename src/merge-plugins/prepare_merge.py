import typing
from collections import defaultdict
from typing import List, Dict, Set, Tuple
import os
import json

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
        self.layoutChanged.emit()

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

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        qDebug("Removes!!!!")

        if 0 <= row <= len(self._data) - count:
            del self._data[row:row + count]
            self.layoutChanged.emit()
            return True

        return False

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        default_flags = super().flags(index)

        if index.isValid():
            return default_flags | Qt.ItemIsDragEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled

    def mimeData(self, indexes: typing.Iterable[QModelIndex]) -> QtCore.QMimeData:
        mime_data = QtCore.QMimeData()
        data = []
        for i in indexes:
            if i.column() == 0:
                data.append(self._data[i.row()])
        data_json = json.dumps(data)
        mime_data.setData("application/json", data_json.encode())
        return mime_data

    def mimeTypes(self) -> typing.List[str]:
        return ["application/json"]

    def dropMimeData(self, data: QtCore.QMimeData, action: Qt.DropAction, row: int, column: int,
                     parent: QModelIndex) -> bool:
        if action == Qt.IgnoreAction:
            return True

        if not data.hasFormat("application/json"):
            return False

        if column > 0:
            return False

        if row != -1:
            begin_row = row
        elif parent.isValid():
            begin_row = parent.row()
        else:
            begin_row = len(self._data)

        data_json = data.data("application/json").data().decode()
        new_data = json.loads(data_json)

        for d in new_data:
            self._data.insert(begin_row, d)
            begin_row += 1

        self.layoutChanged.emit()

        return True


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

        self.update_table_view()

    def create_list_widget(self):
        selected_plugins = QtWidgets.QListView()
        selected_plugins.setModel(self._list_model)
        selected_plugins.setModelColumn(1)

        selected_plugins.setDragEnabled(True)
        # selected_plugins.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        selected_plugins.setAcceptDrops(True)
        selected_plugins.setDropIndicatorShown(True)
        # selected_plugins.setDefaultDropAction(QtCore.Qt.MoveAction)
        selected_plugins.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

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

        table.setDragEnabled(True)
        # table.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        # table.setDefaultDropAction(QtCore.Qt.MoveAction)
        table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        table.setDropIndicatorShown(True)
        table.setAcceptDrops(True)

        # table.setContextMenuPolicy(Qt.CustomContextMenu)
        # table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # table.customContextMenuRequested.connect(self.openProfileMenu)

        return table

    def create_button_layout(self):
        button_layout = QtWidgets.QHBoxLayout()

        select_button = QtWidgets.QPushButton(self.__tr("&Select active profile as base"), self)
        select_button.clicked.connect(self.select_current_profile)
        button_layout.addWidget(select_button)

        merge_button = QtWidgets.QPushButton(self.__tr("&Prepare merge in active profile"), self)
        merge_button.clicked.connect(self.activate_plugins)
        button_layout.addWidget(merge_button)

        close_button = QtWidgets.QPushButton(self.__tr("&Close window"), self)
        close_button.clicked.connect(self.close)
        button_layout.addWidget(close_button)

        return button_layout

    def update_table_view(self):
        self._table_model.init_data(self._settings.plugin_mapping)
        self._list_model.init_data([])

        self._table_widget.sortByColumn(0, Qt.AscendingOrder)
        self._table_widget.resizeColumnToContents(1)
        self._table_widget.resizeColumnToContents(3)

    def select_current_profile(self):
        self._settings.selected_main_profile = self.__organizer.profile().name()
        self._settings.plugin_mapping.clear()
        self._settings.plugin_mapping.extend(self.create_plugin_mapping())
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

    def activate_plugins(self):
        modlist = self.__organizer.modList()
        pluginlist = self.__organizer.pluginList()

        plugins = [self._list_model.data(self._list_model.index(i, 1), Qt.DisplayRole)
                   for i in range(self._list_model.rowCount())]
        plugin_to_mod = dict()

        for _, p, _, m in self._settings.plugin_mapping:
            plugin_to_mod[p] = m

        # Disable all mods
        modlist.setActive(modlist.allMods(), active=False)

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
