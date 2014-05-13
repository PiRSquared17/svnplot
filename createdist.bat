@echo off
REM Creating binrary and source distribution of SVNPlot
del /s /q build\*
echo "Creating SVNPlot source distribution in zip format"
python setup.py sdist --formats=zip
echo "Creating Windows installer for SVNPlot"
python setup.py bdist_wininst
