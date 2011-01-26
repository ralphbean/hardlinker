#!/usr/bin/python
""" most of the work of hardlinker is done in this module """

from gstats import gStats
from __init__ import __version__

import getopt
import os
import re
import stat
import sys

# Python 2.4 backwards compatibility :/
try:
    from hashlib import md5
except ImportError, e:
    from md5 import md5

from optparse import OptionParser

def hash_value(stat_info, options):
    """ Produce a hash value optionally including certain file params """
    h = md5()

    # We add size by default :P
    h.update(str(stat_info[stat.ST_SIZE]))

    options_stat_map = {
        'notimestamp' : stat.ST_MTIME,
        'nofilemode' : stat.ST_MODE,
        'nouid' : stat.ST_UID,
        'nogid' : stat.ST_GID,
    }

    for opt, prop in options_stat_map.iteritems():
        if not getattr(options, opt):
            h.update(str(stat_info[prop]))

    return str(h.hexdigest())

def isAlreadyHardlinked(st1, st2):
    """ True is two files have the same inode and are on the same device """
    result = (
        (st1[stat.ST_INO] == st2[stat.ST_INO]) and # Inodes equal
        (st1[stat.ST_DEV] == st2[stat.ST_DEV])     # Devices equal
    )
    return result

def eligibleForHardlink(st1, st2, options):
    """ Evaluates a number of criteria to see if two files should be hardlinked

    :param st1 first file's info
    
    :param st2 second file's info

    :param options from the command line

    """

    options.__noopt__ = False
    criteria = {
        '__noopt__': lambda x, y: not isAlreadyHardlinked(x, y),
        '__noopt__': lambda x, y: x[stat.ST_SIZE] == y[stat.ST_SIZE],
        '__noopt__': lambda x, y: x[stat.ST_SIZE] != 0,
        'nouid': lambda x, y: x[stat.ST_UID] == y[stat.ST_UID],
        'nogid': lambda x, y: x[stat.ST_GID] == y[stat.ST_GID],
        'notimestamp': lambda x, y: x[stat.ST_MTIME] == y[stat.ST_MTIME],
        '__noopt__': lambda x, y: x[stat.ST_DEV] == y[stat.ST_DEV],
    }

    result = True
    for opt, predicate in criteria.iteritems():
        if not getattr(options, opt):
            result = result and predicate(st1, st2)

    if options.super_debug:
        print "\n***\n", st1
        print st2
        print "Already hardlinked: %s" % (not isAlreadyHardlinked(st1, st2))
        print "Modes:", st1[stat.ST_MODE], st2[stat.ST_MODE]
        print "UIDs:", st1[stat.ST_UID], st2[stat.ST_UID]
        print "GIDs:", st1[stat.ST_GID], st2[stat.ST_GID]
        print "SIZE:", st1[stat.ST_SIZE], st2[stat.ST_SIZE]
        print "MTIME:", st1[stat.ST_MTIME], st2[stat.ST_MTIME]
        print "Ignore date:", options.notimestamp
        print "Device:", st1[stat.ST_DEV], st2[stat.ST_DEV]
    return result


def areFileContentsEqual(filename1, filename2, options):
    """Determine if the contents of two files are equal.

    **!! This function assumes that the file sizes of the two files are equal.
    
    """
    # Open our two files
    file1 = open(filename1,'rb')
    file2 = open(filename2,'rb')
    # Make sure open succeeded
    if not (file1 and file2):
        print "Error opening file in areFileContentsEqual"
        print "Was attempting to open:"
        print "file1: %s" % filename1
        print "file2: %s" % filename2
        result = False
    else:
        if options.verbose >= 1:
            print "Comparing: %s" % filename1
            print "     to  : %s" % filename2
        buffer_size = 1024*1024
        while 1:
            buffer1 = file1.read(buffer_size)
            buffer2 = file2.read(buffer_size)
            if buffer1 != buffer2:
                result = False
                break
            if not buffer1:
                result = True
                break
        gStats.didComparison()
    return result

def areFilesHardlinkable(file_info_1, file_info_2, options):
    """ Determines if two files should be hardlinked together """
    filename1 = file_info_1[0]
    stat_info_1 = file_info_1[1]
    filename2 = file_info_2[0]
    stat_info_2 = file_info_2[1]
    # See if the files are eligible for hardlinking
    if eligibleForHardlink(stat_info_1, stat_info_2, options):
        # TODO -- simplify all this into eligible for hardlink


        # Now see if the contents of the file are the same.  If they are then
        # these two files should be hardlinked.
        if not options.samename:
            # By default we don't care if the filenames are equal
            result = areFileContentsEqual(filename1, filename2, options)
        else:
            # Make sure the filenames are the same, if so then compare content
            basename1 = os.path.basename(filename1)
            basename2 = os.path.basename(filename2)
            if basename1 == basename2:
                result = areFileContentsEqual(filename1, filename2, options)
            else:
                result = False
    else:
        result = False
    return result

def hardlinkfiles(sourcefile, destfile, stat_info, options):
    """ hardlink two files together """

    # rename the destination file to save it
    temp_name = destfile + ".$$$___cleanit___$$$"
    try:
        if not options.dryrun:
            os.rename(destfile, temp_name)
    except OSError, error:
        print "Failed to rename: %s to %s" % (destfile, temp_name)
        print error
        result = False
    else:
        # Now link the sourcefile to the destination file
        try:
            if not options.dryrun:
                os.link(sourcefile, destfile)
        except:
            print "Failed to hardlink: %s to %s" % (sourcefile, destfile)
            # Try to recover
            try:
                os.rename(temp_name, destfile)
            except:
                print "BAD BAD - failed to rename back %s to %s" (temp_name, destfile)
            result = False
        else:
            # hard link succeeded
            # Delete the renamed version since we don't need it.
            if not options.dryrun:
                os.unlink ( temp_name)
            # update our stats
            gStats.didHardlink(sourcefile, destfile, stat_info)
            if options.verbose >= 1:
                if options.dryrun:
                    print "Did NOT link.  Dry run"
                size = stat_info[stat.ST_SIZE]
                print "Linked: %s" % sourcefile
                print"     to: %s, saved %s" % (destfile, size)
            result = True
    return result

def hardlink_identical_files(directories, filename, options):
    """
    The purpose of this function is to hardlink files together if the files are
    the same.  To be considered the same they must be equal in the following
    criteria:
          * file mode
          * owner user id
          * owner group id
          * file size
          * modified time (optional)
          * file contents

    Also, files will only be hardlinked if they are on the same device.  This
    is because hardlink does not allow you to hardlink across file systems.

    The basic idea on how this is done is as follows:

        Walk the directory tree building up a list of the files.

     For each file, generate a simple hash based on the size and modified time.

     For any other files which share this hash make sure that they are not
     identical to this file.  If they are identical then hardlink the files.

     Add the file info to the list of files that have the same hash value.
     
     """

    for exclude in options.excludes:
        if re.search(exclude, filename):
            return
    try:
        stat_info = os.stat(filename)
    except OSError:
        # Python 1.5.2 doesn't handle 2GB+ files well :(
        print "Unable to get stat info for: %s" % filename
        print "If running Python 1.5 this could be because the file is greater than 2 Gibibytes"
        return
    if not stat_info:
        # We didn't get the file status info :(
        return

    # Is it a directory?
    if stat.S_ISDIR(stat_info[stat.ST_MODE]):
        # If it is a directory then add it to the list of directories.
        directories.append(filename)
    # Is it a regular file?
    elif stat.S_ISREG(stat_info[stat.ST_MODE]):
        # Create the hash for the file.
        file_hash = hash_value(stat_info, options)

        # Bump statistics count of regular files found.
        gStats.foundRegularFile()
        if options.verbose >= 2:
            print "File: %s" % filename
        work_file_info = (filename, stat_info)
        if file_hashes.has_key(file_hash):
            # We have file(s) that have the same hash as our current file.
            # Let's go through the list of files with the same hash and see if
            # we are already hardlinked to any of them.
            for (temp_filename,temp_stat_info) in file_hashes[file_hash]:
                if isAlreadyHardlinked(stat_info,temp_stat_info):
                    gStats.foundHardlink(temp_filename,filename,temp_stat_info)
                    break
            else:
                # We did not find this file as hardlinked to any other file
                # yet.  So now lets see if our file should be hardlinked to any
                # of the other files with the same hash.
                for (temp_filename,temp_stat_info) in file_hashes[file_hash]:
                    if areFilesHardlinkable(work_file_info,
                                            (temp_filename,temp_stat_info),
                                            options):
                        hardlinkfiles(temp_filename, filename,
                                      temp_stat_info, options)
                        break
                else:
                    # The file should NOT be hardlinked to any of the other
                    # files with the same hash.  So we will add it to the list
                    # of files.
                    file_hashes[file_hash].append(work_file_info)
        else:
            # There weren't any other files with the same hash value so we will
            # create a new entry and store our file.
            file_hashes[file_hash] = [work_file_info]

def printversion(self):
    print "hardlink.py, Version %s" % __version__
    print "Copyright (C) 2003 - 2006 John L. Villalovos."
    print "email: software@sodarock.com"
    print "web: http://www.sodarock.com/"
    print """
This program is free software; you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation; version 2 of the License.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program; if not, write to the Free Software Foundation, Inc., 59 Temple
Place, Suite 330, Boston, MA  02111-1307, USA.
"""


def parseCommandLine():
    usage = "usage: %prog [options] directory [ directory ... ]"
    version = "%prog: " + __version__
    parser = OptionParser(usage=usage, version=version)

    parser.add_option(
        "-d", "--debug",
        help="Print debug output along the way",
        action="store_true", dest="debug", default=False,)

    parser.add_option(
        "-D", "--super-debug",
        help="Print a ton of debug output along the way",
        action="store_true", dest="super_debug", default=False,)

    parser.add_option(
        "-f", "--filenames-equal",
        help="Filenames have to be identical",
        action="store_true", dest="samename", default=False,)

    parser.add_option(
        "-t", "--ignore-timestamp",
        help="File modification times do NOT have to be identical",
        action="store_true", dest="notimestamp", default=False,)

    parser.add_option(
        "-m", "--ignore-mode",
        help="File modes do NOT have to be identical",
        action="store_true", dest="nofilemode", default=False,)

    parser.add_option(
        "-u", "--ignore-uid",
        help="File owner user ids do NOT have to be identical",
        action="store_true", dest="nouid", default=False,)

    parser.add_option(
        "-g", "--ignore-gid",
        help="File owner group ids do NOT have to be identical",
        action="store_true", dest="nogid", default=False,)

    parser.add_option(
        "-n", "--dry-run", help="Do NOT actually hardlink files",
        action="store_true", dest="dryrun", default=False,)

    parser.add_option(
        "-p", "--print-previous", help="Print previously created hardlinks",
        action="store_true", dest="printprevious", default=False,)

    parser.add_option(
        "-q", "--no-stats", help="Do not print the statistics",
        action="store_false", dest="printstats", default=True,)


    parser.add_option(
        "-v", "--verbose", help="Verbosity level (default: %default)",
        metavar="LEVEL", action="store", dest="verbose", default=1,)

    parser.add_option(
        "-x", "--exclude",
        help="Regular expression used to exclude files/dirs " + \
        "(may specify multiple times)",
        metavar="REGEX", action="append", dest="excludes", default=[],)

    (options, args) = parser.parse_args()
    if not args:
        parser.print_help()
        print
        print "Error: Must supply one or more directories"
        sys.exit(1)
    args = [os.path.abspath(os.path.expanduser(dirname)) for dirname in args]
    for dirname in args:
        if not os.path.isdir(dirname):
            parser.print_help()
            print
            print "Error: %s is NOT a directory" % dirname
            sys.exit(1)
    return options, args


file_hashes = {}

def main():
    """ main entry point

    TODO -- actually use python `entry_points`
    """

    # Parse our argument list and get our list of directories
    options, directories = parseCommandLine()
    # Compile up our regexes ahead of time
    MIRROR_PL_REGEX = re.compile(r'^\.in\.')
    RSYNC_TEMP_REGEX = re.compile((r'^\..*\.\?{6,6}$'))
    # Now go through all the directories that have been added.
    # NOTE: hardlink_identical_files() will add more directories to the
    #       directories list as it finds them.
    while directories:
        # Get the last directory in the list
        directory = directories[-1] + '/'
        del directories[-1]
        if not os.path.isdir(directory):
            print "%s is NOT a directory!" % directory
        else:
            gStats.foundDirectory()
            # Loop through all the files in the directory
            try:
                dir_entries = os.listdir(directory)
            except OSError:
                print "Error: Unable to do an os.listdir on: %s  Skipping..." % directory
                continue
            for entry in dir_entries:
                pathname = os.path.normpath(os.path.join(directory,entry))
                # Look at files/dirs beginning with "."
                if entry[0] == ".":
                    # Ignore any mirror.pl files.  These are the files that
                    # start with ".in."
                    if MIRROR_PL_REGEX.match(entry):
                        if options.super_debug:
                            print "%s is a mirror.pl file, ignoring" % pathname
                        continue
                    # Ignore any RSYNC files.  These are files that have the
                    # format .FILENAME.??????
                    if RSYNC_TEMP_REGEX.match(entry):
                        if options.super_debug:
                            print "%s is a rsync file, ignoring" % pathname
                        continue
                if os.path.islink(pathname):
                    if options.debug:
                        print "%s: is a symbolic link, ignoring" % pathname
                    continue
                if options.debug and os.path.isdir(pathname):
                    print "%s is a directory!" % pathname
                hardlink_identical_files(directories, pathname, options)
    if options.printstats:
        gStats.printStats(options)

if __name__ == '__main__':
    main()
