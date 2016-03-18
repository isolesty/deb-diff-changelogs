#!/usr/bin/env python3
#-*- encoding:utf-8 -*-

# TODO: import python-apt

import os
import re

import glob
from fnmatch import fnmatch

# random tmp dir
import random
import string

# debug switch
DEBUG = 1


def log_print(output):
    if DEBUG:
        print(output)


def gen_string(length):
    """Create a random string
    length: int
    return str
    """
    randomstring = string.ascii_letters + string.digits
    return ''.join([random.choice(randomstring) for i in range(length)])


def get_deb_details(debpath):
    """Show the control details of deb file.
    depends on dpkg-deb
    debpath: str
    return: str
    TODO: read one deb file only once
    """
    return os.popen('dpkg-deb -f %s' % debpath).read()


def compare_version(newversion, oldversion):
    """Compare versions, depends on dpkg
    newversion: str
    oldversion: str
    return 1 if newversion is great than oldversion else 0"""
    filelist = os.system(
        'dpkg --compare-versions %s gt %s' % (newversion, oldversion))
    if filelist == 0:
        return 1
    else:
        return 0


def get_changelog_file(debpath):
    """Get a deb's changelog path in deb.
    depends on dpkg-deb, grep, awk.
    debpath: str
    return 1 if deb has changelogs and set pacakge's changelogpath else 0.
    """
    # some deb files contain multi changelog files, only one is useful
    # example:
    # -rw-r--r-- root/root     38974 2016-01-13 23:09 ./usr/share/doc/python3.5/changelog.Debian.gz
    # lrwxrwxrwx root/root         0 2016-01-14 02:55
    # ./usr/share/doc/python3.5/changelog.gz -> NEWS.gz
    cmd = "dpkg-deb -c " + debpath + \
        " | grep changelog  | awk '$3!=0{print $6;}'"
    # strip the \n in filepath
    filepath = os.popen(cmd).read().strip()
    if filepath:
        return filepath
    else:
        # deb file doesn't contain a changelog,
        return ''


def diff_changelog(debpath, changelogpath, baseversion, updateversion):
    """Show the changelogs of package.
    depends on dpkg-deb, zcat, sed.
    debpath: str
    changelogpath: str
    baseversion: str
    updateversion: str
    return diff log: str
    """
    # create tmp dir
    randomstring = gen_string(10)
    TMPDIR = '/tmp/diffchangelog-' + randomstring

    extractcmd = "dpkg-deb -x " + debpath + " " + TMPDIR

    extractdeb = os.system(extractcmd)
    # extrace deb failed?
    if extractdeb != 0:
        log_print("extract deb file failed.")
        return 8

    if baseversion == '0':
        # a new source, no baseversion, show all changlogs
        diffcmd = "cd " + TMPDIR + " && zcat " + changelogpath
    else:
        # diff the changelog after baseversion
        diffcmd = "cd " + TMPDIR + " && zcat " + changelogpath + " | sed -n '/" + \
            updateversion + "/,/" + baseversion + \
            "/p' | grep -v " + baseversion

    logdiff = os.popen(diffcmd).read()

    # clean TMPDIR
    cleancmd = "rm -rf " + TMPDIR
    os.system(cleancmd)

    if logdiff:
        return logdiff
    else:
        # changelog diff failed
        return 9


def gen_deb(deblist):
    """Generate all deb files to source,
    deblist: list
    return source: dict
    """
    sourcelist = {}

    for i in deblist:
        checkdeb = Package(i)
        if checkdeb.source in sourcelist.keys():
            # if the source changelogpath is not set and this deb has a
            # changelog, try to set it
            if sourcelist[checkdeb.source].changelogpath == '':
                sourcelist[checkdeb.source]._update_details(checkdeb)

            if checkdeb.name in sourcelist[checkdeb.source].debs.keys():
                # this is an update version of source
                if compare_version(checkdeb.version, sourcelist[checkdeb.source].version):
                    sourcelist[checkdeb.source].oldversion = sourcelist[
                        checkdeb.source].version
                    sourcelist[checkdeb.source].version = checkdeb.version

                    sourcelist[checkdeb.source].debpath = checkdeb.path
                else:
                    # the same deb name of different arch(such as amd64 and
                    # i386)
                    if (checkdeb.version == sourcelist[checkdeb.source].version) and (checkdeb.arch != sourcelist[checkdeb.source].debs[checkdeb.name]):
                        sourcelist[checkdeb.source].debs[
                            checkdeb.name] += " " + checkdeb.arch
                    # this is an old version of this source
                    else:
                        sourcelist[
                            checkdeb.source].oldversion = checkdeb.version

            else:
                # this is a new deb of this source ,add it to deb list
                sourcelist[checkdeb.source].debs[checkdeb.name] = checkdeb.arch

                # try to extract the smallest deb of every source
                # package.installsize and source.size are string, not number
                if (int(checkdeb.installsize) < int(sourcelist[checkdeb.source].size)):
                    sourcelist[checkdeb.source]._update_details(checkdeb)

        else:
            # add a new source
            newsource = Source(
                checkdeb.source, checkdeb.name, checkdeb.arch, checkdeb.version, )
            newsource._update_details(checkdeb)

            sourcelist[newsource.name] = newsource

    return sourcelist


class Package(object):

    """The base package class
    TODO: a more useful way to get the deb informaiton
    """

    def __init__(self, path):
        self.path = path
        # path=/tmp/ws/1.txt base=/tmp/ws filename=1.txt
        self.base, self.filename = os.path.split(path)
        self.controlfile = get_deb_details(self.path)
        self.name = re.search(
            'Package:.*', self.controlfile).group().replace('Package: ', '')
        self.version = re.search(
            'Version:.*', self.controlfile).group().replace('Version: ', '')
        self.arch = re.search(
            'Architecture:.*', self.controlfile).group().replace('Architecture: ', '')
        self.installsize = re.search(
            'Installed-Size:.*', self.controlfile).group().replace('Installed-Size: ', '')
        source = re.search('Source:.*', self.controlfile)
        if source:
            self.source = source.group().replace('Source: ', '')
        else:
            self.source = self.name


class Source(object):

    """Pacakges' Source,
    changelog diff depend on this"""

    def __init__(self, name, debname, debarch, version):
        self.name = name
        self.debs = {debname: debarch}
        self.version = version
        self.oldversion = '0'
        self.changelogdiff = ''
        self.debpath = ''
        self.size = ''
        self.changelogpath = ''

    def _set_details(self, debpath, size, changelogpath):
        self.debpath = debpath
        self.size = size
        self.changelogpath = changelogpath

    def _get_diff_changelog(self):
        if self.changelogpath != '':
            logdiff = diff_changelog(
                self.debpath, self.changelogpath, self.oldversion, self.version)
            # diff_changelog failed?
            if logdiff != 8 and logdiff != 9:
                self.changelogdiff = logdiff
            elif logdiff == 8:
                self.changelogdiff = 'Extract deb failed.'
            elif logdiff == 9:
                self.changelogdiff = 'No changlog found.'

        else:
            self.changelogdiff = ''

    def _update_details(self, checkdeb):
        changelogpath = get_changelog_file(checkdeb.path)
        if changelogpath != '':
            # this deb has a changelog, use it in source
            self._set_details(checkdeb.path, checkdeb.installsize, changelogpath)



if __name__ == '__main__':

    deblist = [name for name in os.listdir('./') if fnmatch(name, '*.deb')]

    sp = gen_deb(deblist)

    for x in sp.keys():
        sp[x]._get_diff_changelog()
        log_print( sp[x].name  + ": " + sp[x].changelogpath)
        log_print( sp[x].changelogdiff)