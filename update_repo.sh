#/bin/bash
#Created by Drew Bonasera
wget http://mirror.centos.org/centos/filelist.gz || { echo ERROR: Could not wget filelist; exit; }
gunzip filelist.gz
grep "\.rpm" filelist | grep "/os/" > repocache.txt
grep "\.rpm" filelist | grep "/updates/" >> repocache.txt
rm filelist
