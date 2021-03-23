import json
import typing
from typing import List, Set, Tuple

import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QModelIndex


class PrepareMergeListModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []
    _indices_to_remove: Set[int] = set()
    _header = ("", "Selected Plugins", "", "")

    def init_data(self, data):
        self._data = data
        self._indices_to_remove.clear()
        self.layoutChanged.emit()

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...
    ) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._header[section]

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.ToolTipRole:
            return f"{self._data[index.row()][3]}"

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        self.beginRemoveRows(QModelIndex(), row, row + count - 1)
        for _ in range(count):
            del self._data[row]
        self.endRemoveRows()
        return True

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 4

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)

    def supportedDropActions(self) -> Qt.DropActions:
        return Qt.MoveAction

    def supportedDragActions(self) -> Qt.DropActions:
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
            data.append(self._data[i.row()])
        data_json = json.dumps(data)
        mime_data.setData("application/json", data_json.encode())
        return mime_data

    def mimeTypes(self) -> typing.List[str]:
        return ["application/json"]

    def dropMimeData(
        self,
        data: QtCore.QMimeData,
        action: Qt.DropAction,
        row: int,
        column: int,
        parent: QModelIndex,
    ) -> bool:

        if action == Qt.IgnoreAction:
            return True

        if not data.hasFormat("application/json"):
            return False

        if row != -1:
            begin_row = row
        elif parent.isValid():
            begin_row = parent.row()
        else:
            begin_row = len(self._data)

        data_json = data.data("application/json").data().decode()
        new_data = json.loads(data_json)

        if len(new_data) == 0 or len(new_data[0]) != 4:
            return False

        self.beginInsertRows(QModelIndex(), begin_row, begin_row + len(new_data) - 1)
        for d in new_data:
            self._data.insert(begin_row, d)
            begin_row += 1
        self.endInsertRows()

        return True
