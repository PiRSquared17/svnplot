'''
svnstats.py

This is a helper class for getting the actual subversion statistics from the database.
SVNPlot and other classes will use this to query the data and then render it as
graphs or html tables or json data.
'''

import sqlite3
import calendar, datetime
import os.path, sys
import string
import operator
import logging

def filetype(path):
    '''
    get the file type (i.e. extension) from the path
    '''
    (root, ext) = os.path.splitext(path)
    return(ext)

def dirname(searchpath, path, depth):
    '''
    get directory name till given depth (relative to searchpath) from the full file path
    '''
    assert(searchpath != None and searchpath != "")
    #replace the search path and then compare the depth
    path = path.replace(searchpath, "", 1)
    #first split the path and remove the filename
    pathcomp = os.path.dirname(path).split('/')
    #now join the split path upto given depth only
    dirpath = '/'.join(pathcomp[0:depth])
    #Now add the dirpath to searchpath to get the final directory path
    dirpath = searchpath+dirpath
    #print "%s : [%s]" %(path, dirpath)
    return(dirpath)

class SVNStats:
    def __init__(self, svndbpath):
        self.svndbpath = svndbpath
        self.__searchpath = '/%'
        self.verbose = False
        self.bugfixkeywords = ['bug', 'fix']

        self.dbcon = sqlite3.connect(self.svndbpath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        #self.dbcon.row_factory = sqlite3.Row
        # Create the function "regexp" for the REGEXP operator of SQLite
        self.dbcon.create_function("dirname", 3, dirname)
        self.dbcon.create_function("filetype", 1, filetype)        
        self.cur = self.dbcon.cursor() 
            
    def __del__(self):
        self.cur.close()
        self.dbcon.commit()
        self.dbcon.close()
        
    def SetVerbose(self, verbose):       
        self.verbose = verbose

    def SetSearchPath(self, searchpath = '/'):
        '''
        Set the path for searching the repository data.
        Default value is '/%' which searches all paths in the repository.
        Use self.SetSearchPath('/trunk/%') for searching inside the 'trunk' folder only
        '''
        if(searchpath != None and len(searchpath) > 0):
            self.__searchpath = searchpath
        if( self.__searchpath.endswith('%')==True):
            self.__searchpath = self.__searchpath[:-1]
        self._printProgress("Set the search path to %s" % self.__searchpath)

    @property
    def searchpath(self):
        return(self.__searchpath)

    @property    
    def sqlsearchpath(self):
        '''
        return the sql regex search path (e.g. '/trunk/' will be returned as '/trunk/%'
        '''
        return(self.__searchpath + '%')

    def _printProgress(self, msg):
        if( self.verbose == True):
            print msg

    def __sqlForbugFixKeywordsInMsg(self):
        sqlstr = "( "
        first = True
        for keyword in self.bugfixkeywords:
            if( first == False):
                sqlstr = sqlstr + ' or '
            sqlstr=sqlstr + "svnlog.msg like '%%%s%%'" % keyword
            first = False
        sqlstr = sqlstr + " )"
        return(sqlstr)
    
    def getAuthorList(self, numAuthors=None):
        #Find out the unique developers and their number of commit sorted in 'descending' order
        self.cur.execute("select author, count(*) as commitcount from SVNLog group by author order by commitcount desc")
        
        #get the auhor list (ignore commitcount) and store it. Since LogGraphLineByDev also does an sql query. It will otherwise
        # get overwritten
        authList = [author for author,commitcount in self.cur]
        #Keep only top 'numAuthors'
        if( numAuthors != None):
            authList = authList[:numAuthors]
        
        #if there is an empty string in author list, replace it by "unknown"
        authListFinal = []
        for author in authList:
            if( author == ""):
                author='unknown'
            authListFinal.append(author)
        return(authListFinal)

    def getActivityByWeekday(self):
        '''
        returns two lists (commit counts and weekday)
        '''
        self.cur.execute("select strftime('%w', SVNLog.commitdate), count(SVNLog.revno) from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                         group by strftime('%w', SVNLog.commitdate)", (self.sqlsearchpath,))
        weekdaylist=[]
        commits = []
        for dayofweek, commitcount in self.cur:
           commits.append(commitcount)           
           weekdaylist.append(calendar.day_abbr[int(dayofweek)])
           
        return(commits, weekdaylist)

    def getActivityByTimeOfDay(self):
        '''
        returns two lists (commit counts and time of day)
        '''
        self.cur.execute("select strftime('%H', SVNLog.commitdate), count(SVNLog.revno) from SVNLog, SVNLogDetail \
                          where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                          group by strftime('%H', SVNLog.commitdate)", (self.sqlsearchpath,))
        commits =[]
        hrofdaylist = []
        for hourofday, commitcount in self.cur:
           commits.append(commitcount)           
           hrofdaylist.append(int(hourofday))
        return(commits, hrofdaylist)

    def getFileCountStats(self):
        '''
        returns two lists (dates and total file count on those dates)
        '''
        self.cur.execute("select strftime('%Y', SVNLog.commitdate), strftime('%m', SVNLog.commitdate),\
                         strftime('%d', SVNLog.commitdate), sum(SVNLog.addedfiles), sum(SVNLog.deletedfiles) \
                         from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                         group by date(SVNLog.commitdate)", (self.sqlsearchpath,))
        dates = []
        fc = []
        totalfiles = 0
        for year, month, day, fadded,fdeleted in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            totalfiles = totalfiles + fadded-fdeleted
            fc.append(float(totalfiles))

        return(dates, fc)            

    def getFileTypesStats(self, numTypes):
        '''
        numTypes - number file types to return depending of number of files of that type.
        returns two lists (file types and number of files of that type. 
        '''
        #first get the file types and         
        self.cur.execute("select filetype(changedpath) as ftype, count(*) as typecount\
                         from (select distinct changedpath from SVNLogDetail where SVNLogDetail.changedpath like ? \
                         ) group by ftype order by typecount DESC limit 0,?"
                         , (self.sqlsearchpath,numTypes,))

        ftypelist = []
        ftypecountlist = []
        
        for ftype, typecount in self.cur:
            ftypelist.append(ftype)
            ftypecountlist.append(float(typecount))
        return(ftypelist, ftypecountlist)

    def getAvgLoC(self):
        '''
        get statistics of how average LoC is changing over time.
        returns two lists (dates and average loc on that date)
        '''
        self.cur.execute("select strftime('%Y', SVNLog.commitdate), strftime('%m', SVNLog.commitdate),\
                         strftime('%d', SVNLog.commitdate), sum(SVNLogDetail.linesadded), sum(SVNLogDetail.linesdeleted), \
                         sum(SVNLog.addedfiles), sum(SVNLog.deletedfiles) \
                         from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                         group by date(SVNLog.commitdate)", (self.sqlsearchpath,))
        dates = []
        avgloclist = []
        avgloc = 0
        totalFileCnt = 0
        totalLoc = 0
        for year, month, day, locadded, locdeleted, filesadded, filesdeleted in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            totalLoc = totalLoc + locadded-locdeleted
            totalFileCnt = totalFileCnt + filesadded - filesdeleted
            avgloc = 0.0
            if( totalFileCnt > 0.0):
               avgloc = float(totalLoc)/float(totalFileCnt)
            avgloclist.append(avgloc)
        return(dates, avgloclist)

    def getAuthorActivityStats(self, numAuthors):
        '''
        numAuthors - number authors to return depending on the contribution of authors. 
        returns four lists (authors, percentage of added files, percentage of changed files and percentage of deleted files)
        '''
        self.cur.execute("select SVNLog.author, sum(SVNLog.addedfiles), sum(SVNLog.changedfiles), \
                         sum(SVNLog.deletedfiles), count(SVNLog.revno) as commitcount from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                         group by SVNLog.author order by commitcount DESC LIMIT 0, ?"
                         , (self.sqlsearchpath, numAuthors,))

        authlist = []
        addfraclist = []
        changefraclist=[]
        delfraclist = []
        
        for author, filesadded, fileschanged, filesdeleted,commitcount in self.cur:
            authlist.append(author)
            activitytotal = float(filesadded+fileschanged+filesdeleted)
            
            if( activitytotal > 0.0):
               addfraclist.append(float(filesadded)/activitytotal*100)
               changefraclist.append(float(fileschanged)/activitytotal*100)
               delfraclist.append(float(filesdeleted)/activitytotal*100)
            else:
               addfraclist.append(0.0)
               changefraclist.append(0.0)
               delfraclist.append(0.0)
               
        return(authlist, addfraclist, changefraclist, delfraclist)

    def getDirFileCountStats(self, dirdepth=2):
        '''
        dirdepth - depth of directory search relative to search path. Default value is 2
        returns two lists (directory names upto dirdepth and number of files in that directory (including
        files in subdirectories)        
        '''
        self.cur.execute("select dirname(?, changedpath, ?) as dirpath, count(*) as filecount \
                    from (select distinct changedpath from SVNLogDetail where SVNLogDetail.changedpath like ?) \
                    group by dirpath", (self.searchpath,dirdepth, self.sqlsearchpath,))
            
        dirlist = []
        dirfilecountlist = []        
        for dirname, fcount in self.cur:
            dirlist.append(dirname)
            dirfilecountlist.append(float(fcount))
            
        return(dirlist, dirfilecountlist)

    def getDirLoCStats(self, dirdepth=2):
        '''
        dirdepth - depth of directory search relative to search path. Default value is 2
        returns two lists (directory names upto dirdepth and total line count of files in that directory (including
        files in subdirectories)        
        '''
        self.cur.execute("select dirname(?, SVNLogDetail.changedpath, ?) as dirpath, sum(SVNLogDetail.linesadded), sum(SVNLogDetail.linesdeleted) \
                    from SVNLog, SVNLogDetail \
                    where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                    group by dirpath", (self.searchpath,dirdepth, self.sqlsearchpath,))
            
        dirlist = []
        dirsizelist = []        
        for dirname, linesadded, linesdeleted in self.cur:
            dsize = linesadded-linesdeleted
            if( dsize > 0):
                dirlist.append(dirname)
                dirsizelist.append(dsize)
                
        return(dirlist, dirsizelist)

    def getDirnames(self, dirdepth=2):
        '''
        gets the directory names upto depth (dirdepth) relative to searchpath.
        returns one list of directory names
        '''
        self.cur.execute("select dirname(?, changedpath, ?) as dirpath from SVNLogDetail where changedpath like ? \
                         group by dirpath",(self.searchpath, dirdepth, self.sqlsearchpath,))
        
        dirlist = [dirname for dirname, in self.cur]
        return(dirlist)
    
    def getLoCStats(self):
        '''
        returns two lists (dates and total line count on that date)
        '''
        self.cur.execute("select strftime('%Y', SVNLog.commitdate), strftime('%m', SVNLog.commitdate),\
                         strftime('%d', SVNLog.commitdate), sum(SVNLogDetail.linesadded), sum(SVNLogDetail.linesdeleted) \
                         from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                         group by date(SVNLog.commitdate)", (self.sqlsearchpath,))
        dates = []
        loc = []
        tocalloc = 0
        for year, month, day, locadded, locdeleted in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            tocalloc = tocalloc + locadded-locdeleted
            loc.append(float(tocalloc))
            
        return(dates, loc)
    
    def getChurnStats(self):
        '''
        returns two lists (dates and churn data on that date)
        churn - total number of lines modifed (i.e. lines added + lines deleted + lines changed)
        '''
        self.cur.execute("select strftime('%Y', SVNLog.commitdate), strftime('%m', SVNLog.commitdate),\
                         strftime('%d', SVNLog.commitdate), sum(SVNLogDetail.linesadded+SVNLogDetail.linesdeleted) as churn \
                         from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? \
                         group by date(SVNLog.commitdate)", (self.sqlsearchpath,))
        dates = []
        churnloclist = []
        tocalloc = 0
        for year, month, day, churn in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            churnloclist.append(float(churn))
            
        return(dates, churnloclist)

    def getDirLocTrendStats(self, dirname):
        '''
        gets LoC trend data for directory 'dirname'.
        returns two lists (dates and total LoC at that date) for the directory 'dirname'
        '''
        sqlQuery = "select sum(SVNLogDetail.linesadded), sum(SVNLogDetail.linesdeleted), \
                    strftime('%%Y', SVNLog.commitdate), strftime('%%m', SVNLog.commitdate), strftime('%%d', SVNLog.commitdate) \
                         from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like '%s%%' \
                         group by date(SVNLog.commitdate)" % (dirname)

        self.cur.execute(sqlQuery)
        dates = []
        dirsizelist = []
        dirsize = 0
        for locadded, locdeleted, year, month, day in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            dirsize= dirsize+locadded-locdeleted
            dirsizelist.append(max(0, float(dirsize)))
            
        return(dates, dirsizelist)

    def getAuthorCommitActivityStats(self, author):
        '''
        get the commit activit by hour of day stats for author 'author'
        returns two lists (dates , time at which commits happened on that date) for author.
        '''
        self.cur.execute("select strftime('%H', commitdate), strftime('%Y', SVNLog.commitdate), \
                    strftime('%m', SVNLog.commitdate), strftime('%d', SVNLog.commitdate) \
                    from SVNLog where author=? group by date(commitdate)" ,(author,))

        dates = []
        committimelist = []
        for hr, year, month, day in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            committimelist.append(int(hr))
        return(dates, committimelist)

    def getLoCTrendForAuthor(self, author):
        '''
        get the trend of LoC contributed by the author 'author'
        return two lists (dates and loc on that date) contributed by the author
        '''
        self.cur.execute("select strftime('%Y', SVNLog.commitdate), strftime('%m', SVNLog.commitdate),\
                         strftime('%d', SVNLog.commitdate), sum(SVNLogDetail.linesadded), sum(SVNLogDetail.linesdeleted) \
                         from SVNLog, SVNLogDetail \
                         where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like ? and SVNLog.author=? \
                         group by date(SVNLog.commitdate)",(self.sqlsearchpath, author,))
        dates = []
        loc = []
        tocalloc = 0
        for year, month, day, locadded, locdeleted in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            tocalloc = tocalloc + locadded-locdeleted
            loc.append(float(tocalloc))
            
        return(dates, loc)

    def getBugfixCommitsTrendStats(self):
        '''
        get the trend of bug fix commits over time. Bug fix commit are commit where log message contains words
        like 'bug', 'fix' etc.
        returns three lists (dates, total line count on that date, churn count on that date)
        '''
        sqlquery = "select strftime('%%Y', SVNLog.commitdate), strftime('%%m', SVNLog.commitdate), \
                         strftime('%%d', SVNLog.commitdate), count(*) as commitfilecount \
                         from SVNLog, SVNLogDetail where SVNLog.revno = SVNLogDetail.revno and SVNLogDetail.changedpath like '%s' \
                         and %s group by date(SVNLog.commitdate)" % (self.sqlsearchpath, self.__sqlForbugFixKeywordsInMsg())
        
        self.cur.execute(sqlquery)
        dates = []
        fc = []
        commitchurn = []
        totalcommits = 0
        for year, month, day, commitfilecount in self.cur:
            dates.append(datetime.date(int(year), int(month), int(day)))
            commitchurn.append(float(commitfilecount))
            totalcommits = totalcommits+commitfilecount
            fc.append(float(totalcommits))
        return(dates, fc, commitchurn)