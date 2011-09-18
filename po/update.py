#!/usr/bin/env python

import glob
import os.path
import shutil

sources = []
for root, dirs, files in os.walk(os.path.join('..', 'picard')):
    for name in files:
        if name.endswith('.py'):
            sources.append(os.path.join(root, name))

cmd = "xgettext --copyright-holder=MusicBrainz " \
    "--msgid-bugs-address=http://tickets.musicbrainz.org/ " \
    "--add-comments=TR -L Python -d picard -o picard.pot --keyword=N_ " + \
    " ".join(sources)

print cmd
os.system(cmd)
print

f = file('picard.pot', 'rt')
lines = f.readlines()
f.close()
f = file('picard.pot', 'wt')
for line in lines:
    if line.startswith('#. TR: '):
        line = '#. ' + line[7:]
    f.write(line)
f.close()

for po in glob.glob("*.po"):
    cmd = "msgmerge %s picard.pot -o new.%s" % (po, po)
    print cmd
    if os.system(cmd) == 0:
        print "new.%s.po --> %s" % (po, po)
        shutil.move("new.%s" % po, po)
        os.system("msgfmt --statistics  -c -v -o %s %s" % (os.devnull, po))
        print
