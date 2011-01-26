"""
 hardlinker - Goes through a directory structure and creates hardlinks for
 files which are identical.

 Copyright (C) 2003 - 2007  John L. Villalovos, Hillsboro, Oregon

 This program is free software; you can redistribute it and/or modify it under
 the terms of the GNU General Public License as published by the Free Software
 Foundation; either version 2 of the License, or (at your option) any later
 version.

 This program is distributed in the hope that it will be useful, but WITHOUT
 ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
 more details.

 You should have received a copy of the GNU General Public License along
 with this program; if not, write to the Free Software Foundation, Inc., 59
 Temple Place, Suite 330, Boston, MA  02111-1307, USA.

 ------------------------------------------------------------------------

 Forked project url: http://github.com/ralphbean/hardlinker/
 Original project url:  http://code.google.com/p/hardlinkpy/

 AUTHORS

 John Villalovos
 email: john@sodarock.com
 http://www.sodarock.com/

 Ralph Bean
 email: ralph.bean@gmail.com
 http://threebean.wordpress.com/

 Inspiration for this program came from the hardlink.c code. I liked what it
 did but did not like the code itself, to me it was very unmaintainable.  So I
 rewrote in C++ and then I rewrote it in python.  In reality this code is
 nothing like the original hardlink.c, since I do things quite differently.
 Even though this code is written in python the performance of the python
 version is much faster than the hardlink.c code, in my limited testing.  This
 is mainly due to use of different algorithms.

 Original inspirational hardlink.c code was written by:  Jakub Jelinek
 <jakub@redhat.com>

 ------------------------------------------------------------------------

 TODO:
   *   Thinking it might make sense to walk the entire tree first and collect
       up all the file information before starting to do comparisons.  Thought
       here is we could find all the files which are hardlinked to each other
       and then do a comparison.  If they are identical then hardlink
       everything at once.
"""


__version__ = '0.5.0'
__version_info__ = tuple([ int(num) for num in __version__.split('.')])
