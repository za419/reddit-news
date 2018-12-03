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
    ("rhuang97", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/rhuang97/","old",27),
    ("sjw1337", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/sjw1337/","ouch",1),
    ("sam123", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/sam123/","oops",3),
    ("steve340", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/steve340/","Florida",20),
    ("bboyday", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/bboyday/","mistake",5),
    ("kkian111", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/kkian111/","male",17),
    ("eaz0310", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","booked",12),
    ("eaz0310", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","grandma",13),
    ("croweH", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/croweH/","jail",23),
    ("killian__", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/killian__/","accident",11),
    ("eaz0310", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","all",11),
    ("eaz0310", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","Florida",20),
    ("eaywomj", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaywomj/","nurse", 15)


             )

    unrelated=(("eaz2fc6", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz2fc6/", "pads", 10),
               ("ty4td2a", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz8d2a/", "oreos", 8)),
               ("mikefjwf97", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/rhuang97/","Boston",15),
                ("himynameis999", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/sjw1337/","Shooter",8),
                ("trumpistheman", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/sam123/","China",13),
                ("bobthebuilder", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/steve340/","Japan",11),
                ("todayistheday", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/bboyday/","Terrorist",14),
                ("4324rfe", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/kkian111/","Saudi Arabia",32),
                ("sed720", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","Brazil",24),
                ("this777bye", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","Ronaldo",24),
                ("messi99124", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/croweH/","Messi",13),
                ("thfc1882", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/killian__/","doctor",10),
                ("nttf124123", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","patient",30),
                ("medsed123", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaz0310/","Hurricane",17),
                ("12345abcde", "/r/news/comments/a2hl8o/grandma_mistakenly_booked_into_allmale_jail_staff/eaywomj/","nurse", 15))
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
