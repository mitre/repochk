# repochk #
repochk is a set of scripts to test if a system has packages with version numbers
different then that of  the official mirrors. This is useful for finding out-of-date
packages, packages with a future version number, and packages which are not
from the official mirror.

## Requirements ##
You will need a system with internet access to update the mirror cache. Nothing
is required to be installed on the system being tested. The following are required
to run the other scripts.

- wget
- gzip
- Python

## Running ##
1. On the machine you wish to check run `getrpms.sh`. This will create `rpmlist.txt`.
This script does not need internet access to run. If you are testing an offline
system you will need to transfer `rpmlist.txt` to a system with internet for the
next steps.
2. Run `update_repo.sh` which will download the CentOS mirror list and output it
to `repocache.txt`.
3. Run `repochk.py`, output prints to the screen

## How it works ##
The latest version string for each package in `repocache.txt` is extracted. Then
each package from `rpmlist.txt` is compared against the latest in the repo.

The version strings to compare are split into sections, they are split on two
characters `-` and `.`. Each section is iterated and converted to an integer if
possible. If both sections are integers then they are compared based on that. If
they aren't integers a string compare is used. If one string has more sections and
they have been equal up to this point, the longer one is considered larger.

## Example ##
```
$ ./repochk.py

           ."""-.
          /      \
          |  _..--'-.
          >.`__.-"";"`
         / /(     ^\
         '-`)     =|-.
          /`--.'--'   \ .-.
        .'`-._ `.\    | J /
       /      `--.|   \__/



Outdated Packages:
Package Name | Arch   | Installed Version      | Latest Mirror Version
-------------+--------+------------------------+-----------------------
kernel       | x86_64 | 2.6.32-431             | 2.6.32-431.20.3
openldap     | x86_64 | 2.4.23-32.el6_4.1      | 2.4.23-34.el6_5.1
initscripts  | x86_64 | 9.03.40-2.el6.centos.2 | 9.03.40-2.el6.centos.3
postfix      | x86_64 | 2.6.6-2.2              | 2.6.6-6


Packages newer than mirror:
Package Name | Arch   | Installed Version | Latest Mirror Version
-------------+--------+-------------------+----------------------
acl          | x86_64 | 3.2.49-6          | 2.2.49-6


Packages not in official mirror:
Package Name                 | Arch    | Installed Version
-----------------------------+---------+------------------
gpg-pubkey-0608b895-4bd22942 | Unknown | Unknown
tmux                         | x86_64  | 1.6-3
epel-release                 | noarch  | 6-8
python-pip                   | noarch  | 1.3.1-4
```