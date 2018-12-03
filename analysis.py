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

    articleText = "According to Cal Fire, the Camp Fire is now 100 percent contained and burned 153,336 acres. The Camp Fire started on Thursday, November 8 near Pulga Road and Camp Creek Road at 6:29 a.m. The fire quickly moved through the communities of Pulga, Concow, Paradise, and Magalia. As the assessment continues into the damage caused by the fire, 13,696 homes have been reported destroyed so far. The death toll is now at 85 as teams continue to search for the missing. 271 people remain unaccounted for according to the Butte County Sheriff's Office. The cause of the fire remains under investigation but according to Cal Fire, a second ignition point is possible and is being investigated."

    comment = ("eah518o",
    "/r/news/comments/a0a0v5/camp_fire_now_100_contained_153336_acres_burned/eah518o/",
    """Okay, at 15 miles to each side, that's 30x30, or 90 square miles per person, which is a bit more reasonable. This means North Carolina would be able to support 598 people, now.

For reference, the 2017 population of Charlotte, NC is 859,035 people, just by itself, which is roughly twice the population of Atlanta, GA or Raleigh, NC.

A population of about 600 people is roughly the size of one mid-size apartment complex.

(This also means, for example, that NC could be good habitat for animals like wolves, just based on the hypothetical population density. If the human population density is greater than 2 people per square mile, healthy wolves will generally leave the area and move somewhere else.)""")


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

    for comment in comments:
        for token in comment[2]:
            if not token.is_stop and not token.like_num and not token.is_punct:
                commentTokens.append(token.lower_)
                if not token.lower_ in commentSources:
                    commentSources[token.lower_]=(comment[0], comment[1])
        for ent in comment[3]:
            commentTokens.append(ent.text)
            if not ent.text in commentSources:
                commentSources[ent.text]=(comment[0], comment[1])

    commentTokens=Counter(commentTokens)

    related=[]
    unrelated=[]
    for el in commentTokens.most_common():
        source=commentSources[el[0]]
        keyword=(source[0], source[1], el[0], el[1])
        if el[0] in articleTokens:
            related.append(keyword)
        else:
            unrelated.append(keyword)
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
