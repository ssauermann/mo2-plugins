import typing
from typing import List, Dict, Set, Tuple
import json
from collections import defaultdict

import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt, QModelIndex, qDebug


class PrepareMergeTableModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []
    _selected: Dict[int, bool] = defaultdict(lambda: False)
    _header = ("Priority\n(Plugin)", "Plugin Name", "Priority\n(Mod)", "Mod Name")
    _alignments = (Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter, Qt.AlignCenter, Qt.AlignLeft | Qt.AlignVCenter)

    def __init__(self):
        super().__init__()

    def init_data(self, data):
        self._data = data
        self._selected.clear()
        self.layoutChanged.emit()

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._header[section]

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
        elif role == Qt.TextAlignmentRole:
            return self._alignments[index.column()]

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        if value:  # We don't support writing values
            return False

        # Else: None-Value
        # This happens when we move rows to the right
        if index.column() > 0:
            return False

        row = index.row()
        self._selected[self._data[row][0]] = True
        # qDebug(f"set data: {value} {str(self._data)}")

        self.dataChanged.emit(self.index(row, 0), self.index(row, 4))

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
            if not self.isSelected(index):
                return default_flags | Qt.ItemIsDragEnabled
            else:
                return default_flags ^ Qt.ItemIsEnabled
        else:
            return default_flags | Qt.ItemIsDropEnabled

        return default_flags

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

        # TODO: More precise index?
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._data), 4))

        return True


class PrepareMergeListModel(QtCore.QAbstractTableModel):
    _data: List[Tuple[int, str, int, str]] = []

    def __init__(self):
        super().__init__()

    def init_data(self, data):
        self._data = data
        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: int = ...) -> typing.Any:
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]
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

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        qDebug(f"Foo {row} {count}")
        #   if 0 <= row + count <= len(self._data):
        #      #self.beginRemoveRows(parent, row, row + count - 1)
        #     for _ in range(count):
        #        pass
        #       #self._data.pop(row)
        #  #self.endRemoveRows()
        # return True

        return False

    def setData(self, index: QModelIndex, value: typing.Any, role: int = ...) -> bool:
        qDebug(f"set data list: ")  # {value} {str(self._data)}")

        # if value:  # We don't support writing values
        return False

        # Else: None-Value
        # This happens when we move rows to the left
        # qDebug(f"set data: {value} {index.row()} {str(self._data)}")
        # self.removeRows(index.row(), 1)

        self.dataChanged.emit(index, index)

        # return True

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

        return default_flags

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

        if len(new_data) == 0 or len(new_data[0]) != 4:
            return False

        for d in new_data:
            self._data.insert(begin_row, d)
            begin_row += 1

        # TODO: More precise index?
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._data), 4))

        return True
