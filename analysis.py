import spacy
from collections import Counter

nlp = spacy.load('en')
nlp.vocab["\n"].is_stop = True
nlp.vocab["'s"].is_stop = True
nlp.vocab[" "].is_stop = True

def analyze(articleText, comments):
    """
    Perform text analysis on passed article text and list of comment triples (from client.py)
    Returns a pair of keyword lists, then a dictionary.
    The first list is those which are common between the comments and the article.
    The second is those which only appear in the comments.
    The dictionary associates keyword strings to a comment source pair (commentID, commentPermalink).

    Each keyword list is itself a list of quads: (commentID, commentPermalink, keyword, frequency)
    commentID and commentPermalink point to some comment which referred to the keyword.
    """

    article = nlp(articleText)

    # Remove named entities from articleText (saving them for later)
    articleEnts = article.ents
    for ent in articleEnts: # First, replace entities with null zeros (preserving indexes)
        articleText = articleText[:ent.start_char]+(chr(0)*len(ent.text))+articleText[ent.end_char:]
    # Then replace all null zeros with empty strings (and handle newlines in the process)
    articleText = articleText.replace(chr(0), '').replace("\n", " ")
    # And re-analyze articleText (now sure that we don't have duplication between tokens and articleEnts).
    article = nlp(articleText)

    articleTokens  = []
    commentTokens  = []
    commentSources = {}

    for token in article:
        if not token.is_stop and not token.like_num and not token.is_punct:
            articleTokens.append(token.lower_)
            
    for ent in articleEnts:
        if ent.text in spacy.lang.en.stop_words.STOP_WORDS:
            continue
        try:
            float(ent.text)
            continue
        except:
            pass
        articleTokens.append(ent.text)

    # Process all comments at once for named entities
    comments=[(comment[0], comment[1], comment[2], nlp(comment[2]).ents) for comment in comments]
    l=[]

    # Perform named entity removal over comments (See above)
    # Then replace original comment text with the tokenized version
    for comment in comments:
        temp=comment[2]
        for ent in comment[3]:
            temp=temp[:ent.start_char]+(chr(0)*len(ent.text))+temp[ent.end_char:]
        temp=nlp(temp.replace(chr(0), '').replace("\n", " "))
        l.append((comment[0], comment[1], temp, comment[3]))

    comments=l
    l=None

    pos_whitelist = ["NOUN", "PROPN"]

    for comment in comments:
        for token in comment[2]:
            if not token.is_stop and not token.like_num and not token.is_punct and token.pos_ in pos_whitelist:
                commentTokens.append(token.lower_)
                if not token.lower_ in commentSources:
                    commentSources[token.lower_]=[(comment[0], comment[1]),]
                else:
                    commentSources[token.lower_].append((comment[0], comment[1]))
        for ent in comment[3]:
            if ent.text in spacy.lang.en.stop_words.STOP_WORDS:
                continue
            try:
                float(ent.text)
                continue
            except:
                pass

            commentTokens.append(ent.text)
            if not ent.text in commentSources:
                commentSources[ent.text]=[(comment[0], comment[1]),]
            else:
                commentSources[ent.text].append((comment[0], comment[1]))

    commentTokens=Counter(commentTokens)

    related=[]
    unrelated=[]
    for el in commentTokens.most_common():
        source=commentSources[el[0]][0]
        keyword=(source[0], source[1], el[0], el[1])
        if el[0] in articleTokens:
            related.append(keyword)
        else:
            unrelated.append(keyword)
    return (related, unrelated, commentSources)

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
