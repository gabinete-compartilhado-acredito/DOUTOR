#!/usr/bin/env python

"""
Download gabi DOU filters from Google Bigquery (that actually are stored as a Sheet in
Google drive) to the file given as this script's input.

USAGE:   download_gabi_dou_filters.py <OUTFILE>
EXAMPLE: download_gabi_dou_filters.py ../filters/all_dou_filters.json

Written by Henrique S. Xavier, hsxavier@gmail.com, on 21/jun/2019.
"""

import filter_articles as fa
import json
import sys

# Docstring output:
if len(sys.argv) != 1 + 1:
    print (__doc__)
    sys.exit(0)

# Get input:
outfile = sys.argv[1]

# Download filters:
print('Downloading filters...')
filters = fa.query_bigquery("SELECT * FROM `gabinete-compartilhado.gabi_bot.gabi_filters` WHERE casa = 'dou'")

# Save to file:
print('Saving it to '+outfile+'...')
with open(outfile, 'w') as f:
    json.dump(filters, f, ensure_ascii=False, indent=1)
