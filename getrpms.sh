#/bin/bash
#Created by Drew Bonasera
echo `hostname` `uname -m` `cat /etc/redhat-release` > rpmlist.txt
rpm -qa | sort >> rpmlist.txt
