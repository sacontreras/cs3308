import os
from abc import ABC, abstractmethod
import math  
import time

from .indexer_storage import SQLiteInvertedIndexStorage
from .indexer_ds import InvertedIndexDS

    
# this abstract class allows for varying the "form" of the document
#   for examples, the document could come in the form of
#       - a literal string
#       - a filepath, wherein the contents of the document can be located
#       - a URL, if the document contents should be retrieved from a website
#       - etc.
class AbstractInvertedIndexer(ABC):
    def __init__(self, storage):
        self.ds = InvertedIndexDS() # the "light weight" inv idx data structure tracking all metrics
        self.storage = storage
        super().__init__()
        
    @abstractmethod
    def index_document_impl(self, document_content_source, doc_id):
        pass
    
    def index_document(self, document_content_source):
        self.ds.n_documents += 1
        self.index_document_impl(document_content_source, self.ds.n_documents)
    
    
# but this assignment uses local file structure as the document source
class LocalFileInvertedIndexer(AbstractInvertedIndexer):
    def __init__(self, storage=SQLiteInvertedIndexStorage()):   # defaults to sqlite storage with db file saved to current working directory
        super().__init__(storage)
        
    def process_local_file(self, file):
        for l in file.readlines(): 
            self.ds.parse_tokenize(l)
        
    # this function handles the specifics of opening the file, which won't change for this type of document source
    # but processing (tokenizing) might; therefore, this function calls process_local_file() which can be overridden
    def index_document_impl(self, document_file_path, doc_id):
        file = None
        try:
            file = open(document_file_path, 'r')
            
            self.storage.insert_doc_dict(document_file_path, doc_id)
            
            self.process_local_file(file)
                
            return True
            
        except IOError:
            print("IOError ocurred for file %s" % document_file_path)
            return False
        
        finally:
            if file is not None:
                file.close()
                
    def __walk_directory__(self, dirname):
        all = [f for f in os.listdir(dirname) if os.path.isdir(os.path.join(dirname, f)) or os.path.isfile(os.path.join(dirname, f))] 
        for f in all:
            filepath = dirname + '/' + f
            if os.path.isdir(filepath): 
                self.__walk_directory__(filepath)
            else:    
                self.index_document(filepath)
                
    #this is the equivalent of the function originally named "walkdir"
    def reindex_directory(self, dirname, verbose=False):
        self.ds = InvertedIndexDS()
        
        self.storage.init_storage()
        
        #
        # Capture the start time of the routine so that we can determine the total running
        # time required to process the corpus
        #
        t2 = time.localtime()
        print('Start Time: %.2d:%.2d' % (t2.tm_hour, t2.tm_min))
        self.__walk_directory__(dirname)
        print('Indexing Complete, writing to storage (%s): %.2d:%.2d' % (self.storage.short_desc, t2.tm_hour, t2.tm_min))
                
        
        
        # # S.C., DEBUG: sanity check for entries in the index for terms occurring in more than one document
        # #   this is a virtual guarantee so, if this list is empty, something went wrong!
        terms_gt1_docs = list(filter(lambda item: len(item[1].docids)>1, self.ds.d_inv_index.items()))
        if len(terms_gt1_docs) == 0:
            print(f"*** WARNING!!! Apparently none of the {self.ds} terms occurs in more than one document out of the entire collection of {self.ds.n_documents} documents!!! ***")
        if verbose:
            for s_term, o_term in terms_gt1_docs:
                print(f"term['{s_term}']:")
                print(f"\ttermid: {o_term.termid}")
                print(f"\tcf_t: {o_term.collfreq}")
                print(f"\tdf_t: {o_term.docs}")
                print(f"\tdocids: {o_term.docids}")
                print()
        
        
        #
        # Create (insert data into) the inverted index tables.
        #
        for s_term, o_term in self.ds.d_inv_index.items():
            df_t = o_term.docs

            idf_t = math.log(self.ds.n_documents/df_t)
    
            # Insert a row into the TermDictionary for each unique term along with a termid which is na integer assigned to each term by incrementing an integer
            self.storage.insert_term_dict(s_term, o_term.termid, self.ds.n_documents, df_t, idf_t)
            
            # Insert a row into the posting table for each unique combination of Docid and termid
            for docid, tf_t_d in o_term.docids.items():
                # tuple to insert is defined as (TermId, DocId, tfidf, docfreq, termfreq)
                #   the only thing missing is tfidf, but we first need to compute idf
                tfidf = tf_t_d * idf_t
                
                self.storage.insert_posting(o_term.termid, docid, tf_t_d, idf_t, tfidf)
    
        #
        # Commit changes to the database and close the connection
        #
        self.storage.finalize_storage()
        t2 = time.localtime()
        
        print("Documents %i" % self.ds.n_documents) 
        print("Terms %i" % self.ds.n_terms)
        print("Tokens %i" % self.ds.n_tokens)
        t2 = time.localtime()
        print('End Time: %.2d:%.2d' % (t2.tm_hour, t2.tm_min))
     
        return True




"""
==========================================================================================
    >>> main

    This section is the 'main' or starting point of the indexer program. The python interpreter will find this 'main' routine and execute it first.
==========================================================================================

"""

if __name__ == '__main__':
    LocalFileInvertedIndexer().reindex_directory(doc_dir=os.getcwd()+'/cacm', verbose=False)
    
