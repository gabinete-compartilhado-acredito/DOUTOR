# -*- coding: utf-8 -*-

import requests
from lxml import html
import json
import datetime as dt
import global_settings as gs
import os

if not gs.local:
    import boto3                                  
    from dynamodb_json import json_util as dyjson


def daterange(start_date, end_date):
    """
    Works the same as python's 'range' but for datetime in days.
    As in 'range', the 'end_date' is omitted.
    """
    for n in range(int ((end_date - start_date).days)):
        yield start_date + dt.timedelta(n)


def get_artigos_do(data, secao):
    """
    For a date (datetime) 'data' and a DOU section 'secao', 
    retuns a list of jsons with all links to that day and section's
    articles, along with some metadata.
    
    If no articles exist for a certain date and/or section, 
    if returns an empty list.
    """

    # Hard-coded:
    do_date_format = '%d-%m-%Y'
    url_prefix     = 'http://www.in.gov.br/leiturajornal?data='
    url_sec_sel    = '&secao=do'
    
    # Transforms date to DOU format:
    data_string    = data.strftime(do_date_format)
    
    # Example of URL: 'http://www.in.gov.br/leiturajornal?data=13-05-2019&secao=do1'
    url = url_prefix + data_string + url_sec_sel + str(secao)
    
    # Specifies number of retries for GET:
    session = requests.Session()
    session.mount('http://www.in.gov.br', requests.adapters.HTTPAdapter(max_retries=3))
    
    # Captura a lista de artigos daquele dia e seção:
    res   = session.get(url, timeout=10)
    if res.status_code != 200:
        raise Exception('http GET request failed with code '+str(res.status_code)+'!')
    tree  = html.fromstring(res.content)
    xpath = '//*[@id="params"]/text()'
    return json.loads(tree.xpath(xpath)[0])['jsonArray']


def fix_filename(urlTitle):
    """
    Change the url 'urlTitle' substring used to acess the DOU article to something 
    that can be used as part of a filename.    
    """
    fixed = urlTitle.replace('//', '/')
    fixed = fixed.replace('*', 'xXx')
    return fixed


def build_filename(date, secao, urlTitle, hive_partitioning=False):
    """ 
    Create a filename for the data to be saved on AWS and GCP
    (without the folders).
    
    Input
    -----

    date : datetime
        The date of publication.

    secao : int or str
        The seção (or extra edition) where the publication was made. 
        It can take the values 1, 2, 3, 'e' or '1a'.

    urlTitle : str
        The name of the file on in.gov.br website, without the folders and extension.

    hive_partitioning : bool (default True)
        Whether or not to use BigQuery's hive partitioning structure in the filename
        (e.g. part_data_pub=2020-07-29/part_secao=2/...)
    """

    if hive_partitioning:
        prefix = 'part_data_pub=' + date.strftime('%Y-%m-%d') + '/part_secao=' + str(secao) + '/'
    else:
        prefix = ''
    
    return prefix + date.strftime('%Y-%m-%d') + '_s' + str(secao) + '_' + fix_filename(urlTitle) + '.json'


def brasilia_day():
    """
    No matter where the code is ran, return UTC-3 day
    (Brasilia local day, no daylight savings)
    """
    return (dt.datetime.utcnow() + dt.timedelta(hours=-3)).replace(hour=0, minute=0, second=0, microsecond=0)


def load_captured_urls_aws(table_name):
    """
    Load items from the AWS dynamoDB table `table_name` as entries in a list
    and return list.
    """
    # Pega a referência (pointer) da tabela do dynamo:    
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(table_name)

    # Get all items (following pagination if necessary):
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])
    
    # Format data as a list of URLs:
    url_list = [d['url'] for d in data]
    
    return url_list


def load_captured_urls_local(filename):
    """
    Load lines in the file `filename` as entries in a list
    and return list. Return empty list if file is not found.
    """
    if os.path.isfile(filename) == False:
        return []
    
    with open(filename, 'r') as f:
        return f.read().splitlines()


def load_captured_urls(url_list):
    """
    Load list of urls from local or remote (AWS) source, according to 
    global variable gs.local. `url_list` is string that is either 
    a file path or a DynamoDB table name.
    """
    if gs.local:
        result = load_captured_urls_local(url_list)
    else:
        result = load_captured_urls_aws(url_list)
    return result


def register_captured_url_aws(table_name, url):
    """
    Put the `url` (str) as a new item in AWS DynamoDB table 
    `table_name` (str).
    """
    # Pega a referência (pointer) da tabela do dynamo:    
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(table_name)

    # Escreve os dicionários criados pela função generate_body na tabela do dynamo: 
    with table.batch_writer() as batch:
        batch.put_item(Item={'url': url})
        

def register_captured_url_local(filename, url):
    """
    Append `url` (str) as a new line to the file `filename`.
    """
    with open(filename, 'a') as f:
        f.write(url + '\n')


def register_captured_url(url_list, url):
    """
    Append `url` (str) to `url_list`, which is either 
    a local file or an AWS DynamoDB table (according to 
    global variable gs.local).
    """    
    if gs.local:
        register_captured_url_local(url_list, url)
    else:
        register_captured_url_aws(url_list, url)
    
        
def erase_captured_urls_aws(table_name):
    """
    Erase all items found in DynamoDB table with name 
    `table_name`.
    """
    # Pega a referência (pointer) da tabela do dynamo:    
    dynamodb = boto3.resource('dynamodb')
    table    = dynamodb.Table(table_name)

    # Get all items (following pagination if necessary):
    response = table.scan()
    data = response['Items']
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        data.extend(response['Items'])

    # Delete all items:
    with table.batch_writer() as batch:
        for each in data:
            batch.delete_item(Key=each)


def erase_captured_urls_local(filename):
    """
    Erase the contant of `filename`.
    """
    with open(filename, 'w') as f:
        f.write('')

        
def erase_captured_urls(url_list):
    """
    Erase list of URLs stored in `url_list`, which 
    might be a local filename or a DynamoDB table name
    (according to global variable gs.local).
    """
    if gs.local:
        erase_captured_urls_local(url_list)
    else:
        erase_captured_urls_aws(url_list)

        
def filter_captured_urls(urls_files, url_list_file):
    """
    Given a list of dicts `urls_files` containing URLs and filenames 
    and a list of URLs stored in the file `url_list_file`, 
    return a list of the dicts whose URLs are not listed in the file.
    """
    captured_urls = load_captured_urls(url_list_file)
    
    to_capture = list(filter(lambda d: d['url'] not in captured_urls, urls_files))
    
    return to_capture


def update_config(config, Nurls):
    """
    Given a config file for capturing DOU articles' URLs and the number of
    articles that sgould be downloaded prior to batch size limitations `Nurls`,
    return an updated config for the next request try. 
    
    Required config keys:
    * end_date    > The articles' date to request the URLs;
    * date_format > The format of the date above (e.g. %Y-%m-%d);
    * timedelta   > Current implementation requires this to be 0;
    * url_list    > filename (or DynamoDB table name) where a list of captured URLs is stored;
    * daily_clean_url_list > Whether or not to erase the content of url_list once the current day change.
    """
    
    if config['timedelta'] != 0:
        raise Exception('current implementation only allows timedelta=0.')
    
    # Copy config:
    config2  = dict(config)
    end_date = dt.datetime.strptime(config['end_date'], config['date_format'])

    # Se batemos no limite do batch, prepara para chamar de novo:
    if gs.local == False and Nurls > config['article_batch_size']:
        config2['next_batch'] = True
        return config2
    else:
        config2['next_batch'] = False
        
    
    # If end_date is in the past, return next day and clean captured URLs list (if requested):
    if end_date < brasilia_day():
        if config['daily_clean_url_list'] == True:
            erase_captured_urls(config['url_list'])
        config2['end_date'] = (end_date + dt.timedelta(days=1)).strftime(config['date_format'])
        return config2
            
    return config2


def get_articles_url(config):
    """
    Get as input a dict 'config' with keys:
    
    * 'date_format': format of 'end_date' below, e.g. '%Y-%m-%d';
    * 'end_date':    last date to search for URLs (one can set to 'now' to get the current day); 
    * 'secao':       list of DOU sections to scan (1, 2, 3, e and/or 1a, or set to 'all' for '[1,2,3,e]';
    * 'timedelta':   number of days from end_date to start URL search (is a negative number);
    * 'url_list':    filename or dynamoDB table name of a list of captured URLs (to avoid capturing again).
    * 'daily_clean_url_list': whether or not to erase 'url_list' every day.

    and creates a list of DOU articles' URLs to download. 
    """
    
    # Hard-coded stuff:
    url_prefix = 'http://www.in.gov.br/web/dou/-/'
    
    # Debug message:
    if True or gs.debug:
        print("Starting get_articles_url with config:")
        print(config)
    
    # Translate string representing date to datetime:
    if gs.debug:
        print('Reading date range...')
    if config['end_date'] == 'now':
        end_date = brasilia_day()
    elif config['end_date'] == 'yesterday':
        end_date = brasilia_day() + dt.timedelta(days=-1)
    else:
        end_date = dt.datetime.strptime(config['end_date'], config['date_format'])
    # Save it back to config dict:
    config['end_date'] = end_date.strftime(config['date_format'])
    
    timedelta = dt.timedelta(days=config['timedelta'])
    
    # If end_date is in the future, return empty list and same config
    # (wait for the next day):
    # PS: this will skip request URLs even for negative timedelta.
    if end_date > brasilia_day():
        return [], config
        
    # Translate secao config to a list of strings:
    if gs.debug:
        print('Reading selected sections...')    
    secoes = config['secao']
    secoes = [1, 2, 3, 'e', '1a'] if secoes == 'all' else secoes
    secoes = secoes if type(secoes) == list else [secoes]
    secoes = [str(s) for s in secoes]
    
    # LOOP over dates:
    url_file_list = []
    start_date = end_date + timedelta
    if gs.debug:
        print('Will enter loop over config date and section range:')    
    for date in daterange(start_date, end_date + dt.timedelta(days=1)):
        if gs.debug:
            print('-- '+date.strftime('%Y-%m-%d'))
        # LOOP over DOU sections:
        for s in secoes:
            if gs.debug:
                print('   -- s'+str(s))
            jsons = get_artigos_do(date, s)
            # LOOP over downloaded URL list:
            if gs.debug:
                print('      Looping over URLs...')            
            for j in jsons:
                url      = url_prefix + j['urlTitle']
                filename = build_filename(date, s, j['urlTitle'])
                url_file_list.append({'url':url, 'filename':filename})

    # Filter out already captured articles:
    url_file_list = filter_captured_urls(url_file_list, config['url_list'])
    Nurls         = len(url_file_list)
    
    if gs.local == False:
        # Chop article list to fit into AWS time limit:
        batch_size    = config['article_batch_size']
        url_file_list = url_file_list[:batch_size]
            
    return url_file_list, update_config(config, Nurls)


def load_remote_config():
    """
    Given a hard-coded table reference in dynamoDB (AWS) (see event), 
    loads the configuration for the DOU articles' capture.
    """
    
    # Event for old lambda_handler, tells which data in dynamoDB to load:
    event = {
      "table_name": "capture_urls",
      "key": {
        "name": {
          "S": "executivo-federal-dou"
        },
        "capture_type": {
          "S": "historical"
        }
      }
    }

    # Read json from dynamoDB: 
    client   = boto3.client('dynamodb')
    response = client.get_item(TableName=event['table_name'],  Key=event['key'])
    response = dyjson.loads(response)
    # Get configurations:
    config   = response['Item']['parameters'][0]['params']
    config['bucket'] = response['Item']['bucket']
    config['key']    = response['Item']['key']
    
    return config


def load_local_config(config_file):
    """
    Given a filename 'config_file' for the configuration file for the
    'get_articles_url' function, loads the configuration.
    """
    # Load the configuration:
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    return config
