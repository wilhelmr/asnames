# asnames
Python script to amend AS name data from potaroo.net with
organisation names from the RIPE database

Following a change in RIPE Database policies in 2016, most of the AS
numbers assigned or maintained by the RIPE NCC no longer have information
related to the holder/usage of the AS in the descr lines of the aut-num object.

See: https://www.ripe.net/ripe/mail/archives/ncc-announce/2016-June/001051.html

This script restores the old behaviour as it follows the references
to organisation objects and from those extracts the AS holders' organisation names.

