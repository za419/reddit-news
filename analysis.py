import spacy
from collections import Counter

nlp = spacy.load('en')
nlp.vocab["\n"].is_stop = True
nlp.vocab["'s"].is_stop = True

def analyze(a, b):

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