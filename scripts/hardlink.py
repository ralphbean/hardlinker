#!/usr/bin/env python

import hardlinker

print hardlinker.__file__
print hardlinker.__doc__

import hardlinker.tools

if __name__ == '__main__':
    hardlinker.tools.main()
