import requests
from lxml import html
import json
import datetime as dt
import global_settings as gs

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
    return fixed


def brasilia_day():
    """
    No matter where the code is ran, return UTC-3 day
    (Brasilia local day, no daylight savings)
    """
    return (dt.datetime.utcnow() + dt.timedelta(hours=-3)).replace(hour=0, minute=0, second=0, microsecond=0)


def update_config(config, Narticles_in_section):
    """
    Given a config file for capturing DOU articles' URLs and a dict 
    that states how many articles were found in each requested section
    'Narticles_in_section', return an updated config for the next request 
    try. 
    
    Required config keys:
    * end_date    > The articles' date to request the URLs;
    * date_format > The format of the date above (e.g. %Y-%m-%d);
    * secao       > Current list of sections to request URLs;
    * secao_all   > All sections one may want to request (does not update);
    * timedelta   > Current implementation requires this to be 0.
`   * last_extra  > The extra edition number of the last capture.
    """
    
    if config['timedelta'] != 0:
        raise Exception('current implementation only allows timedelta=0.')
    
    # Copy config:
    config2  = dict(config)
    end_date = dt.datetime.strptime(config['end_date'], config['date_format'])
    
    # If end_date is in the future, keep the same config:
    if end_date > brasilia_day():
        return config2
    
    # If end_date is in the past, return next day and all sections:
    if end_date < brasilia_day():
        config2['secao'] = config['secao_all']
        config2['end_date'] = (end_date + dt.timedelta(days=1)).strftime(config['date_format'])
        config2['last_extra'] = 0
        return config2
    
    # PRESENT DAY: find out missing sections and set config to that:
    # PS: always keep Extra ('e') because it can appear at any time 
    section_keys = list(filter(lambda k: Narticles_in_section[k] == 0 or k == 'e', Narticles_in_section.keys()))
    config2['secao'] = section_keys

    # If there are no missing sections, reset sections list and get next day:
    if len(section_keys)==0:
        config2['end_date'] = (end_date + dt.timedelta(days=1)).strftime(config['date_format'])
        config2['secao'] = config['secao_all']
        
    return config2


def get_articles_url(config):
    """
    Get as input a dict 'config' with keys:
    
    * 'date_format': format of 'end_date' below, e.g. '%Y-%m-%d';
    * 'end_date':    last date to search for URLs (one can set to 'now' to get the current day); 
    * 'secao':       list of DOU sections to scan (1, 2, 3, e and/or 1a, or set to 'all' for '[1,2,3,e]';
    * 'timedelta':   number of days from end_date to start URL search (is a negative number);
    
    and creates a list of DOU articles' URLs to download. 
    """
    
    # Hard-coded stuff:
    url_prefix = 'http://www.in.gov.br/web/dou/-/'
    
    # Debug message:
    if True or gs.debug == True:
        print("Starting get_articles_url with config:")
        print(config)
    
    # Translate string representing date to datetime:
    if gs.debug == True:
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
    if gs.debug == True:
        print('Reading selected sections...')    
    secoes = config['secao']
    secoes = [1, 2, 3, 'e', '1a'] if secoes == 'all' else secoes
    secoes = secoes if type(secoes) == list else [secoes]
    secoes = [str(s) for s in secoes]
    
    # LOOP over dates:
    url_file_list = []
    Narticles_in_section = dict(zip(secoes, [0]*len(secoes)))
    start_date = end_date + timedelta
    if gs.debug == True:
        print('Will enter loop over config date and section range:')    
    for date in daterange(start_date, end_date + dt.timedelta(days=1)):
        if gs.debug == True:
            print('-- '+date.strftime('%Y-%m-%d'))
        # LOOP over DOU sections:
        for s in secoes:
            if gs.debug == True:
                print('   -- s'+str(s))
            jsons = get_artigos_do(date, s)
            Narticles_in_section[s] = len(jsons)
            # LOOP over downloaded URL list:
            if gs.debug == True:
                print('      Looping over URLs...')            
            for j in jsons:
                url      = url_prefix + j['urlTitle']
                filename = date.strftime('%Y-%m-%d') + '_s' + str(s) + '_' + fix_filename(j['urlTitle']) + '.json'
                url_file_list.append({'url':url, 'filename':filename})
    
    return url_file_list, update_config(config, Narticles_in_section)


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
