import json

spamfilterItems = []
spamfilterWords = []
spamfilterExpr = []
spamfilterjson = None
spamfilterRE = None
#
with open('spamfilter.json') as json_file:
    spamfilterjson = json.load(json_file)
    for wentry in spamfilterjson:
        spamfilterWords = spamfilterWords + [wentry["word"]]
        spamfilterItems = spamfilterItems + [wentry]
print('(%s)' % '|'.join(spamfilterWords))
#            #spamFilterRE = re.compile( '(%s)' % '|'.join(spamfilterWords), re.I )
