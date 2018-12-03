import spacy
from collections import Counter

nlp = spacy.load('en')
nlp.vocab["\n"].is_stop = True
nlp.vocab["'s"].is_stop = True
nlp.vocab[" "].is_stop = True

def analyze(articleText, comments):
    """
    Perform text analysis on passed article text and list of comment triples (from client.py)
    Returns a pair of keyword lists.
    The first list is those which are common between the comments and the article.
    The second is those which only appear in the comments.

    Each keyword list is itself a list of quads: (commentID, commentPermalink, keyword, frequency)
    commentID and commentPermalink point to some comment which referred to the keyword.
    """

    # Return mock data for server testing
    related=(("eaz0310", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","Florida",20),
             ("eaywomj", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaywomj/","nurse", 15))
    unrelated=(("eaz2fc6", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz2fc6/", "pads", 10),
               ("eaz8d2a", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz8d2a/", "oreos", 8))
    return (related, unrelated)

if __name__=="__main__" and False:
    # Just take arguments from argv and run analyze on them
    import sys
    import json

    if len(sys.argv)!=3:
        try:
            print("Usage: python {0} <articleText> <commentTriples>".format(sys.argv[0]))
        except:
            print("Usage: python analysis.py <articleText> <commentTriples")
        print("  <articleText> is the text of the analysis article.")
        print("  <commentTriples> is the JSONified comments list as returned from client.py and parsed into JSON.")
        sys.exit(1)

    analyze(sys.argv[1], json.loads(sys.argv[2]))
