"""
BM25 & Semantic Hybrid Retriever for Historical Resolution Grounding.
Implements Okapi BM25 in pure Python with zero external dependencies.
"""

import math
import re
from collections import Counter
from src.data_loader import load_historical_conversations, load_knowledge_base, clean_tweet_text

def tokenize(text: str):
    """Tokenize and normalize text into clean lower-case alphanumeric tokens."""
    return re.findall(r'[a-z0-9]+', text.lower())

class BM25Retriever:
    """
    Okapi BM25 ranking algorithm for retrieving historical AppleSupport resolutions.
    k1 = 1.5 (term saturation parameter)
    b = 0.75 (document length normalization)
    """
    def __init__(self, corpus, text_key="customer_query", k1=1.5, b=0.75):
        self.corpus = corpus
        self.text_key = text_key
        self.k1 = k1
        self.b = b
        self.N = len(corpus)
        self.doc_lens = []
        self.doc_freqs = Counter()
        self.doc_term_freqs = []

        self._build_index()

    def _build_index(self):
        total_len = 0
        for doc in self.corpus:
            text = clean_tweet_text(doc.get(self.text_key, "") + " " + doc.get("summary", "") + " " + " ".join(doc.get("keywords", [])))
            tokens = tokenize(text)
            doc_len = len(tokens)
            self.doc_lens.append(doc_len)
            total_len += doc_len
            
            tf = Counter(tokens)
            self.doc_term_freqs.append(tf)
            for term in tf.keys():
                self.doc_freqs[term] += 1
                
        self.avg_doc_len = (total_len / self.N) if self.N > 0 else 1.0

    def _idf(self, term: str) -> float:
        n = self.doc_freqs.get(term, 0)
        # Standard Lucene/Okapi BM25 smoothing
        return math.log(1.0 + (self.N - n + 0.5) / (n + 0.5))

    def score(self, query_tokens, doc_idx: int) -> float:
        doc_len = self.doc_lens[doc_idx]
        tf = self.doc_term_freqs[doc_idx]
        score = 0.0

        for term in query_tokens:
            if term not in tf:
                continue
            freq = tf[term]
            idf = self._idf(term)
            numerator = freq * (self.k1 + 1.0)
            denominator = freq + self.k1 * (1.0 - self.b + self.b * (doc_len / self.avg_doc_len))
            score += idf * (numerator / denominator)

        return score

    def retrieve(self, query: str, top_k: int = 3):
        """Retrieve top_k documents for a given query."""
        tokens = tokenize(clean_tweet_text(query))
        if not tokens:
            return []

        scored_docs = []
        for i in range(self.N):
            s = self.score(tokens, i)
            if s > 0:
                scored_docs.append((s, self.corpus[i]))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return scored_docs[:top_k]

class HybridSupportRetriever:
    """
    Unified Support Retriever that queries both historical Twitter resolutions
    and official Apple Support Knowledge Base articles.
    """
    def __init__(self):
        self.historical_data = load_historical_conversations()
        self.kb_data = load_knowledge_base()
        
        self.hist_bm25 = BM25Retriever(self.historical_data, text_key="customer_query")
        self.kb_bm25 = BM25Retriever(self.kb_data, text_key="title")

    def retrieve_grounding_context(self, customer_query: str, top_k: int = 2):
        """
        Retrieves top relevant historical resolutions and matching official KB articles.
        Returns a structured dictionary with grounding sources.
        """
        hist_results = self.hist_bm25.retrieve(customer_query, top_k=top_k)
        kb_results = self.kb_bm25.retrieve(customer_query, top_k=1)

        grounding = {
            "top_historical_pairs": [
                {
                    "score": round(score, 3),
                    "query": item.get("customer_query", ""),
                    "reply": item.get("agent_reply", ""),
                    "kb_article_id": item.get("kb_article_id", ""),
                    "intent": item.get("intent", "")
                }
                for score, item in hist_results
            ],
            "top_kb_article": None
        }

        if kb_results:
            top_score, top_kb = kb_results[0]
            grounding["top_kb_article"] = {
                "score": round(top_score, 3),
                "article_id": top_kb.get("article_id", ""),
                "title": top_kb.get("title", ""),
                "url": top_kb.get("url", ""),
                "summary": top_kb.get("summary", ""),
                "action_type": top_kb.get("action_type", ""),
                "diagnostic_question": top_kb.get("diagnostic_question", "")
            }

        return grounding
