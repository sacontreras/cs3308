# this file does the "same thing" as the associated Jupyter Notebook (unit4-PA-labreport.ipynb)
#   it is included in order to run the assignment from the command-line instead of as a Jupyter Notebook (in case you don't have Jupyter installed)

from unit4.indexer import LocalFileInvertedIndexer
import os
from unit4.indexer_storage import SQLiteInvertedIndexStorage
from common import disp

"""
==========================================================================================
    >>> main

    This section is the 'main' or starting point of the indexer program. The python interpreter will find this 'main' routine and execute it first.
==========================================================================================

"""

if __name__ == '__main__':
    LocalFileInvertedIndexer(storage=SQLiteInvertedIndexStorage(root_dir="./unit4")).reindex_directory(dirname=os.getcwd()+"/unit4/cacm",verbose=False)
    
    # we're done
    disp("")
    disp("")
    disp("That's all, folks.  Thanks for playing!  BYE BYE.")