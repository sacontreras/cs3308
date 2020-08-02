from abc import ABC, abstractmethod
import sqlite3
import os

# this abstract class allows for varying external storage of the inverted index
class AbstractInvertedIndexStorage(ABC):
    def __init__(self, root_dir, short_desc):
        self.root_dir = root_dir
        self.short_desc = short_desc
        super().__init__()

    @abstractmethod
    def init_storage(self, overwrite=True):
        pass
    
    @abstractmethod
    def insert_doc_dict(self, doc_path, doc_id):
        pass
    
    @abstractmethod
    def insert_term_dict(self, term, termid, N, df_t, idf_t):
        pass
    
    @abstractmethod
    def insert_posting(self, termid, docid, tf_t_d, idf_t, tfidf):
        pass
    
    @abstractmethod
    def purge_storage(self):
        pass
    
    @abstractmethod
    def finalize_storage(self):
        pass


# but implementation in this file defaults to sqlite storage    
class SQLiteInvertedIndexStorage(AbstractInvertedIndexStorage):
    def __init__(self, root_dir=os.getcwd(), db_fname="indexer_part2.db"):
        self.db_fname = db_fname
        self.con = None
        self.cur = None
        super().__init__(root_dir, 'sqlite database')
        

    def init_storage(self, overwrite=True):
        #
        # Create a sqlite database to hold the inverted index. The isolation_level statment turns
    
        # on autocommit which means that changes made in the database are committed automatically
        #
        self.con = sqlite3.connect(self.root_dir + '/' + self.db_fname) 
        self.con.isolation_level = None
        self.cur = self.con.cursor()
        
        #
        # In the following section three tables and their associated indexes will be created.
        # Before we create the table or index we will attempt to drop any existing tables in
        # case they exist
        #
        
        # Document Dictionary Table
        if overwrite:
            self.cur.execute("drop table if exists DocumentDictionary") 
            self.cur.execute("drop index if exists idxDocumentDictionary")
        self.cur.execute("create table if not exists DocumentDictionary (DocumentName text, DocId int)") 
        self.cur.execute("create index if not exists idxDocumentDictionary on DocumentDictionary (DocId)")
        
        # Term Dictionary Table
        if overwrite:
            self.cur.execute("drop table if exists TermDictionary") 
            self.cur.execute("drop index if exists idxTermDictionary")
        self.cur.execute("create table if not exists TermDictionary (Term text, TermId int, N int, df_t int, idf_t real)") 
        self.cur.execute("create index if not exists idxTermDictionary on TermDictionary (TermId)")
        
        # Postings Table
        if overwrite:
            self.cur.execute("drop table if exists Posting") 
            self.cur.execute("drop index if exists idxPosting1") 
            self.cur.execute("drop index if exists idxPosting2")
        self.cur.execute("create table if not exists Posting (TermId int, DocId int, tf_t_d int, idf_t real, tfidf real)") 
        self.cur.execute("create index if not exists idxPosting1 on Posting (TermId)")
        self.cur.execute("create index if not exists idxPosting2 on Posting (Docid)")
        
    
    def insert_doc_dict(self, doc_path, doc_id):
        self.cur.execute("insert into DocumentDictionary values (?, ?)", (doc_path, doc_id))
        
    
    def insert_term_dict(self, term, termid, N, df_t, idf_t):
        # Insert a row into the TermDictionary for each unique term along with a termid which is na integer assigned to each term by incrementing an integer
        self.cur.execute("insert into TermDictionary values (?, ?, ?, ?, ?)", (term, termid, N, df_t, idf_t))
        
    
    def insert_posting(self, termid, docid, tf_t_d, idf_t, tfidf):
        self.cur.execute("insert into Posting values (?, ?, ?, ?, ?)", (termid, docid, tf_t_d, idf_t, tfidf))
        
    
    def purge_storage(self):
        if self.con is None:
            self.con = sqlite3.connect(self.root_dir + '/' + self.db_fname) 
            self.con.isolation_level = None
            self.cur = self.con.cursor()
            
        self.cur.execute("drop table if exists DocumentDictionary") 
        self.cur.execute("drop index if exists idxDocumentDictionary")
        self.cur.execute("drop table if exists TermDictionary") 
        self.cur.execute("drop index if exists idxTermDictionary")
        self.cur.execute("drop table if exists Posting") 
        self.cur.execute("drop index if exists idxPosting1") 
        self.cur.execute("drop index if exists idxPosting2")
        
    
    def finalize_storage(self):
        #
        # Commit changes to the database and close the connection
        #
        self.con.commit() 
        self.con.close()