from typing import List, Dict, Set, Tuple

import mobase

import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

import PyQt5.QtCore as QtCore

from PyQt5.QtWidgets import QApplication

from PyQt5.QtCore import Qt

from PyQt5.QtCore import qDebug, qCritical, qWarning, qInfo

from .prepare_merge_model import PrepareMergeTableModel


class PrepareMergeSettings:
    plugin_mapping: List[Tuple[int, str, int, str]] = []
    selected_main_profile: str = ""


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
        self._table_model_proxy.setFilterKeyColumn(1)

        self.resize(1280, 720)
        self.setWindowIcon(QtGui.QIcon())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Vertical Layout
        vertical_layout = QtWidgets.QVBoxLayout()
        horizontal_split = QtWidgets.QSplitter()

        self._table_widget = self.create_table_widget()

        active_profile_layout = QtWidgets.QHBoxLayout()
        active_profile_label = QtWidgets.QLabel()
        active_profile_label.setText("Base profile")
        self._active_profile = QtWidgets.QLineEdit()
        self._active_profile.setReadOnly(True)
        self._active_profile.setFrame(False)
        self._active_profile.setPlaceholderText("No base profile selected")
        self._active_profile.setText(self._settings.selected_main_profile)
        active_profile_label.setFixedHeight(20)  # same height as _active_profile
        active_profile_layout.addWidget(active_profile_label)
        active_profile_layout.addWidget(self._active_profile)

        filter_box = QtWidgets.QLineEdit()
        filter_box.setClearButtonEnabled(True)
        filter_box.setPlaceholderText("Filter")
        filter_box.textChanged.connect(lambda: self._table_model_proxy.setFilterWildcard(filter_box.text()))

        wrapper_left = QtWidgets.QWidget()
        layout_left = QtWidgets.QVBoxLayout()
        layout_left.addLayout(active_profile_layout)
        layout_left.addWidget(self._table_widget)
        layout_left.addWidget(filter_box)
        wrapper_left.setLayout(layout_left)

        selected_plugins_label = QtWidgets.QLabel()
        selected_plugins_label.setText("Plugins selected for merge")

        wrapper_right = QtWidgets.QWidget()
        layout_right = QtWidgets.QVBoxLayout()
        layout_right.addWidget(selected_plugins_label)
        layout_right.addWidget(self.create_list_widget())
        wrapper_right.setLayout(layout_right)
        selected_plugins_label.setFixedHeight(20)  # same height as _active_profile

        horizontal_split.addWidget(wrapper_left)
        horizontal_split.addWidget(wrapper_right)

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
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        # table.setDropIndicatorShown(True)
        # table.setAcceptDrops(True)

        # table.setContextMenuPolicy(Qt.CustomContextMenu)
        # table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        # table.customContextMenuRequested.connect(self.openProfileMenu)

        return table

    def create_button_layout(self):
        button_layout = QtWidgets.QHBoxLayout()

        select_button = QtWidgets.QPushButton(self.__tr("&Load active profile as base"), self)
        select_button.clicked.connect(self.select_current_profile)
        button_layout.addWidget(select_button)

        merge_button = QtWidgets.QPushButton(self.__tr("&Prepare merge in active profile"), self)
        merge_button.clicked.connect(self.show_activate_plugins)
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
        self._active_profile.setText(self._settings.selected_main_profile)
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

    def show_activate_plugins(self):
        confirmation_box = QtWidgets.QMessageBox()
        confirmation_box.setWindowTitle("Prepare Merge")
        confirmation_box.setText("Are you sure you want to continue?")
        confirmation_box.setInformativeText(
            "Continuing will disable all mods in the current profile and load only the mods containing the selected plugins and their masters.")
        confirmation_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        value = confirmation_box.exec_()
        if value == QtWidgets.QMessageBox.Yes:
            self.activate_plugins()

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
