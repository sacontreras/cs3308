from unit4.indexer import LocalFileInvertedIndexer
import os
from unit4.indexer_storage import SQLiteInvertedIndexStorage

"""
==========================================================================================
    >>> main

    This section is the 'main' or starting point of the indexer program. The python interpreter will find this 'main' routine and execute it first.
==========================================================================================

"""

if __name__ == '__main__':
    LocalFileInvertedIndexer(storage=SQLiteInvertedIndexStorage(root_dir="./unit4")).reindex_directory(dirname=os.getcwd()+"/unit4/cacm",verbose=False)