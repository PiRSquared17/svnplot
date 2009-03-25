'''
setup.py
Copyright (C) 2009 Nitin Bhide (nitinbhide@gmail.com)

This module is part of SVNPlot (http://code.google.com/p/svnplot) and is released under
the New BSD License: http://www.opensource.org/licenses/bsd-license.php
--------------------------------------------------------------------------------------
Setup file for installing svnplot
'''

from distutils.core import setup

setup(name='SVNPlot', version ='0.5',
      description='python module to generate graphs and statistics from Subversion repository data',
      author='Nitin Bhide',
      author_email='nitinbhide@gmail.com',
      url='http://code.google.com/p/svnplot',
      py_modules=['matplotlib', 'numpy'],
      packages=['svnplot']
     )