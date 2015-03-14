Readme for GSoC09 contributions to SVNPlot

# Introduction #

This project contributed code to SVNPlot (http://code.google.com/p/svnplot/) and open source project hosted on Google Code. I (Oscar) was given commiter rights to SVNPlot's SVN repository hosted on Google Code. A new branch (ocastaneda\_gsoc09) was created based on the work and research conducted during GSoC09.

The Python scripts svnsqlite2ora.py and svnsqlite2agora.py convert SVN logs stored in sqlite, and collected through svnlog2sqlite.py, into formats usable by **CMU's ORA tool** ([1](.md)) and **Apache Agora** ([2](.md)). Both scripts take parameters as specified below:

> Usage: svnsqlite2ora.py < sqlitedbpath > < outputfile >

> Usage: svnsqlite2agora.py < sqlitedbpath > < outputfile >

Once the SVN logs have been converted the output files can be used in **CMU's ORA** and **Apache Agora**.

# Quick Start #

1. First generate the sqlite database for your project.

> svnlog2sqlite.py < svnrepo url > < sqlitedbpath >

> <svnrepo url> can be any repository format supported by Subverson. If you are using the local repositories on windows use the [file:///d:/](file:///d:/)... format. < sqlitedbpath > is sqlite database file path. Its a path on your local machine

> You can run this step multiple times. The new revisions added in the repository will get added to datatbase

> Options :
  * -l : Update the changed line count data also. By default line count data is NOT updated.
> NOTE : For versions 0.5.5 (as reported) and up to 0.5.9 (as tested) there was a bug with the -l option. This bug was recently fixed by Nitin Bhide, and adjusted to also work for non-root repository URLs. For more information check the issues list in SVNPlot's Google Code site ([3](.md))

  * -v : Verbose output
  * -g : enable logging of intermediate data and errors. Enable this option if you face any problems like line count not getting generated, no data in the generated sqlite database etc.

2. Now create the output files.

  * svnsqlite2ora.py < sqlitedbpath > < outputfile >

  * svnsqlite2agora.py < sqlitedbpath > < outputfile >

3. Use the output files in **CMU's ORA** or **Apache Agora**.

# Update 4Sep2009 #

Recently Nitin Bhide (the creator of SVNPlot) fixed a bug in SVNPlot which prevented LoC (Lines of Code) counts to be issued when analyzing SVN logs collected with svnlog2sqlite.py. This bug-fix was further modified by Nitin Bhide to also cover non-root SVN repositories (e.g. Apache Incubator projects for which the non-root SVN repo lives at https://svn.(eu).apache.org/repos/asf/incubator/< projectname >). The bug fix was integrated with the changes described in the section below (ie. Options for collecting SVN logs from different dates) so that time period collection can also benefit from this recent bug-fix.

The old version of the files developed during GSoC'09 have been dated with extension 24Aug2009 (date when the GSoC program ended).Therefore, new and updated files have the original names and extensions (ie. those that will be found in the /trunk). Further changes and updates to this branch (ocastaneda\_gsoc09) will be made and announced through separate means (such as a CHANGES file) instead of in this file.

# Options for collecting SVN logs from different dates #

SVNPlot collects SVN logs through svnlog2sqlite.py. This script in turn uses another Python script, svnlogiter.py. Changes can be made to svnlogiter.py to allow collection of SVN logs from different time periods specified through the 'date' of a Revision. This includes specifiying a different date and time for the start and end Revisions of an SVN log being collected. These changes allow specification of time frames for SVN log collection, which can be useful, for instance, when analyzing the evolution of an open source codebase.

For the start Revision, or headrev in svnlogiter.py, the following changes were made to svnlogiter.py:

> headrev = pysvn.Revision( pysvn.opt\_revision\_kind.head)

**was changed to:**

> headrev = pysvn.Revision( pysvn.opt\_revision\_kind.date, calendar.timegm((self.svnrepoyear, self.svnrepomonth, self.svnrepoday, 22,12, 12, 2, 251, 0)) )

This allows specifying the svnrepoyear, svnrepomonth and svnrepoday, followed by a fix time, to a desired value (e.g. 2008-01-01 @ 22.12). The result will be that the Head Revision collected will be that of the date specified. Another way to refer to this is the 'end' Revision, or latter time period of collection.

For the start Revision, or the earlier period of collection, the following changes were made to svnlogiter.py:

> starttime = calendar.timegm((self.svnrepoyear, self.svnrepomonth, 1, 00, 00, 00, 0,0,0))

This will define a starttime for SVN log collection to a date determined by svnrepoyear and svnrepomonth, always on the first day of the month. Further changes can be made along these lines as deemed necessary.

Status in SVNPlot: Currently the changes mentioned above are only implemented by manually changing the code in svnlogiter.py. The plan is to include parameters for these options to make SVNPlot, and more specifically svnlog2sqlite.py, a more flexible tool for collection of SVN logs.

# Acknowledgements #

I thank Google and the Google Open Source Programs Office for the support of this work and my research. I would also like to express my gratitute to Nitin Bhide for his valuable and friendly feedback during my Google Summer of Code (2009) project. Lastly, I would like to thank my MSc thesis supervisors, Prof.dr. Michel van Eeten and Dr. Victor Scholten, for their mentoring and friendship.

_Oscar Castañeda_

_Delft, 2009_


# License #

SVNPlot is released under New BSD License http://www.opensource.org/licenses/bsd-license.php

# References #

[1](.md) http://www.casos.cs.cmu.edu/projects/ora/

[2](.md) http://people.apache.org/~stefano/agora/

[3](.md) http://code.google.com/p/svnplot/