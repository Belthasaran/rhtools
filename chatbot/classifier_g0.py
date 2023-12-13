
import crm114
import crm114nam

cn = crm114nam.Classifier('/home/swtbot/namedata', ['good', 'bad'])
with open('goodnames.txt') as phrases_file:
    for l in phrases_file.readlines():
        if len(l)>3:
            cn.learn('good', l)

with open('badnames.txt') as phrases_file:
    for l in phrases_file.readlines():
        if len(l)>3:
            cn.learn('bad', l)



c = crm114.Classifier('/home/swtbot/textdata', ['good','spam','toxic'])

with open('goodphrases.txt') as phrases_file:
    for l in phrases_file.readlines():
        if len(l)>6:
	    c.learn('good', l)

with open('spamphrases.txt') as phrases_file:
    for l in phrases_file.readlines():
        if len(l)>6:
	    c.learn('spam', l)
label, confidence = c.classify('some text')


