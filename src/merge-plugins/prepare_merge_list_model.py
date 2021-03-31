import json
import typing
from typing import List, Tuple

import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QModelIndex
from PyQt5.QtWidgets import QApplication


class PrepareMergeListModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []
    _header = ("", "Selected Plugins", "", "")

    def init_data(self, data):
        self._data = data
        self.layoutChanged.emit()

    def __tr(self, name: str):
        return QApplication.translate("PrepareMerge", name)

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = ...
    ) -> typing.Any:
        if role == Qt.DisplayRole:
            return self.__tr(self._header[section])

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
        mime_data.setData("application/json/list", data_json.encode())
        return mime_data

    def mimeTypes(self) -> typing.List[str]:
        return ["application/json/table", "application/json/list"]

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

        if not data.hasFormat("application/json/table") and not data.hasFormat("application/json/list"):
            return False

        if row != -1:
            begin_row = row
        elif parent.isValid():
            begin_row = parent.row()
        else:
            begin_row = len(self._data)

        if data.hasFormat("application/json/list"):
            data_json = data.data("application/json/list").data().decode()
        else:
            data_json = data.data("application/json/table").data().decode()
        new_data = json.loads(data_json)

        if len(new_data) == 0 or len(new_data[0]) != 4:
            return False

        self.insertEntries(begin_row, new_data)

        return True

    def insertEntries(self, start, data):
        self.beginInsertRows(QModelIndex(), start, start + len(data) - 1)
        for d in data:
            self._data.insert(start, d)
            start += 1
        self.endInsertRows()
