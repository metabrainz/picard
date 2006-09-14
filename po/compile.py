#!/usr/bin/env python

import glob, os, os.path

for po in glob.glob("*.po"):
    lang = po.split('.')[0]
    path = "../locale/%s/LC_MESSAGES" % lang
    if not os.path.isdir(path):
        os.makedirs(path)
    cmd = "msgfmt %s -o %s/picard.mo" % (po, path)
    print cmd
    os.system(cmd)
           
      
                    
  


