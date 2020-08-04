from unit4.indexer import AbstractInvertedIndexer
from unit4.indexer_storage import SQLiteInvertedIndexStorage
from unit4.indexer_ds import InvertedIndexDS
import math  
import time
import datetime
from common import disp, strfdelta
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
from bs4.element import Script, Comment
import re
import traceback

class WebCrawlInvertedIndexer(AbstractInvertedIndexer):
    def __init__(self, storage=SQLiteInvertedIndexStorage(db_fname="webcrawler.db"), max_n_outlinks=500):   # defaults to sqlite storage with db file saved to current working directory
        super().__init__(storage)
        self.__init_wc__()
        self.max_n_outlinks = max_n_outlinks
        
        
    def __init_wc__(self):
        #
        # Initialize variables  
        #
        self.crawled = ([])              # contains the list of pages that have already been crawled
        self.tocrawl = []                # contains the queue of url's that will be crawled
        self.links_queue = 0             # counts the number of links in the queue to limit the depth of the crawl
        
    
    # this function *recursively* tokenizes only the CONTENT within tags (so html tags and attributes are excluded from the vocabulary)
    def index_element(self, elt, depth=0):
        if type(elt) is Script or type(elt) is Comment: # we are not interested in script/code and this element will contain no content/children we will want to index
            return
                
        if hasattr(elt, "string") and elt.string is not None:
            text = repr(elt.string).strip()
            if len(text) > 0:
                # pass the text extracted from the tag content to the parse_tokenize routine (of the InvertedIndexDS class) for indexing
                self.ds.parse_tokenize(text)
        
        if hasattr(elt, "contents") and len(elt.contents)>0: # then this tag contains child tags... recursively tokenize their content
            if elt.name != "footer":
                for c in elt.contents:
                    self.index_element(c, depth+1)   
        
        
    def index_document_impl(self, doc_url, doc_id):
        #
        # Parse the URL and open it.
        #
        try:
            http_response = urlopen(doc_url)
            if http_response.getcode() != 200:
                # raise ValueError(f"ERROR {http_response.getcode()} while opening {doc_url}.")
                print(f"\tcannot index this document: http response code {http_response.getcode()}")
                self.ds.n_documents -= 1    # since we don't actually index anything, we need to decrement this counter so TFIDF ccomputations are not thrown off
                self.ds.n_documents_failed_indexing += 1
                return
        except Exception as e:
            print(f"\tcannot index this document due to exception: {e}")
            self.ds.n_documents -= 1    # since we don't actually index anything, we need to decrement this counter so TFIDF ccomputations are not thrown off
            self.ds.n_documents_failed_indexing += 1
            return
            
        parsed_doc_url = urlparse(doc_url)
        
        raw_html = http_response.read()
        
        #
        # Use BeautifulSoup modules to format web page as text that can
        # be parsed and indexed
        #
        soup = BeautifulSoup(raw_html, features="html.parser")
        html_body = soup.find("body")
        if html_body is None or not hasattr(html_body, "contents") or html_body.contents is None:
            print("\tcannot index this document since it does not have an html BODY tag")
            self.ds.n_documents -= 1    # since we don't actually index anything, we need to decrement this counter so TFIDF ccomputations are not thrown off
            self.ds.n_documents_failed_indexing += 1
            return
            
        
        self.storage.insert_doc_dict(doc_url, doc_id)
                
        
        self.index_element(html_body)
            
        
        #
        # Find all of the weblinks on the page put them in the stack to crawl through
        #
        if self.links_queue < self.max_n_outlinks:
            links = re.findall('''href=["'](.[^"']+)["']''', str(html_body), re.I)

            n_links = len(links)
            if n_links > 0:
                print(f"\thtml doc contains {n_links} outlinks")
                
                # if n_links > space_remaining:
                #     print(f"\t\t*** truncating outlinks count to remaining space in queue ({space_remaining}): {n_links-space_remaining} will not be crawled ***")
                #     links = links[:space_remaining]
                    
                n_queued = 0
                n_already_queued_or_crawled = 0
                for link in (links.pop(0) for _ in range(len(links))):
                    if link.startswith('//'):
                        link = f"{parsed_doc_url.scheme}:{link}"
                    
                    elif link.startswith('/') or link.startswith('#'):
                        link = f"{parsed_doc_url.scheme}://{parsed_doc_url.netloc}{link}"
                        
                    if self.links_queue < self.max_n_outlinks:
                        if link not in self.crawled and link not in self.tocrawl:
                            print(f"\t\tqueueing link: {link}")
                            self.tocrawl.append(link)
                            self.links_queue += 1
                            n_queued += 1
                        else:
                            n_already_queued_or_crawled += 1
                            
                    else:
                        break
                    
                if n_already_queued_or_crawled > 0:
                    print(f"\t\t*** {n_already_queued_or_crawled} outlinks are either queued to be or have already been crawled ***")
                    
                n_not_queued = n_links - n_queued
                if n_not_queued != n_already_queued_or_crawled and n_queued < n_links:
                    print(f"\t\t*** {n_not_queued} were not crawled because max outlinks threshold has been reached ***")
                    
            else:
                print("\t*** html doc contains NO outlinks ***")
                
        else:
            print("\t*** skipping outlinks scan: max outlinks threshold reached ***")
                
        print("\tINDEXING COMPLETE")
                    
    
    def __crawl_web__(self, root_url):
        #
        # Crawl the starting web page and links in the web page up to the limit.
        #
        self.tocrawl.append(root_url)
        do_crawl = True
        while do_crawl:
            #
            # Pop the top url off of the queue and process it. 
            #
            try:
                crawling = self.tocrawl.pop()
            except:
                do_crawl = False
                continue
            
            l = len(crawling)
            ext = crawling[l-4:l]
            if ext in ['.pdf', '.png', '.jpg', '.gif', '.asp']:
                self.crawled.append(crawling)
                continue
            
            #
            # Print the current length of the queue of URL's to crawl
            #
            print(f"URLs queued: {len(self.tocrawl)}, INDEXING CURRENT URL: {crawling}...")
            try:
                self.index_document(crawling)
            except Exception:
                traceback.print_exc()
            
            self.crawled.append(crawling)
        
    #
    # Crawl the starting web page and links in the web page up to the limit.
    #
    def reindex_url(self, url, overwrite_storage=True, verbose=False):
        self.ds = InvertedIndexDS()
        
        self.storage.init_storage(overwrite=overwrite_storage)
        
        self.__init_wc__()
        
        # Capture the start time of the routine so that we can determine the total running
        # time required to process the corpus
        #
        
        _t0 = datetime.datetime.now()
        t0 = time.localtime()
        print('Start Time: %.2d:%.2d' % (t0.tm_hour, t0.tm_min))
        
        print()
        self.__crawl_web__(url)
        print()
        
        _t1 = datetime.datetime.now()
        t1 = time.localtime()
        print("\nIndexing Complete (started at %.2d:%.2d), writing to storage (%s): %.2d:%.2d" % (t0.tm_hour, t0.tm_min, self.storage.short_desc, t1.tm_hour, t1.tm_min))
        
        # # S.C., DEBUG: sanity check for entries in the index for terms occurring in more than one document
        # #   this is a virtual guarantee so, if this list is empty, something went wrong!
        terms_gt1_docs = list(filter(lambda item: len(item[1].docids)>1, self.ds.d_inv_index.items()))
        if len(terms_gt1_docs) == 0:
            print(f"\n*** WARNING!!! Apparently none of the {self.ds} terms occurs in more than one document out of the entire collection of {self.ds.n_documents} documents!!! ***\n")
        if verbose:
            for s_term, o_term in terms_gt1_docs:
                print(f"\nterm['{s_term}']:")
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
                self.storage.insert_posting(o_term.termid, docid, tf_t_d, idf_t, tfidf=tf_t_d*idf_t)
                
    
        #
        # Commit changes to the database and close the connection
        #
        self.storage.finalize_storage()
        
        
        _t2 = datetime.datetime.now()
        t2 = time.localtime()
        print("\nEnd Time: %.2d:%.2d\n" % (t2.tm_hour, t2.tm_min))
        
        disp("### Indexing Statistics:")
        print("\tHTML Documents Indexed:")
        print("\t\tSuccessfully: %i" % self.ds.n_documents) 
        print("\t\tFailed: %i" % self.ds.n_documents_failed_indexing) 
        print("\tTerms: %i" % self.ds.n_terms)
        print("\tProcessed Tokens: %i" % self.ds.n_tokens) 
        print("\tSkipped Tokens:") 
        print("\t\t1st letter puncuation: %i" % self.ds.n_tokens_skipped__punc) 
        print("\t\tpurely numeric: %i" % self.ds.n_tokens_skipped__number)  
        print("\t\tfewer than 3 characters: %i" % self.ds.n_tokens_skipped__len2orless)
        print("\t\tstop word: %i" % self.ds.n_tokens_skipped__stopword)
        
        print(f"\tElapsed Time: {strfdelta(_t2-_t0, '{hours}h:{minutes}m:{seconds}s')}")
        print(f"\t\tDocument Processing: {strfdelta(_t1-_t0, '{hours}h:{minutes}m:{seconds}s')}")
        print(f"\t\tWriting to storage ({self.storage.short_desc}): {strfdelta(_t2-_t1, '{hours}h:{minutes}m:{seconds}s')}")