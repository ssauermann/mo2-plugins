from typing import List

import mobase

from .prepare_merge import PrepareMerge


def createPlugins() -> List[mobase.IPlugin]:
    return [PrepareMerge()]
