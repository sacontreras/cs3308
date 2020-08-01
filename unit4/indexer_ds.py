import re
from .porterstemmer import PorterStemmer
import string


# regular expression for: extract words, extract ID from path, check for hexa value 
chars = re.compile(r'\W+')
pattid= re.compile(r'(\d{3})/(\d{3})/(\d{3})')

p = PorterStemmer()
stopwords = [
 'i',
 'me',
 'my',
 'myself',
 'we',
 'our',
 'ours',
 'ourselves',
 'you',
 "you're",
 "you've",
 "you'll",
 "you'd",
 'your',
 'yours',
 'yourself',
 'yourselves',
 'he',
 'him',
 'his',
 'himself',
 'she',
 "she's",
 'her',
 'hers',
 'herself',
 'it',
 "it's",
 'its',
 'itself',
 'they',
 'them',
 'their',
 'theirs',
 'themselves',
 'what',
 'which',
 'who',
 'whom',
 'this',
 'that',
 "that'll",
 'these',
 'those',
 'am',
 'is',
 'are',
 'was',
 'were',
 'be',
 'been',
 'being',
 'have',
 'has',
 'had',
 'having',
 'do',
 'does',
 'did',
 'doing',
 'a',
 'an',
 'the',
 'and',
 'but',
 'if',
 'or',
 'because',
 'as',
 'until',
 'while',
 'of',
 'at',
 'by',
 'for',
 'with',
 'about',
 'against',
 'between',
 'into',
 'through',
 'during',
 'before',
 'after',
 'above',
 'below',
 'to',
 'from',
 'up',
 'down',
 'in',
 'out',
 'on',
 'off',
 'over',
 'under',
 'again',
 'further',
 'then',
 'once',
 'here',
 'there',
 'when',
 'where',
 'why',
 'how',
 'all',
 'any',
 'both',
 'each',
 'few',
 'more',
 'most',
 'other',
 'some',
 'such',
 'no',
 'nor',
 'not',
 'only',
 'own',
 'same',
 'so',
 'than',
 'too',
 'very',
 's',
 't',
 'can',
 'will',
 'just',
 'don',
 "don't",
 'should',
 "should've",
 'now',
 'd',
 'll',
 'm',
 'o',
 're',
 've',
 'y',
 'ain',
 'aren',
 "aren't",
 'couldn',
 "couldn't",
 'didn',
 "didn't",
 'doesn',
 "doesn't",
 'hadn',
 "hadn't",
 'hasn',
 "hasn't",
 'haven',
 "haven't",
 'isn',
 "isn't",
 'ma',
 'mightn',
 "mightn't",
 'mustn',
 "mustn't",
 'needn',
 "needn't",
 'shan',
 "shan't",
 'shouldn',
 "shouldn't",
 'wasn',
 "wasn't",
 'weren',
 "weren't",
 'won',
 "won't",
 'wouldn',
 "wouldn't",

 # other non-contrib words
 "html",
 "pre",
 "form"
]




#
# We will create a term object for each unique instance of a term
#
class Term():
    termid = 0
    collfreq = 0
    docs = 0 
    docids = {}    


class InvertedIndexDS():
    def __init__(self):
        self.d_inv_index = {}
        self.n_documents = 0
        self.n_tokens = 0
        self.n_terms = 0
        
    # parse/tokenize content
    def parse_tokenize(self, content): # content could be a line in a document or an entire document
        # this replaces any tab characters with a space character in the line
        # read from the file
        content = content.replace('\t',' ') 
        content = content.strip()
        
        #
        # This routine splits the contents of the line into tokens 
        tokenized = chars.split(content)
        processed_tokenized = []
        
        # for each token in the line process 
        for token in tokenized:
            # This statement removes the newline character if found 
            token = token.replace('\n','')
        
            # This statement converts all letters to lower case 
            processed_token = token.lower().strip()
            
            
            
            
            # ********** S.C.: preprocessing code that I added: BEGIN **********
            if len(processed_token) == 0:
                continue
            
            # Ignore any term that begins with a punctuation character
            if processed_token[0] in string.punctuation:
                # if DEBUG_VERBOSE: print(f"IGNORED term '{processed_token}': begins with puncuation")
                continue
            
            # Ignore any term that is a number
            if re.match(r'^([\s\d]+)$', processed_token):
                # if DEBUG_VERBOSE: print(f"IGNORED term '{processed_token}': is a number")
                continue
            
            # Ignore any term that is 2 characters or shorter in length
            if len(processed_token) < 3:
                # if DEBUG_VERBOSE: print(f"IGNORED term '{processed_token}': len < 3")
                continue
            
            # skip if it is a stopword
            if processed_token in stopwords:
                # if DEBUG_VERBOSE: print(f"IGNORED term '{processed_token}': is stopword")
                continue
            
            processed_token = p.stem(processed_token, 0,len(processed_token)-1)
            # ********** S.C.: preprocessing code that I added: END **********
            
            
        
        
            #
            # Increment the counter of the number of tokens processed. This value will
            # provide the total size of the corpus in terms of the number of terms in the
            # entire collection
            #
            self.n_tokens += 1
        
        
            # if the term doesn't currently exist in the term dictionary
            # then add the term
            if not (processed_token in self.d_inv_index.keys()): 
                self.n_terms += 1
                self.d_inv_index[processed_token] = Term() 
                self.d_inv_index[processed_token].termid = self.n_terms 
                self.d_inv_index[processed_token].docids = dict() 
                self.d_inv_index[processed_token].docs = 0
        
            # if the document is not currently in the postings
            # list for the term then add it
            #
            if not (self.n_documents in self.d_inv_index[processed_token].docids.keys()): 
                self.d_inv_index[processed_token].docs += 1
                self.d_inv_index[processed_token].docids[self.n_documents] = 0
        
            # Increment the counter that tracks the term frequency 
            self.d_inv_index[processed_token].docids[self.n_documents] += 1
            # term freq is just the sum of all freqs of this term for each doc
            self.d_inv_index[processed_token].collfreq += 1
    
            processed_tokenized.append(processed_token)
        
        return processed_tokenized