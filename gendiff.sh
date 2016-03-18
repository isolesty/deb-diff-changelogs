#!/bin/bash

TMPDIR=/tmp/diff-deb-$(date +%Y-%m-%d~%H%M%S)
trap clean exit
clean(){
	if [ -d ${TMPDIR} ]; then
		rm -rf ${TMPDIR}
	fi
}


update_deb=$1
base_deb=$2


base_deb_cfile=$(dpkg-deb -f ${base_deb})
base_deb_source=$(dpkg-deb -f ${base_deb} | grep 'Source:' | awk '{print $2};')
base_deb_version=$(dpkg-deb -f ${base_deb} | grep 'Version:' | awk '{print $2};')


update_deb_cfile=$(dpkg-deb -f ${update_deb})
update_deb_source=$(dpkg-deb -f ${update_deb} | grep 'Source:' | awk '{print $2};')
update_deb_version=$(dpkg-deb -f ${update_deb} | grep 'Version:' | awk '{print $2};')

if [ ${base_deb_source} == ${update_deb_source} ]; then
	echo "Y"
	update_deb_changelog=$(dpkg-deb -c ${update_deb} | grep changelog | awk '{print $6}')

	if [ x${update_deb_changelog} == 'x' ]; then
		echo "no changelog found."
		exit 1
	fi
	mkdir ${TMPDIR} && 	dpkg-deb -x ${update_deb} ${TMPDIR} && cd ${TMPDIR}
	if [ -f ${update_deb_changelog} ]; then
		changelog_diff=$(zcat ${update_deb_changelog} | sed -n "/${update_deb_version}/,/${base_deb_version}/p" | grep -v ${base_deb_version})
		echo -e ${changelog_diff}
	else
		echo "no changelog found after extract ${update_deb}."
		exit 2
	fi
fi