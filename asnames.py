#!/usr/bin/env python

# Script to create a version of cidr-report's AS names file with
# better content for RIPE NCC assigned AS numbers.

# Following a change in RIPE Database policiies, most of the AS
# numbers assigned or maintained by the RIPE NCC no longer have
# useful information in the first 'descr' line in the aut-num object.
# See: https://www.ripe.net/ripe/mail/archives/ncc-announce/2016-June/001051.html
#
# This script restores the old situation by following the references
# to organisation objects and extract the AS holders organisation names
# from there.

import argparse
import calendar
import re
import sys
import urllib2
import zlib


def getGeoffASNs(outfile):
    """Get Geoff Huston's list of AS numbers, names and descriptons
    """
    """ If outfile is defined, copy the original data there
    """

    asns={}

    asnrecord = re.compile("^(\d+)\s+(\S.*)$")

    # Example records from asn.txt, to be matched by above regex:
    #
    # 12833   GIGAPIX GigaPix - Portuguese Internet eXchange, PT
    # 13005   C2INTERNET ******************************************************, GB
    # 13018   , IT


    if outfile:
        o = open(outfile, 'w')

    f=urllib2.urlopen('http://www.cidr-report.org/as2.0/asn.txt')
    for line in f:
        m = asnrecord.match(line)
        if m:
            asns['AS' + m.group(1)]=m.group(2)
        if outfile:
            o.write(line)

    if outfile:
        o.close()

    return(asns)


def getRIPENCCASNs():
    """Get AS numbers and associated country codes of all ASNs allocated by RIPE NCC 
    """

    asns={}
    asnrecord = re.compile("^ripencc\|(\w\w)\|asn\|(\d+)\|(\d+)\|\d+\|a\w+$")
    f=urllib2.urlopen('ftp://ftp.ripe.net/pub/stats/ripencc/delegated-ripencc-latest')
    for line in f:
        m = asnrecord.match(line)
        if m:
            cc = m.group(1)
            asn = m.group(2)
            size = m.group(3)
            for offset in range(0,int(size)):
                autnum = 'AS' + str(int(asn)+offset)
                asns[autnum] = cc
    return(asns)



def process_object(object):
    """Parse a RIPE DB objec, return key/value dictionary

    If a key occurs more than once, only last value will be stored
    This is good enough for the context of this script, as we look at 
    primary and single keys only

    Arguments:
    object: character string with embedded newlines representing the object
    
    Returns:
    dictionary, with each key a list of values  (often just 1)
    """

    dbline = re.compile("(\S+):\s*(\S+.*)$")
    dbline2 = re.compile("(\S+):\s*(\S+.*)$")

    obj = {}
    lastkey = ''
    lines=object.split('\n')
    for line in lines[0:len(lines)-1]:
        key = ''
        z = dbline.match(line)
        if z:
            # lines which do not match are continuation lines
            # we ignore them here, as not applicable to
            # extracting single value items  (name, org, aut-num)
            key = z.group(1) 
            value = z.group(2)
            if not key in obj:
                obj[key] = []
            obj[key] += [ value ]
    return(obj)
    

def getRIPEDBASNs():
    """Get AS number data from RIPE DB aut-num objects
    """

    asns={}
    f=urllib2.urlopen('ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.aut-num.gz')
    decompressed_data=zlib.decompress(f.read(), 16+zlib.MAX_WBITS)
    for object in decompressed_data.split('\n\n'):
        obj = process_object(object)
        if 'aut-num' in obj: 

            status = obj['status'][0]
            if status == 'ASSIGNED' or ( status == 'LEGACY' and
                'RIPE-NCC-LEGACY-MNT' in obj['mnt-by']):

                autnum = obj['aut-num'][0].upper()
                if 'org' in obj:
                    # Only RIPE NCC maintained ASNs with org handle
                    asns[autnum] = {}
                    asns[autnum]['name'] = obj['as-name'][0]
                    org = obj['org'][0]
                    if ' ' in org:
                        # trailing comment could introduce more than one token 
                        org = re.match('^(\S+)\s+.*$',org).group(1)
                    asns[autnum]['org'] = org.upper()
                else:
                        print "no org: in object? -", autnum
        elif object[0] != '#' and object[0] != '%':
            print "no aut-num in object? - >>",object,"<<", obj
    return(asns)


def getRIPEDBOrgNames():
    """Get names and ids of all organisation objects in RIPE DB
    """

    org={}
    f=urllib2.urlopen('ftp://ftp.ripe.net/ripe/dbase/split/ripe.db.organisation.gz')
    decompressed_data=zlib.decompress(f.read(), 16+zlib.MAX_WBITS)
    for object in decompressed_data.split('\n\n'):
        obj = process_object(object)
        if 'organisation' in obj:
            org[obj['organisation'][0].upper()]=obj['org-name'][0]
        elif object[0] != '#':
            print "no organisation? - >>",object,"<<", obj
    return(org)


def main():

    geoffASNs = getGeoffASNs("autnums.orig.txt")
    ripedbASNs = getRIPEDBASNs()
    delegatedASNs = getRIPENCCASNs()
    organisations = getRIPEDBOrgNames()

    new = open('autnums.new.txt','w')
    for asn in sorted(geoffASNs.keys(), key=lambda asn: int(asn[2:len(asn)])):
        if asn in ripedbASNs:
            try:
                cc = delegatedASNs[asn]
            except:
                # RIPE NCC AS, in RIPE DB, but not/no longer in stats?
                # give it country 'ZZ', like Geoff does.
                cc = 'ZZ'
            org = organisations[ripedbASNs[asn]['org']]
            name =  ripedbASNs[asn]['name']
            if name.upper() == 'UNSPECIFIED':
                new.write("%s\t%s, %s\n" % (asn[2:len(asn)], org, cc))
            else:
                new.write("%s\t%s %s, %s\n" % (asn[2:len(asn)], ripedbASNs[asn]['name'], org, cc))
        else: 
            new.write("%s\t%s\n" % (asn[2:len(asn)], geoffASNs[asn]))

    new.close()

main()
