#!/usr/bin/env python3
# -*- encoding:utf-8 -*-

# TODO: import python-apt

import os
import re

import sys

# xml parser
import json
from pprint import pprint

# random tmp dir
import random
import string

# debug switch
DEBUG = 0


def log_print(output):
    if DEBUG:
        pprint(output)


def find_file(start, name):
    """find all file in start
    start: a location, str
    name: str
    """
    deblist = []
    for relpath, dirs, files in os.walk(start):
        for file in files:
            if file.endswith(name):
                filepath = os.path.join(start, relpath, file)
                deblist.append(os.path.normpath(os.path.abspath(filepath)))

    return deblist


def gen_string(length):
    """Create a random string
    length: int
    return str
    """
    randomstring = string.ascii_letters + string.digits
    return ''.join([random.choice(randomstring) for i in range(length)])


def search_deb(searchbase, searchkey):
    """Search a dict
    searchbase: dict
    searchkey: str
    return a source class, or 0 if not found.
    """
    for i in searchbase.keys():
        if searchkey in searchbase[i].debs.keys():
            return searchbase[i]

    return 0


def search_cacheddata(data, name, version):
    """Search the data.json
    searchbase: list
    searchkey: str, str
    return 0 if not found, else the dict.
    """
    for x in data:
        # already existed in cached data.json
        if name == x['name'] and version == x['version']:
            return x
    return 0


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
    # and another
    # -rw-r--r-- root/root     23459 2015-12-10 12:32 ./usr/share/doc/vim-common/changelog.gz
    # -rw-r--r-- root/root     84110 2016-01-25 10:25 ./usr/share/doc/vim-common/changelog.Debian.gz
    # filepath="./usr/share/doc/vim-common/changelog.gz\n./usr/share/doc/vim-common/changelog.Debian.gz"

    # changelog*.gz always in usr/share/doc/
    cmd = "dpkg-deb -c " + debpath + \
        " | grep changelog | grep 'usr/share/doc' | awk '$3!=0{print $6;}'"
    # strip the \n in filepath
    filepath = os.popen(cmd).read().strip().split('\n')
    changelogpath = ''

    if filepath:
        # multi changelog files in filepath
        if len(filepath) > 1:
            for x in filepath:
                if os.path.split(x)[1] == 'changelog.Debian.gz':
                    changelogpath = x
                    break
            # changelog.Debian.gz is not in deb file list
            if not changelogpath:
                for x in filepath:
                    # a file has changelog and Debian may be the right one?
                    if x.find('Debian') != -1:
                        filepath = x
        else:
            changelogpath = filepath[0]
        return changelogpath
    else:
        # deb file doesn't contain a changelog,
        return ''


def get_changelog(debpath, changelogpath, baseversion, updateversion):
    """Get changelogs of package.
    depends on dpkg-deb, zcat, sed.
    debpath: str
    changelogpath: str
    baseversion: str
    updateversion: str
    return changelogs: str
    """
    # create tmp dir
    randomstring = gen_string(10)
    TMPDIR = '/tmp/diffchangelog-' + randomstring

    extractcmd = "dpkg-deb -x " + debpath + " " + TMPDIR

    extractdeb = os.system(extractcmd)
    # extract deb failed?
    if extractdeb != 0:
        log_print("extract deb file failed.")
        return 9

    zcatcmd = "cd " + TMPDIR + " && zcat " + changelogpath

    changelogs = os.popen(zcatcmd).read()

    # clean TMPDIR
    cleancmd = "rm -rf " + TMPDIR
    os.system(cleancmd)

    return changelogs


def diff_changelog(debpath, changelogpath, baseversion, updateversion):
    """Show the diff changelogs of package.
    debpath: str
    changelogpath: str
    baseversion: str
    updateversion: str
    return logdiff: str
    """
    changelogs = get_changelog(
        debpath, changelogpath, baseversion, updateversion)

    # extract deb file failed
    if changelogs == 8:
        return 8
    # changelogs is Null
    elif changelogs == '':
        return 9

    header_re = re.compile(r'.*;.*urgency=.*\n+')

    # changelog[0] is ''
    changelog = header_re.split(changelogs)
    headers = header_re.findall(changelogs)

    logdiff = ''
    # if not found baseversion, most 10 version of changelogs
    changeloglen = 10
    # get the length
    if len(headers) < changeloglen:
        changeloglen = len(headers)
    for x in range(0, changeloglen):
        # version end, diff changelog stop
        if baseversion in headers[x]:
            break
        else:
            logdiff += headers[x] + changelog[x + 1]

    if logdiff:
        return gen_bugzilla_url(logdiff)
    else:
        # changelog diff failed
        return 9


def gen_bugzilla_url(changelogs):
    """Parse the urls to links
    changelogs: str
    return changelogs: str
    TODO: GNOME, LP
    """
    # deepin bugzilla
    # Resolves: https://bugzilla.deepin.io/show_bug.cgi?id=882
    deepinre = re.compile('Resolves: (.*)')
    deepinbugs = re.findall(deepinre, changelogs)
    if deepinbugs:
        for url in deepinbugs:
            changelogs = changelogs.replace(
                url, "<a href=%s>%s</a>" % (url, url))

    # debian bugzilla
    debianre = re.compile('Closes: #(.*)', flags=re.IGNORECASE)
    debianbugs = re.findall(debianre, changelogs)
    if debianbugs:
        numre = re.compile('(\d+)')
        nums = []
        for bugs in debianbugs:
            bugnums = re.findall(numre, bugs)
            for x in bugnums:
                nums.append(x)

        # sometimes same bugs in multi lines:
        # closes: #434558, #434560, #434577, #434560.
        # CLoses: #434577
        nums = set(nums)
        for num in nums:
            changelogs = changelogs.replace(
                num, "<a href=http://bugs.debian.org/%s>%s</a>" % (num, num))

    # cve bugs
    cvere = re.compile('(CVE-\d+-\d+)')
    cvebugs = re.findall(cvere, changelogs)

    if cvebugs:
        for bug in cvebugs:
            changelogs = changelogs.replace(
                bug, "<a href='https://cve.mitre.org/cgi-bin/cvename.cgi?name=%s'>%s</a>" % (bug, bug))

    return changelogs


def get_commitlog(name, oldversion, newversion):
    """Generate commits between old version and newversion
    name: str
    oldversion: str
    newversion: str
    return commitlog: str
    """
    REPODIR = "/home/leaeasy/git-repo/"
    # get all deepin repos
    try:
        allrepos = [f for f in os.listdir(
            REPODIR) if os.path.isdir(os.path.join(REPODIR, f))]
    except:
        # REPODIR not found
        return 9

    # not deepin packages
    if name not in allrepos:
        return 9

    # version example:
    # 3.0.1-1
    # 2:1.18.1-1
    # 10.1.0.5503~a20p2
    versionre = re.compile("(\d:)?([\d.]+).*")
    oldtag = re.findall(versionre, oldversion)[0][1]
    newtag = re.findall(versionre, newversion)[0][1]

    commitcmd = "cd " + REPODIR + name + " && git log --pretty=oneline --abbrev-commit " + \
        oldtag + ".." + newtag + " && cd - >/dev/null"

    commitlog = os.popen(commitcmd).read()

    if commitlog:
        return gen_commit_url(commitlog, name)
    else:
        return 9


def gen_commit_url(data, name):
    urlbase = "https://github.com/linuxdeepin/" + name + "/commit/"
    for x in data.split('\n'):
        commitid = x.split(" ")[0]
        if commitid:
            data = data.replace(
                commitid, "<a href='%s%s'>%s</a>" % (urlbase, commitid, commitid))

    return data


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
                    if (checkdeb.version == sourcelist[checkdeb.source].version) and (sourcelist[checkdeb.source].debs[checkdeb.name].find(checkdeb.arch) == -1):
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
                checkdeb.source,
                checkdeb.name,
                checkdeb.arch,
                checkdeb.version, )
            newsource._update_details(checkdeb)

            sourcelist[newsource.name] = newsource

    return sourcelist


class Package(object):

    """The base package class
    TODO: a more useful way to get the deb information
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
        try:
            installsize = re.search(
                'Installed-Size:.*', self.controlfile).group().replace('Installed-Size: ', '')
            if installsize:
                self.installsize = installsize
            else:
                self.installsize = '0'
        except:
            self.installsize = '0'

        # a failed example:
        # Source: vice (2.4.dfsg+2.4.26-1)
        try:
            source = re.search('Source:.*', self.controlfile)
        except:
            pass
        if source:
            self.source = source.group().split(' ')[1]
        else:
            self.source = self.name


class Source(object):

    """Packages' Source,
    changelog diff depend on this"""

    def __init__(self, name, debname, debarch, version):
        self.name = name
        self.debs = {debname: debarch}
        self.version = version
        self.oldversion = '0'
        self.changelogdiff = ''
        self.debpath = ''
        self.size = '0'
        self.changelogpath = ''
        self.commitlog = ''

    def _set_details(self, debpath, size, changelogpath):
        self.debpath = debpath
        self.size = size
        self.changelogpath = changelogpath

    def _get_diff_changelog(self):
        if self.changelogpath != '':
            logdiff = diff_changelog(
                self.debpath, self.changelogpath,
                self.oldversion, self.version)
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
            self._set_details(
                checkdeb.path, checkdeb.installsize, changelogpath)

    def _set_commit_log(self):
        commitlog = get_commitlog(self.name, self.oldversion, self.version)
        if commitlog == 9:
            # no commit logs in repo dir
            self.commitlog = 'No commit logs found'
        else:
            self.commitlog = commitlog

if __name__ == '__main__':

    """sys.argv[1]: result,json,
       sys.argv[2]: deb search path,
       sys.argv[3]: old data.json, cached file
    """

    if len(sys.argv) > 1:
        versionset = 0
        resultjson = sys.argv[1]

        if len(sys.argv) > 2:
            debpath = sys.argv[2]
        else:
            debpath = "./"

        if len(sys.argv) > 3:
            with open(sys.argv[3], 'r') as f:
                cacheddata = json.load(f)

        deblist = find_file(debpath, '.deb')
        sp = gen_deb(deblist)

        with open(resultjson, 'r') as f:
            data = json.load(f)

        modifytime = data['time']
        jsondetails = data['details']
        rrjson = []
        cachedSourcelist = []

        for debfile in jsondetails:
            # if old data.json has this source, skip it
            if len(sys.argv) > 3:
                cachedSource = search_cacheddata(
                    cacheddata, debfile['name'], debfile['newversion'])
                if cachedSource:
                    # ignore the same source in result.json,  only once
                    if debfile['name'] not in cachedSourcelist:
                        rrjson.append(cachedSource)
                        cachedSourcelist.append(debfile['name'])
                    continue

            # search the Source object
            oldsp = search_deb(sp, debfile['name'])
            if oldsp != 0:
                if debfile['oldversion'] != '0':
                    # source file's old version is right
                    if debfile['arch'] == 'source':
                        sp[debfile['name']].oldversion = debfile['oldversion']
                    else:
                        # no source file found, use deb's oldversion
                        if oldsp.oldversion == '0':
                            oldsp.oldversion = debfile['oldversion']

        for x in sp.keys():
            if len(sys.argv) > 3:
                if x in cachedSourcelist:
                    continue
            sp[x]._get_diff_changelog()
            sp[x]._set_commit_log()

            rrjson.append({'name': x,
                           'deblist': sp[x].debs,
                           'version': sp[x].version,
                           'oldversion': sp[x].oldversion,
                           'changelog': sp[x].changelogdiff,
                           'commitlog': sp[x].commitlog})

            log_print(sp[x].name + " " + sp[x].oldversion)

        with open('data.json', 'w') as f:
            json.dump(rrjson, f)
