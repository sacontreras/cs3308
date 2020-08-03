from unit4.indexer import AbstractInvertedIndexer
from unit4.indexer_storage import SQLiteInvertedIndexStorage
from unit4.indexer_ds import InvertedIndexDS
import math  
import time
from urllib.parse import urlparse
from urllib.request import urlopen
from bs4 import BeautifulSoup
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
        
        
    # this function handles the specifics of opening the file, which won't change for this type of document source
    # but processing (tokenizing) might; therefore, this function calls process_local_file() which can be overridden
    def index_document_impl(self, doc_url, doc_id):
        #
        # Parse the URL and open it.
        #
        try:
            http_response = urlopen(doc_url)
            if http_response.getcode() != 200:
                # raise ValueError(f"ERROR {http_response.getcode()} while opening {doc_url}.")
                print(f"\tcannot index this document: http response code {http_response.getcode()}")
                return
        except Exception as e:
            print(f"\tcannot index this document due to exception: {e}")
            return
            
        parsed_doc_url = urlparse(doc_url)
        print(f"\tparsed_doc_url: {parsed_doc_url}")
        
        raw_html = http_response.read()
        # print(f"raw_html: {raw_html}")
        
        #
        # Use BeautifulSoup modules to format web page as text that can
        # be parsed and indexed
        #
        soup = BeautifulSoup(raw_html, features="html.parser")
        # print(f"soup: {soup}")
        html_body = soup.find("body")
        if html_body is None or not hasattr(html_body, "contents") or html_body.contents is None:
            print("\tcannot index this document since it does not have an html BODY tag")
            return
            
        self.storage.insert_doc_dict(doc_url, doc_id)
            
        elements = html_body.contents 
        # print(f"content: {content}\n\n")
        
        # pass the text extracted from the web page to the parse_tokenize routine (of the InvertedIndexDS class) for indexing
        for elt in elements:
            s_elt = str(elt).strip()
            if len(s_elt) > 0:
                self.ds.parse_tokenize(s_elt)
            
        #
        # Find all of the weblinks on the page put them in the stack to crawl through
        #
        if self.links_queue < self.max_n_outlinks:
            space_remaining = self.max_n_outlinks - self.links_queue
            links = re.findall('''href=["'](.[^"']+)["']''', str(html_body), re.I)

            n_links = len(links)
            if n_links > 0:
                print(f"\thtml doc contains {n_links} outlinks")
                
                if n_links > space_remaining:
                    print(f"\t\ttruncating outlinks count to remaining space in queue ({space_remaining})")
                    links = links[:space_remaining]
                    
                n_queued_or_crawled = 0
                for link in (links.pop(0) for _ in range(len(links))):
                    if link.startswith('//'):
                        link = f"{parsed_doc_url.scheme}:{link}"
                    
                    elif link.startswith('/') or link.startswith('#'):
                        link = f"{parsed_doc_url.scheme}://{parsed_doc_url.netloc}{link}"
                        
                    if link not in self.crawled and link not in self.tocrawl:
                        print(f"\t\tqueueing link: {link}")
                        self.links_queue += 1
                        self.tocrawl.append(link)
                    else:
                        n_queued_or_crawled += 1
                        
                print(f"\t\t*** {n_queued_or_crawled} of the remaining outlinks are either queued to be or have already been crawled ***")
            else:
                print("\thtml doc contains NO outlinks")
        else:
            print(f"\tskipping outlinks scan: outlinks queue is full")
                
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
        t0 = time.localtime()
        print('Start Time: %.2d:%.2d' % (t0.tm_hour, t0.tm_min))
        
        print()
        self.__crawl_web__(url)
        print()
        
        t1 = time.localtime()
        print('\nIndexing Complete (started at %.2d:%.2d), writing to storage (%s): %.2d:%.2d' % (t0.tm_hour, t0.tm_min, self.storage.short_desc, t1.tm_hour, t1.tm_min))
        
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
                # tuple to insert is defined as (TermId, DocId, tfidf, docfreq, termfreq)
                #   the only thing missing is tfidf, but we first need to compute idf
                tfidf = tf_t_d * idf_t
                
                self.storage.insert_posting(o_term.termid, docid, tf_t_d, idf_t, tfidf)
    
        #
        # Commit changes to the database and close the connection
        #
        self.storage.finalize_storage()
        t2 = time.localtime()
        
        print("Documents: %i" % self.ds.n_documents) 
        print("Terms: %i" % self.ds.n_terms)
        print("Tokens: %i" % self.ds.n_tokens)
        t2 = time.localtime()
        print('End Time: %.2d:%.2d' % (t2.tm_hour, t2.tm_min))