import mobase

from .prepare_merge import PrepareMerge


def createPlugins() -> mobase.IPlugin:
    return [PrepareMerge()]
