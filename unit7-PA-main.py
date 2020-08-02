# this file does the "same thing" as the associated Jupyter Notebook (unit7-PA-labreport.ipynb)
#   it is included in order to run the assignment from the command-line instead of as a Jupyter Notebook (in case you don't have Jupyter installed)

from unit7.webcrawler_indexer import WebCrawlInvertedIndexer
from unit4.indexer_storage import SQLiteInvertedIndexStorage
from common import disp
from unit5.search_engine import SearchEngine

"""
==========================================================================================
    >>> main

    This section is the 'main' or starting point of the search engine program. The python interpreter will find this 'main' routine and execute it first.
==========================================================================================

"""

if __name__ == '__main__':
    b_quit = False
    b_first_run = True # use this to purge the on the first run and append to it thereafter
    while not b_quit:
        root_url = input("Enter URL to crawl (must be in the form http://www.domain.com): ").strip()
        if len(root_url) == 0:
            b_quit = len(input("Are you sure you want to QUIT? (press ENTER again to confirm): ").strip()) == 0
        else:
            WebCrawlInvertedIndexer(
                storage=SQLiteInvertedIndexStorage(root_dir="./unit7", db_fname="webcrawler.db"),
                max_n_outlinks=500
            ).reindex_url(root_url, overwrite_storage=b_first_run)
        b_first_run = False
        
    srch_engine = SearchEngine("unit7/webcrawler.db")
    srch_engine.run()
    
    # we're done
    disp("")
    disp("")
    disp("That's all, folks.  Thanks for playing!  BYE BYE.")