import json
from json import JSONDecodeError
from pathlib import Path
from typing import Tuple

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
import mobase
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from .case_insensitive_dict import CaseInsensitiveDict
from .multi_filter_proxy_model import MultiFilterProxyModel, MultiFilterMode
from .prepare_merge_impl import (
    activate_plugins_impl,
    create_plugin_mapping_impl,
    PluginMapping,
    PrepareMergeException,
)
from .prepare_merge_list_model import PrepareMergeListModel
from .prepare_merge_table_model import PrepareMergeTableModel


class PrepareMergeSettings:
    plugin_mapping: PluginMapping
    selected_main_profile: str
    version: Tuple[int, int, int]

    def __init__(
        self, plugin_mapping=None, selected_main_profile="", version=(1, 1, 0)
    ):
        if plugin_mapping is None:
            plugin_mapping = list()
        self.plugin_mapping = plugin_mapping
        self.selected_main_profile = selected_main_profile
        self.version = version

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def from_json(self, data_json: str):
        try:
            data = json.loads(
                data_json, object_hook=lambda o: PrepareMergeSettings(**o)
            )
            # version check to allow changes of the data structure in the future
            if tuple(data.version) == self.version:
                for x in data.plugin_mapping:
                    if len(x) == 4:
                        self.plugin_mapping.append(tuple(x))
                self.selected_main_profile = str(data.selected_main_profile)
        except JSONDecodeError:
            pass


class PrepareMergeWindow(QtWidgets.QDialog):
    def __tr(self, name: str):
        return QApplication.translate("PrepareMerge", name)

    def __init__(self, organizer: mobase.IOrganizer, parent=None):
        self.__organizer = organizer
        self._settings = PrepareMergeSettings()
        self.load_settings()

        super().__init__(parent)

        self._table_model = PrepareMergeTableModel()
        self._list_model = PrepareMergeListModel()

        self._table_model_proxy = MultiFilterProxyModel()
        self._table_model_proxy.setMultiFilterMode(MultiFilterMode.OR)
        self._table_model_proxy.setSourceModel(self._table_model)
        self._table_model_proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self._table_model_proxy.setSortCaseSensitivity(Qt.CaseInsensitive)

        self.resize(1280, 720)
        self.setWindowIcon(QtGui.QIcon())
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Vertical Layout
        vertical_layout = QtWidgets.QVBoxLayout()
        horizontal_split = QtWidgets.QSplitter()

        self._table_widget = self.create_table_widget()

        active_profile_layout = QtWidgets.QHBoxLayout()
        active_profile_label = QtWidgets.QLabel()
        active_profile_label.setText(self.__tr("Base profile"))
        self._active_profile = QtWidgets.QLineEdit()
        self._active_profile.setReadOnly(True)
        self._active_profile.setFrame(False)
        self._active_profile.setPlaceholderText(self.__tr("No base profile selected"))
        self._active_profile.setText(self._settings.selected_main_profile)
        active_profile_label.setFixedHeight(20)  # same height as _active_profile
        active_profile_layout.addWidget(active_profile_label)
        active_profile_layout.addWidget(self._active_profile)

        filter_box = QtWidgets.QLineEdit()
        filter_box.setClearButtonEnabled(True)
        filter_box.setPlaceholderText(self.__tr("Filter"))

        def update_filter():
            self._table_model_proxy.setFilterByColumn(1, filter_box.text())
            self._table_model_proxy.setFilterByColumn(3, filter_box.text())

        filter_box.textChanged.connect(update_filter)

        wrapper_left = QtWidgets.QWidget()
        layout_left = QtWidgets.QVBoxLayout()
        layout_left.addLayout(active_profile_layout)
        layout_left.addWidget(self._table_widget)
        layout_left.addWidget(filter_box)
        wrapper_left.setLayout(layout_left)

        selected_plugins_label = QtWidgets.QLabel()
        selected_plugins_label.setText(
            self.__tr("Drag and drop the plugins to merge here:")
        )

        wrapper_right = QtWidgets.QWidget()
        layout_right = QtWidgets.QVBoxLayout()
        layout_right.addWidget(selected_plugins_label)
        layout_right.addWidget(self.create_list_widget())
        layout_right.addWidget(self.create_import_button())
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

        self.update_mapping(self.__organizer.profile().name())
        self.update_table_view()

    def create_list_widget(self):
        selected_plugins = QtWidgets.QTreeView()
        selected_plugins.setModel(self._list_model)
        selected_plugins.setColumnHidden(0, True)
        selected_plugins.setColumnHidden(2, True)
        selected_plugins.setColumnHidden(3, True)
        selected_plugins.setRootIsDecorated(True)

        selected_plugins.setDragEnabled(True)
        selected_plugins.setAcceptDrops(True)
        selected_plugins.setDropIndicatorShown(True)
        selected_plugins.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        selected_plugins.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        return selected_plugins

    def create_table_widget(self):
        table = QtWidgets.QTableView()
        table.setModel(self._table_model_proxy)

        table.verticalHeader().setVisible(False)
        table.setSortingEnabled(True)
        table_header = table.horizontalHeader()
        table_header.setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )  # Priority plugin
        table_header.setSectionResizeMode(
            2, QtWidgets.QHeaderView.ResizeToContents
        )  # Priority mod
        table_header.setCascadingSectionResizes(True)
        table_header.setStretchLastSection(True)

        table.setAlternatingRowColors(True)
        table.setShowGrid(False)
        table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)

        table.setDragEnabled(True)
        table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        table.setDropIndicatorShown(False)
        table.setAcceptDrops(True)

        return table

    def create_button_layout(self):
        button_layout = QtWidgets.QHBoxLayout()

        select_button = QtWidgets.QPushButton(
            self.__tr("&Load active profile as base"), self
        )
        select_button.clicked.connect(self.select_current_profile)
        button_layout.addWidget(select_button)

        merge_button = QtWidgets.QPushButton(
            self.__tr("&Prepare merge in active profile"), self
        )
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

    def update_mapping(self, current_profile: str):
        if self._settings.selected_main_profile == current_profile:
            self._settings.plugin_mapping.clear()
            self._settings.plugin_mapping.extend(
                create_plugin_mapping_impl(self.__organizer)
            )
            self._active_profile.setText(self._settings.selected_main_profile)
            self.store_settings()

    def select_current_profile(self):
        self._settings.selected_main_profile = self.__organizer.profile().name()
        self.store_settings()

        self.update_mapping(self.__organizer.profile().name())
        self.update_table_view()

        def profile_changed(old: mobase.IProfile, _: mobase.IProfile) -> None:
            self.update_mapping(old.name())

        self.__organizer.onProfileChanged(profile_changed)

    def show_activate_plugins(self):
        confirmation_box = QtWidgets.QMessageBox()
        confirmation_box.setWindowTitle(self.__tr("Prepare Merge"))
        confirmation_box.setText(self.__tr("Are you sure you want to continue?"))
        confirmation_box.setInformativeText(
            self.__tr(
                "Continuing will disable all mods in the current profile and load only the mods containing the"
                " selected plugins and their masters."
            )
        )
        confirmation_box.setStandardButtons(
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        value = confirmation_box.exec_()
        if value == QtWidgets.QMessageBox.Yes:
            self.activate_plugins()

    def activate_plugins(self):
        plugins = [
            self._list_model.data(self._list_model.index(i, 1), Qt.DisplayRole)
            for i in range(self._list_model.rowCount())
        ]
        plugin_to_mod = CaseInsensitiveDict()

        for _, p, _, m in self._settings.plugin_mapping:
            plugin_to_mod[p] = m

        try:
            activate_plugins_impl(self.__organizer, plugins, plugin_to_mod)
        except PrepareMergeException as ex:
            self.show_error(
                f"The plugin '{ex.plugin}' is missing in your base profile.\n\n"
                f"Check if you already have missing master warnings.",
                "Something went wrong!"
            )

    def show_error(self, message, header):
        exception_box = QtWidgets.QMessageBox()
        exception_box.setWindowTitle(self.__tr("Prepare Merge"))
        exception_box.setText(self.__tr(header))
        exception_box.setIcon(QtWidgets.QMessageBox.Warning)
        exception_box.setInformativeText(self.__tr(message))
        exception_box.setStandardButtons(QtWidgets.QMessageBox.Ok)
        exception_box.exec_()

    def load_settings(self):
        plugin_data = Path(self.__organizer.getPluginDataPath())
        settings_path = plugin_data / "merge-plugins" / "prepare_merge.settings"
        if settings_path.exists():
            settings_file = settings_path.read_text()
            self._settings.from_json(settings_file)

    def store_settings(self):
        plugin_data = Path(self.__organizer.getPluginDataPath())
        settings_path = plugin_data / "merge-plugins"
        settings_path.mkdir(parents=True, exist_ok=True)
        settings_path /= "prepare_merge.settings"
        settings_file = self._settings.to_json()
        settings_path.write_text(settings_file)

    def create_import_button(self):
        import_button = QtWidgets.QPushButton(
            self.__tr("&Import entries from clipboard"), self
        )
        import_button.clicked.connect(self.import_list)
        return import_button

    def import_list(self):
        clipboard = QtGui.QGuiApplication.clipboard()
        text = clipboard.text().split("\n")

        valid_entries = []
        invalid_entries = []
        for e in text:
            e_cleaned = e.strip()
            if len(e_cleaned) == 0:
                continue
            s, d = self._table_model.selectEntry(e_cleaned, 1)
            if s and d:
                valid_entries.append(d)
            elif s:
                QtCore.qInfo(f"Plugin already selected: '{e_cleaned}'")
            else:
                QtCore.qWarning(f"Plugin does not exist: '{e_cleaned}'")
                invalid_entries.append(e_cleaned)

        if len(invalid_entries) > 0:
            self.show_error(f"The following plugins do not exist:\n{invalid_entries}", "Import failed!")

        self._list_model.insertEntries(self._list_model.rowCount(), valid_entries)
