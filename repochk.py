#!/bin/env python
from __future__ import division, absolute_import, with_statement, print_function, unicode_literals
import re
import sys

__author__ = 'Drew Bonasera'
__license__ = 'MIT'

PACKAGERE1 = re.compile('([^\s]+?)[-]+([\d].[\d\.-]+)(?:\.el\d(?:_\d+)?)*\.([^\.]+)(?:\.rpm|$)')
PACKAGERE2 = re.compile('([^\s]+?)[-]+(\d[\w\d\.-]+?)(?:\.el\d(?:_\d+)?)*\.([^\.]+)(?:\.rpm|$)')


def pprinttable(rows, headers):
    lens = []
    for i in range(len(rows[0])):
        lens.append(len(max([x[i] for x in rows] + [headers[i]],key=lambda x:len(str(x)))))
    formats = []
    hformats = []
    for i in range(len(rows[0])):
        if isinstance(rows[0][i], int):
            formats.append("%%%dd" % lens[i])
        else:
            formats.append("%%-%ds" % lens[i])
        hformats.append("%%-%ds" % lens[i])
    pattern = " | ".join(formats)
    hpattern = " | ".join(hformats)
    separator = "-+-".join(['-' * n for n in lens])
    print(hpattern % tuple(headers))
    print(separator)
    for line in rows:
        print(pattern % tuple(line))


def strip_nl(string):
    return string.replace('\r', '').replace('\n', '')


def version_compare(x, y):
    """Compares version strings x and y

    Return 1 if x is greater
    Return -1 if y greater
    Return 0 if equal"""
    # Based on https://fedoraproject.org/wiki/Archive:Tools/RPM/VersionComparison

    # Turn x and y into a list
    x = re.findall('([a-zA-Z]+|[0-9]+)', x)
    y = re.findall('([a-zA-Z]+|[0-9]+)', y)

    # Find longest list
    if len(x) > len(y):
        maxlen = len(x)
    else:
        maxlen = len(y)

    for i in range (0, maxlen):
        #The longer version string is considered to be larger
        try: xval = x[i]
        except: return -1
        try: yval = y[i]
        except: return 1

        #Try and covert subsections to ints
        try:
            a = int(xval)
            b = int(yval)
            xval = a
            yval = b
        except ValueError:
            pass

        if xval > yval:
            return 1
        if yval > xval:
            return -1

    return 0


def parse_repo_cache(filename, version=None, arch=None):
    repo_info = {}
    with open(filename, 'r') as repocache:
        for line in repocache:
            line = strip_nl(line)
            if line.endswith('.rpm'):
                splitline = line.split('/')
                # Check to make sure the major version matches
                major_ver = int(splitline[1].split('.')[0])
                if version is None or major_ver == version:
                    # The architecture of the os
                    osarch = splitline[3]
                    if arch is None or osarch == arch:
                        # Apply the RE to the package name
                        reg = re.match(PACKAGERE1, splitline[5])
                        if not reg:
                            reg = re.match(PACKAGERE2, splitline[5])
                            if not reg:
                                print('WARNING: Did not match REs -', splitline[5], file=sys.stderr)
                                continue
                        package_name, package_version, package_arch = reg.groups()

                        # Make sure all the data structures are in place
                        if major_ver not in repo_info:
                            repo_info[major_ver] = {}
                        if osarch not in repo_info[major_ver]:
                            repo_info[major_ver][osarch] = {}
                        if package_arch not in repo_info[major_ver][osarch]:
                            repo_info[major_ver][osarch][package_arch] = {}
                        # If package is not there just add it
                        if package_name not in repo_info[major_ver][osarch][package_arch]:
                            repo_info[major_ver][osarch][package_arch][package_name] = package_version
                        else:
                            # Check if new version number is greater
                            if version_compare(package_version, repo_info[major_ver][osarch][package_arch][package_name]) > 0:
                                repo_info[major_ver][osarch][package_arch][package_name] = package_version
                else:
                    continue

    return repo_info


def parse_rpm_list(filename):
    data = {'hostname': None, 'arch': None, 'ver': None, 'rpms': {}, 'misc-rpms': []}
    with open(filename, 'r') as fh:
        # Check if first line is metadata
        line = strip_nl(fh.readline()).split(' ')
        if len(line) > 2:
            data['hostname'] = line[0]
            data['arch'] = line[1]
            data['ver'] = ' '.join(line[2:])
        else:
            fh.seek(0)

        # Parse packages
        for line in fh:
            line = strip_nl(line)
            reg = re.match(PACKAGERE1, line)
            if not reg:
                reg = re.match(PACKAGERE2, line)
                if not reg:
                    data['misc-rpms'].append((line, 'Unknown', 'Unknown'))
                    continue
            package_name, package_version, package_arch = reg.groups()

            if package_arch not in data['rpms']:
                data['rpms'][package_arch] = {}
            data['rpms'][package_arch][package_name] = package_version

    return data


def compare_data(repo_cache, rpm_list):
    outdated_list = []
    unoffical_list = rpm_list['misc-rpms']
    newer_list = []

    # Try to get major version
    reg = re.match('[a-zA-Z ]+ (\d+)[\. ].*', rpm_list['ver'])
    if reg:
        os_ver = int(reg.groups()[0])
    else:
        print('ERROR: Unable to find OS version number, assuming 6', file=sys.stderr)
        os_ver = 6

    os_arch = rpm_list['arch']
    if os_arch is None:
        print('WARNING: OS architecture was not found, assuming x86_64', file=sys.stderr)
        os_arch = 'x86_64'

    for package_arch in rpm_list['rpms']:
        for package_name in rpm_list['rpms'][package_arch]:
            # If os_arch is not in the repo cache
            if package_arch not in repo_cache[os_ver][os_arch]:
                unoffical_list.append((package_name, package_arch, rpm_list['rpms'][package_arch][package_name]))
                continue
            # If the package name is not in the repo cache
            if package_name not in repo_cache[os_ver][os_arch][package_arch]:
                unoffical_list.append((package_name, package_arch, rpm_list['rpms'][package_arch][package_name]))
                continue

            ret = version_compare(rpm_list['rpms'][package_arch][package_name], repo_cache[os_ver][os_arch][package_arch][package_name])
            # If versions are equal
            if ret == 0:
                continue
            # If installed is newer
            if ret == 1:
                newer_list.append((package_name, package_arch, rpm_list['rpms'][package_arch][package_name], repo_cache[os_ver][os_arch][package_arch][package_name]))
                continue
            # If out of date
            if ret == -1:
                outdated_list.append((package_name, package_arch, rpm_list['rpms'][package_arch][package_name], repo_cache[os_ver][os_arch][package_arch][package_name]))
                continue
    return outdated_list, unoffical_list, newer_list


def _parse_args():
    import argparse
    parser = argparse.ArgumentParser(description="Checks a list of RPMs against the main mirror to look for updates")
    parser.add_argument('-r','--rpmlist', help="The results of getrpms.sh", required=False, metavar="rpmlist.txt", default='rpmlist.txt')
    parser.add_argument('-c','--repocache', help="The results of update_repo.sh", required=False, metavar="repocache.txt", default='repocache.txt')
    return parser.parse_args()


def _main():
    args = _parse_args()
    print('\n           ."""-.\n          /      \\\n          |  _..--\'-.\n          >.`__.-"";"`\n         / /(     ^\\\n         \'-`)     =|-.\n          /`--.\'--\'   \\ .-.\n        .\'`-._ `.\\    | J /\n       /      `--.|   \\__/\n')

    repo_cache = parse_repo_cache(args.repocache)
    rpm_list = parse_rpm_list(args.rpmlist)
    outdated_list, unoffical_list, newer_list = compare_data(repo_cache, rpm_list)

    if outdated_list:
        print('\n\nOutdated Packages:')
        pprinttable(outdated_list, ['Package Name', 'Arch', 'Installed Version', 'Latest Mirror Version'])
    if newer_list:
        print('\n\nPackages newer than mirror:')
        pprinttable(newer_list, ['Package Name', 'Arch', 'Installed Version', 'Latest Mirror Version'])
    if unoffical_list:
        print('\n\nPackages not in official mirror:')
        pprinttable(unoffical_list, ['Package Name', 'Arch', 'Installed Version'])

if __name__ == '__main__':
    _main()
