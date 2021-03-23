import typing
from typing import List, Dict, Set, Tuple
import json

import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QModelIndex, qDebug


class PrepareMergeTableModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []
    _header = ("Priority\n(Plugin)", "Plugin Name", "Priority\n(Mod)", "Mod Name")
    _alignments = (Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter, Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter)

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
        elif role == Qt.ToolTipRole:
            return f"{self._data[index.row()][3]}"

    def moveRows(self, sourceParent: QModelIndex, sourceRow: int, count: int, destinationParent: QModelIndex,
                 destinationChild: int) -> bool:
        first = sourceRow
        last = sourceRow + count - 1
        target = destinationChild

        # Already in place, calling beginMoveRows results in crash if we don't handle this case
        if target - count == first:
            return True

        self.beginMoveRows(sourceParent, first, last, destinationParent, destinationChild)

        # Moving elements downwards and upwards needs a different offset
        offset = 1 if target > first else 0

        # Remove elements from start index
        tmp = []
        for _ in range(count):
            tmp.append(self._data.pop(sourceRow))

        # Reverse order because we are inserting before index each time
        tmp.reverse()
        for item in tmp:
            self._data.insert(target - offset, item)

        self.endMoveRows()

        return True

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return 4

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self._data)

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

        if column > 0:  # Always move whole rows
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