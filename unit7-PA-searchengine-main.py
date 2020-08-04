# this file does the "same thing" as the associated Jupyter Notebook (unit7-PA-searchengine-labreport.ipynb)
#   it is included in order to run the assignment from the command-line instead of as a Jupyter Notebook (in case you don't have Jupyter installed)

from unit5.search_engine import SearchEngine
from common import disp

"""
==========================================================================================
    >>> main

    This section is the 'main' or starting point of the search engine program. The python interpreter will find this 'main' routine and execute it first.
==========================================================================================

"""

if __name__ == '__main__':
    srch_engine = SearchEngine("unit7/webcrawler.db")
    srch_engine.run()

    # we're done
    disp("")
    disp("")
    disp("That's all, folks.  Thanks for playing!  BYE BYE.")