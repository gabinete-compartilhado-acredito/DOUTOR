#!/usr/bin/env python
"""
Wrapper of the scheduler (daemon) for running DOU articles capture. It takes as input
a configuration (dict) or a JSON filename containing the configuration.

USAGE:   monitore_dou.py <CONFIG>
EXAMPLE: monitore_dou.py ../configs/capture_DOU_test.json

It is recommended to send output to file and run it in the background, e.g.:
         monitore_dou.py ../configs/capture_DOU_test.json > ../temp/2019-05-25_monitore_dou.log &

The configuration has the keywords:
* "sched_interval": number of minutes between each capture attempt;

* storage_path:     the path to save DOU articles;
* save_articles:    BOOL that tells whether or not to write all articles to database; 
* date_format:      the format of end_date (e.g. %Y-%m-%d);
* end_date:         the last day to search for articles (cat be set to 'now');
* secao:            a list with DOU sections to search immediately;
* secao_all:        a list with all DOU sections that one is interested in searching in the future
                    (1, 2, 3, 'e', '1a'; only relevant for scheduler); 
* timedelta:        the number of days in the pasr from end_date to start the search
                    (a negative number);
* filter_file:      JSON filename that describes the filters to be applied to articles;
* post_articles:    BOOL that tells whether or not to post articles to Slack;
* slack_token:      filename for file containing Slack's authentication token.

Written by Henrique S. Xavier, hsxavier@gmail.com, on 25/jun/2019.
"""

import sys
import lambda_function as lf

# Docstring output:
if len(sys.argv) != 1 + 1:
    print(__doc__)
    sys.exit(0)

# Get input:
config_file = sys.argv[1]

# Call scheduler of DOU's capture:
lf.local_scheduler(config_file)
