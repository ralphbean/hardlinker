
import time
import stat

def humanize_number( number ):
    if number  > 1024 * 1024 * 1024:
        return ("%.3f gibibytes" % (number / (1024.0 * 1024 * 1024)))
    if number  > 1024 * 1024:
        return ("%.3f mibibytes" % (number / (1024.0 * 1024)))
    if number  > 1024:
        return ("%.3f kibibytes" % (number / 1024.0))
    return ("%d bytes" % number)

class cStatistics:
    def __init__(self):
        self.dircount = 0L               # how many directories we find
        self.regularfiles = 0L           # how many regular files we find
        self.comparisons = 0L            # how many file content comparisons
        self.hardlinked_thisrun = 0L     # hardlinks done this run
        self.hardlinked_previously = 0L; # hardlinks that are already existing
        self.bytes_saved_thisrun = 0L    # bytes saved by hardlinking this run
        self.bytes_saved_previously = 0L # bytes saved by previous hardlinks
        self.hardlinkstats = []          # list of files hardlinked this run
        self.starttime = time.time()     # track how long it takes
        self.previouslyhardlinked = {}   # list of files hardlinked previously

    def foundDirectory(self):
        self.dircount = self.dircount + 1

    def foundRegularFile(self):
        self.regularfiles = self.regularfiles + 1

    def didComparison(self):
        self.comparisons = self.comparisons + 1

    def foundHardlink(self,sourcefile, destfile, stat_info):
        filesize = stat_info[stat.ST_SIZE]
        self.hardlinked_previously = self.hardlinked_previously + 1
        self.bytes_saved_previously = self.bytes_saved_previously + filesize
        if not self.previouslyhardlinked.has_key(sourcefile):
            self.previouslyhardlinked[sourcefile] = (stat_info,[destfile])
        else:
            self.previouslyhardlinked[sourcefile][1].append(destfile)

    def didHardlink(self,sourcefile,destfile,stat_info):
        filesize = stat_info[stat.ST_SIZE]
        self.hardlinked_thisrun = self.hardlinked_thisrun + 1
        self.bytes_saved_thisrun = self.bytes_saved_thisrun + filesize
        self.hardlinkstats.append((sourcefile, destfile))

    def printStats(self, options):
        print "\n"
        print "Hard linking Statistics:"
        # Print out the stats for the files we hardlinked, if any
        if self.previouslyhardlinked and options.printprevious:
            keys = self.previouslyhardlinked.keys()
            keys.sort()
            print "Files Previously Hardlinked:"
            for key in keys:
                stat_info, file_list = self.previouslyhardlinked[key]
                size = stat_info[stat.ST_SIZE]
                print "Hardlinked together: %s" % key
                for filename in file_list:
                    print "                   : %s" % filename
                print "Size per file: %s  Total saved: %s" % (size,
                                    size * len(file_list))
            print
        if self.hardlinkstats:
            if options.dryrun:
                print "Statistics reflect what would have happened if not a dry run"
            print "Files Hardlinked this run:"
            for (source,dest) in self.hardlinkstats:
                print"Hardlinked: %s" % source
                print"        to: %s" % dest
            print
        print "Directories           : %s" % self.dircount
        print "Regular files         : %s" % self.regularfiles
        print "Comparisons           : %s" % self.comparisons
        print "Hardlinked this run   : %s" % self.hardlinked_thisrun
        print "Total hardlinks       : %s" % (self.hardlinked_previously + self.hardlinked_thisrun)
        print "Bytes saved this run  : %s (%s)" % (self.bytes_saved_thisrun, humanize_number(self.bytes_saved_thisrun))
        totalbytes = self.bytes_saved_thisrun + self.bytes_saved_previously;
        print "Total bytes saved     : %s (%s)" % (totalbytes, humanize_number(totalbytes))
        print "Total run time        : %s seconds" % (time.time() - self.starttime)
 

gStats = cStatistics()

