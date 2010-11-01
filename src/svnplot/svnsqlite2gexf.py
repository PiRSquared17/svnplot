'''
svnsqlite2gexf.py
Copyright (C) 2010 Oscar Castaneda (oscar.castaneda@gmail.com)

This module is part of SVNPlot (http://code.google.com/p/svnplot) and is released under
the New BSD License: http://www.opensource.org/licenses/bsd-license.php
--------------------------------------------------------------------------------------

python script to process a Subversion log collected by svnlog2sqlite.py, which is stored in a 
sqlite database. The idea is to use the SQLite database generated by SVNPlot to create the XML 
input file for the open source Gephi, an interactive visualization and exploration platform for 
all kinds of networks and complex systems, dynamic and hierarchical graphs. Using Gephi several 
SNA graphs and analyses may be conducted and, since Gephi is open source, possibly extended.

Note: This is version of svnsqlite2gexf.py was inspired by Apache Agora. It considers commits 
as part of conversations (like email conversations in Apache Agora). Upon committing code, a 
committer creates a revision in SVN which in turn creates a link to all committers who have 
co-authored the corresponding files from that revision. The idea is the same as in Agora, namely 
to create links based on reply actions, but differs in that there is no one originator but instead 
links are created to all co-authors who are active in the sqlite db contents.

This version of svnsqlite2gexf.py has been tested with SVNPlot version 0.6.1 .
'''
from __future__ import with_statement
import string
import sqlite3
import math
import logging
from os.path import splitext

from optparse import OptionParser
from numpy import *
from numpy import matrix


class SVNSqlite2Gephi:
    def __init__(self, sqlitedbpath, outputfilepath):
        self.dbpath = sqlitedbpath
        self.dbcon = None
        self.outputfile = outputfilepath
        
    def initdb(self):
        self.closedb()
        self.revisions = dict()         
        self.committers = dict()
        
        self.dbcon = sqlite3.connect(self.dbpath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    
    def closedb(self):
        if( self.dbcon):
            self.dbcon.close()
            self.dbcon=None

    def __processAuthorNodes(self, output):
        # We create a cursor for SVNLog and do a SELECT on all records (*), so cur = SVNLog
        cur = self.dbcon.cursor()
        # We go through all the committers and their revisions, then we create lists of both.
        cur.execute('SELECT * FROM SVNLog')
        
        # Write XML specification for Gephi network, then start writing <nodes> section of the XML file consisting of nodes
        output.write("\t\t<nodes>\n")
        
        for row in cur:             
            committer = row[2]
            if( committer== '' or committer == None):
                committer = 'Unknown'
            revno = row[0]
    
            # If committer has not been counted then add him/her to the list, and increment committer_count
            # then write <node id> in XML file.
            if (committer not in self.committers):
                committer_id = len(self.committers)
                self.committers[committer] = committer_id
                output.write('\t\t\t<node id="%d" label="%s"/>\n' %(committer_id,committer))
            
            # If a revision has not been counted then add it to the list, increment revision_count and 
            # associate revision to committer.
            if (revno not in self.revisions):
                self.revisions[revno] = committer
                
        # Finish the <nodes> section, and start the <edges> section
        # of the Gephi XML file.
        output.write("\t\t</nodes>\n")
                        
        cur.close()
        
    def __processAuthorEdges(self, output):
        committer_count = len(self.committers)
                
        # Create a matrix of committers with the dimensions we found out previously.
        mat = array([[0]*committer_count]*committer_count)
    
        ############################################################################
        # Write sociomatrix from                                                   #
        # Agent x Resource(changedpathid) and Resource(changedpathid) x Agent      #
        ############################################################################
        cur = self.dbcon.cursor()
        cur.execute('SELECT * FROM SVNPaths')
                
        for row in cur:
            print 'processing %s' % row[1].encode('utf-8')
            changedpathid = row[0]

            #ignore the line count for tagged version of directories. This will have huge line count            
            cur2 = self.dbcon.cursor()
            cur2.execute('SELECT SVNLogDetail.changedpathid , SVNLog.author, SVNLogDetail.linesadded FROM SVNLog, SVNLogDetail \
                where SVNLogDetail.changedpathid=? and SVNLog.revno=SVNLogDetail.revno and SVNLogDetail.copyfrompathid ISNULL and SVNLogDetail.linesadded > 0 \
                order by SVNLogDetail.revno asc',(changedpathid,))
    
            # Iterate over all authors that worked on file
            authList = set()
            for row2 in cur2:
                
                committer_id = self.committers[row2[1]]
                
                # Iterate over the revision entries to get the work contentsfrom them, namely lines-of-code (loc).
                
                # Note: We only take into account lines added (row3[6]) and not lines deleted
                # because we are interested in what committers 'do' and that is more evident from
                # the loc they add, and not so from the loc they delete. Furthermore, negative links
                # between developers are meaningless. 
                loc = row2[2]
                
                for coauthor_id in authList:
                    # As mentioned, we only consider the lines of code that have been added by a committer.                         
                    # And create links to all previous committers who have revised this same
                    # file, ie. file co-authorship.                    
                    mat[committer_id][coauthor_id] = mat[committer_id][coauthor_id] + loc
                authList.add(committer_id)
                
        cur2.close()
        cur.close()
        
        output.write("\t\t<edges>\n")       
        # We iterate over the resulting matrix to write it out to the XML file.
        edge_id = 0
        for auth1, auth1_id in self.committers.iteritems():
            for auth2, auth2_id in self.committers.iteritems():
                wt = mat[auth1_id][auth2_id]
                if( wt > 1 and auth1_id != auth2_id):
                    output.write('\t\t\t<edge id="%d" source="%d" target="%d" weight="%.4f"/>\n'
                                 % (edge_id, auth1_id, auth2_id,wt))
                    edge_id = edge_id+1                 
                    
        output.write("\t\t</edges>\n")

    def __ProcessAuthorGraph(self):
        '''
        output the author->author relationship graph
        '''
        outfilename = self.outputfile + '_authorgraph.gexf'
        with open(outfilename, 'w') as output:
            print "Processing..."
                        
            # Write XML prelude to CMU node specification
                #output.write("<?xml version=\"1.0\" standalone=\"yes\"?>\n")
                #output.write("<DynamicMetaNetwork id=\"Meta Network\">\n")
        
            # Write XML prelude to Gephi node specification
            output.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            output.write("  <gexf xmlns=\"http://www.gexf.net/1.1draft\"\n")
            output.write("  xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n")
            output.write("  xsi:schemaLocation=\"http://www.gexf.net/1.1draft http://www.gexf.net/1.1draft/gexf.xsd\"\n")
            output.write("  version=\"1.1\">\n")
            output.write("  <graph defaultedgetype=\"directed\">\n")
        
            self.__processAuthorNodes(output)
            self.__processAuthorEdges(output)
            
            output.write("\t</graph>\n")
            output.write("</gexf>\n")            

    def Process(self):
        try:
            self.initdb()
            self.__ProcessAuthorGraph()            
        except:
            logging.exception("Error while processing the sqlite log")
            pass        
        finally:
            self.closedb()
        
def __getOutputFileName(outputfilepath):
    '''
    extract the outputfile name without the 'extension' but with full directory path.
    '''
    outputfilepath, ext = splitext(outputfilepath)
    return(outputfilepath)
    
def RunMain():
    usage = "(File co-authorship version) usage: %prog <sqlitedbpath> <outputfile>"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    
    if( len(args) < 2):
        print "Invalid number of arguments. Use svnsqlite2gexf.py --help to see the details."
    else:
        sqlitedbpath = args[0]
        outputfilepath = args[1]
        outputfilepath = __getOutputFileName(outputfilepath)

        logfilename = outputfilepath+'.log'     
        logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=logfilename,
                    filemode='w')

        print "Processing the sqlite subversion log"        
        sqlite2gephi = SVNSqlite2Gephi(sqlitedbpath, outputfilepath)
        sqlite2gephi.Process()
        
if( __name__ == "__main__"):
    RunMain()
