#!/usr/bin/env python

import os,sys
major, minor = sys.version_info[:2]

loc = os.path.abspath(__file__)
path = '/'.join(loc.split('/')[:-2])
path += '/lib/python%i.%i/site-packages' % (major, minor)

import site
site.addsitedir(path)

import hardlinker.tools

if __name__ == '__main__':
    hardlinker.tools.main()
