import typing
from typing import List, Dict, Tuple
import json
from collections import defaultdict

import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QModelIndex


class PrepareMergeTableModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []
    _selected: Dict[int, bool] = defaultdict(lambda: False)
    _header = ("Priority\n(Plugin)", "Plugin Name", "Priority\n(Mod)", "Mod Name")
    _alignments = (Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter, Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter)

    def init_data(self, data):
        self._data = data
        self._selected.clear()
        self.layoutChanged.emit()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._header[section]

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 4

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.TextAlignmentRole:
            return self._alignments[index.column()]

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def supportedDragActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        default_flags = super().flags(index)

        if index.isValid():
            if not self.isSelected(index):
                return default_flags | Qt.ItemIsDragEnabled
            else:
                return default_flags ^ Qt.ItemIsEnabled

        return default_flags | Qt.ItemIsDropEnabled

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if value:  # We don't support writing values
            return False

        # Else: None-Value
        # This happens when we move rows to the right
        if index.column() > 0:
            return False

        row = index.row()
        self._selected[self._data[row][0]] = True

        self.dataChanged.emit(self.index(row, 0), self.index(row, 4))

        return True

    def isSelected(self, index: QModelIndex):
        return self._selected[self._data[index.row()][0]]

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

        data_json = data.data("application/json").data().decode()
        new_data = json.loads(data_json)

        if len(new_data) == 0 or len(new_data[0]) != 4:
            return False

        for d in new_data:
            self._selected[d[0]] = False

        self.dataChanged.emit(self.index(0, 0), self.index(len(self._data), len(self._data)))

        return True
