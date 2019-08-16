#!/usr/bin/env python
"""
Given a JSON configuration file that specifies the dates and sections 
of the DOU that should be downloaded, filtered and posted to Slack, 
do all that. The configuration file keywords are:

storage_path   > Path to where to save downloaded DOU articles;
date_format    > Formar of 'end_date' below;
end_date       > Date of the last day to download articles (can be set to 'now' for the current date);
secao          > a list of sections to download (maximal list is [1,2,3,'e','1a']);
timedelta      > Number of the days from 'end_date' to download articles (is a negative number);
save_articles  > Boolean (true, false) that specifies if articles should be saved to 'storage_path';
filter_file    > filename (with path) of the file that describes the desired filtering.

USAGE:   capture_dou.py <CONFIG_FILE>
EXAMPLE: capture_dou.py configs/capture_DOU_test.json

Written by Henrique S. Xavier, hsxavier@gmail.com, on 23/jun/2019.
"""

import sys
import capture_driver as cd

# Docstring output:
if len(sys.argv) != 1 + 1:
    print(__doc__)
    sys.exit(0)

# Get input:
config_file = sys.argv[1]

# Call driver of DOU's capture:
next_config = cd.capture_DOU_driver(config_file)

