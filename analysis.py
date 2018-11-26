import spacy
from collections import Counter

nlp = spacy.load('en')
nlp.vocab["\n"].is_stop = True
nlp.vocab["'s"].is_stop = True

def analyze(articleText, comments):
    """
    Perform text analysis on passed article text and list of comment triples (from client.py)
    Returns a pair of keyword lists.
    The first list is those which are common between the comments and the article.
    The second is those which only appear in the comments.

    Each keyword list is itself a list of quads: (commentID, commentPermalink, keyword, frequency)
    commentID and commentPermalink point to some comment which referred to the keyword.
    """

    article = nlp(articleText)
    articleTokens = []
    commentTokens = []

    for token in article:
        if not token.is_stop and not token.like_num and not token.is_punct:
            articleTokens.append(token.lower_)
    for commentTriple in comments:
        comment = nlp(commentTriple[2])
        for token in comment:
            if not token.is_stop and not token.like_num and not token.is_punct:
                commentTokens.append(token.lower_)

    print(Counter(articleTokens))
    print(Counter(commentTokens))
