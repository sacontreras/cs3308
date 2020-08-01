from unit5.search_engine import SearchEngine

"""
==========================================================================================
    >>> main

    This section is the 'main' or starting point of the search engine program. The python interpreter will find this 'main' routine and execute it first.
==========================================================================================

"""

if __name__ == '__main__':
    SearchEngine("unit4/indexer_part2.db").run() # assumes inv idx sqlite db is in same directory

