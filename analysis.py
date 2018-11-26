import spacy
from collections import Counter

nlp = spacy.load('en')
nlp.vocab["\n"].is_stop = True
nlp.vocab["'s"].is_stop = True

def analyze(a, b):
    """
    Perform text analysis on passed article text and list of comment triples (from client.py)
    Returns a pair of keyword lists.
    The first list is those which are common between the comments and the article.
    The second is those which only appear in the comments.

    Each keyword list is itself a list of quads: (commentID, commentPermalink, keyword, frequency)
    commentID and commentPermalink point to some comment which referred to the keyword.
    """

    doc1 = nlp(a)
    arr1 = []
    arr2 = []

    for token in doc1:
        if not token.is_stop and not token.like_num and not token.is_punct:
            arr1.append(token.lower_)
    for comment in b:
        doc2 = nlp(comment[2])
        for token in doc2:
            if not token.is_stop and not token.like_num and not token.is_punct:
                arr2.append(token.lower_)

    print(Counter(arr1))
    print(Counter(arr2))