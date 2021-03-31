from typing import List

import PyQt5.QtGui as QtGui
import mobase
from PyQt5.QtWidgets import QApplication

from .prepare_merge_window import PrepareMergeWindow


class PrepareMerge(mobase.IPluginTool):
    NAME = "Prepare Merge"
    DESCRIPTION = "Finds and enables the mods containing a selected list of plugins and their required masters. Then places the selected plugins at the end of the load order."

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
        self.__window = PrepareMergeWindow(self.__organizer)
        self.__window.setWindowTitle(self.NAME)
        self.__window.exec_()

    def displayName(self):
        return self.__tr(self.NAME)

    def icon(self):
        return QtGui.QIcon()

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
