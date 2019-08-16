import json
import global_settings as gs
from collections import defaultdict

def query_bigquery(query):
    import boto3
    import google.auth
    from google.cloud import bigquery
    """
    Runs a query in Google BigQuery and returns the result as a list of dicts
    (each line is an element in the list, and each column is an entry in the dict,
    with column names as keys).
    """ 
    # Get & set Google credentials to fetch filters from BigQuery:
    s3 = boto3.client('s3')
    a = s3.get_object(
                      Bucket='config-lambda', 
                      Key='layers/google-cloud-storage/gabinete-compartilhado.json')
    open('/tmp/key.json', 'w').write(a['Body'].read().decode('utf-8'))
    if gs.local:
        # Must set this environment variable:
        import os
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = "/tmp/key.json"
    
    # Create credentials with Drive & BigQuery API scopes
    # Both APIs must be enabled for your project before running this code
    credentials, project = google.auth.default(scopes=[
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/bigquery',
    ])
    
    # Run the query:
    bq = bigquery.Client(credentials=credentials, project=project)
    result = bq.query(query, location="US") # Location must match that of the dataset(s) referenced in the query.
    # Translate the query result into a list of dicts:
    result = [dict(r.items()) for r in result] 
    
    return result


def load_remote_filters():
    """
    Loads filters from Google BigQuery, with a hard-coded query.
    """
    filters_raw = query_bigquery("SELECT * FROM `gabinete-compartilhado.gabi_bot.gabi_filters` WHERE casa = 'dou'")
    return filters_raw


def load_local_filters(filter_path):
    """
    Given a .json file of a set of filters in 'filter_path', 
    loads it to a list of dicts (each line is an element in the list, 
    and each column is an entry in the dict, with column names as keys).
    """
    with open(filter_path, 'r') as f:
        filters_raw = json.load(f)
    return filters_raw


def csvrow_to_list(csvrow):
    """
    Takes a string 'csvrow' that has substrings separated by semicolons and 
    returns a list of substrings.
    """
    if csvrow != None:
        return list(map(lambda s: s.strip(), csvrow.split(';')))
    else:
        return None

    
def check_for_ambiguity(filter_group, filter_ids, key):
    """
    Check if all filters numbered the same way have the same tag 'key'
    (nome, casa, channel, description). Returns an error if it 
    doesn't. This is needed to group filters under the same 
    filter set.
    -- filter_group: pandas grouby object, grouped by filter number.
    -- key: nome, casa, channel, description
    """
    unique_key = all([[f[key] == filter_group[i][0][key] for f in filter_group[i]] for i in filter_ids])
    if not unique_key:
        raise Exception('Found multiple entries of \''+key+'\' for same filter.')

        
def get_filter_par(filter_group, filter_ids, key):
    """
    Given a pandas groupby object 'filter_group' that group the 
    filters by filter_number (giving a filter set) and a key, 
    get the first value for that key in each group.
    """
    return [filter_group[i][0][key] for i in filter_ids]


def filterset_gen(filters_raw, fnumber):
    """
    Group all filters in table 'filter_raw' in a filter set according to filter_number 'fnumber'.
    Then, transforms comma separated filter keywords into a list.
    It also deals with missing values in filter entries / filter entry at all.
    """
    # If there is no filter, return an empty list:
    flist = [f for f in filters_raw if f['filter_number'] == fnumber]
    if len(flist) == 1 and flist[0]['column_name'] == None:
            return []
    else:
        # If there are filters, group them:
        return [{k:(f[k] if k=='column_name' else csvrow_to_list(f[k])) 
                 for k in ('column_name', 'positive_filter', 'negative_filter') if f[k]!=None} 
                for f in filters_raw if f['filter_number'] == fnumber]


def format_filters(filters_raw):
    """
    Format the filters loaded from Google sheets (a table 'filters_raw')
    into the dict used by João Carabetta:
    """
    # Group list of filters by filter_number, to form a filter set:
    filter_group = defaultdict(list)
    for f in filters_raw:
        filter_group[f['filter_number']].append(f)
    # Get filter set ids:
    filter_ids = list(filter_group.keys())
    # List of filter set tags:
    filter_id_keys = ['nome', 'casa', 'channel', 'description']

    # Check if every filter set has unique tags:
    dump = [check_for_ambiguity(filter_group, filter_ids, key) for key in filter_id_keys]
    # Get filter set tags:
    filter_tag = {key: get_filter_par(filter_group, filter_ids, key) for key in filter_id_keys}

    # Organize filters in a filter set:
    filter_set = [filterset_gen(filters_raw, fnumber) for fnumber in filter_ids]

    # Put all filter sets (with tags) into a list:
    event = [{'nome': filter_tag['nome'][i], 
              'casa': filter_tag['casa'][i],
              'media': {'type': 'slack', 
                        'channel': filter_tag['channel'][i],
                        'description': filter_tag['description'][i]},
              #'sns-topic': 'slack-test-DEV', # For debugging.
              'sns-topic': 'slack-test',
              'filters': filter_set[i]} 
             for i in range(len(filter_ids))]
    
    return event


# Functions for finding out if filter over the field 'secao' will eliminate the
# entirity of the downloaded articles, according to config['secao']:

def build_article_set(secao_list):
    """
    Takes the value of 'secao' key in a 'config' dict ('secao_list') that
    specifies which DOU sections to download and return a set of all possible 
    sections that might be downloaded: (sections 1, 2 and 3 from ordinary, 
    extra or sumplement editions).
    """
    # First select ordinary sections:
    sel_set = [str(s) for s in secao_list if str(s) in ['1', '2', '3']]
    # Then select all sections that might appear in an extra edition:
    sel_set = sel_set + ['1e', '2e', '3e'] if 'e'  in secao_list else sel_set
    # Then select all sections that might appear in an suplement edition (maybe it is just 1):
    sel_set = sel_set + ['1a', '2a', '3a'] if '1a' in secao_list else sel_set
    return set(sel_set)


def std_secao_filter(secao_list):
    """
    Takes a words list from a secao filter and standardize the words to the 
    same pattern as the one used to download the articles' URLs:
    extra -> e and suplemento -> a.
    """
    return [str(s).lower().replace('extra','e').replace('suplemento','a') for s in secao_list]


def build_filter_set(secao_pos, secao_neg):
    """
    Create a set of articles that would be accepted by the section's 
    positive and negative filters 'secao_pos' and 'secao_neg', that is:
    keep only the articles that have words in secao field that appear in 
    'secao_pos' and that do not have words that appear in 'secao_neg'.
    """
    secao_pos = std_secao_filter(secao_pos)
    secao_neg = std_secao_filter(secao_neg)
    # A filter will, in principle, select all sections and editions:
    sel_set = ['1','2','3','1e','2e','3e','1a','2a','3a']
    # Only keep items that appear in the positive_filter list:
    sel_set = [s for s in sel_set if len(set(s) & set(secao_pos)) != 0] if len(secao_pos)>0 else sel_set
    # Only keep items that do not appear in the negative_filter list:
    sel_set = [s for s in sel_set if len(set(s) & set(secao_neg)) == 0] if len(secao_neg)>0 else sel_set
    return set(sel_set)


def remaining_sections(secao_set, secao_pos, secao_neg):
    """
    Given a list of DOU sections to download 'secao_list' (e.g. 
    ['1','1e','2','2e']) and a positive and negative list of secao 
    filters to apply ('secao_pos' and 'secao_neg'), returns the 
    remaining sections after filtering.
    """
    will_select_set = build_filter_set(secao_pos, secao_neg)
    return secao_set & will_select_set


def secao_left(config_secao, bot_info):
    """
    Given a list of DOU sections to download, e.g. config['secao'] = [1,2,3,'e','1a'] 
    and a bot_info, return a set of sections/editions that will remain after applying 
    the bot_info's filters on secao.
    """    
    # Select all secao filters in bot_info:
    secao_filters = [{'positive_filter': defaultdict(lambda: [], d)['positive_filter'],
                      'negative_filter': defaultdict(lambda: [], d)['negative_filter']} 
                     for d in bot_info['filters'] if d['column_name']=='secao']
    
    # Transform the secao list in config['secao'] to a set of all sections/editions:
    secao_set = build_article_set(config_secao)
    # Remove sections/editions by applying successive secao filters:
    for f in secao_filters:
        secao_set = remaining_sections(secao_set, f['positive_filter'], f['negative_filter'])
        
    return secao_set

# End.


def get_relevant_articles(bot_info, articles):
    """
    Filter the query result 'articles' that gets the last 30 minutes new stuff
    in the database.
    -- articles: list of dicionaries. Each entry in list (a dict) is a row in the query results,
       and each key in dict is a column.
       
    # About bot_info['filters']:
    # This is a list of filters (dict), each filter has the entries:
    # 1 FILTER: column_name, positive_filter, negative_filter.
    #           -- The value for column_name is the column to check.
    #           -- The positive and negative_filter are a list of keywords that are combined with OR;
    #           -- The positive and negative filters are combined with AND;
    # The filters are combined with AND;
    # To combine filters with OR, create a new bot_info with a different list of filters.
    """
    
    filters = bot_info['filters']
    
    if len(filters):
        if gs.debug:
            print('name:', bot_info['nome'])
            print('# articles:', len(articles))

        # Loop over filters in a filter set:
        for f in filters:
           
            if gs.debug:
                print('f', f)
            
            # Delete None
            # Select all desired columns that actually exist in the bigquery results:
            articles = list(filter(lambda x: x[f['column_name']] is not None, articles))
                
            if 'positive_filter' in f.keys():
                articles = list(filter(lambda x: 
                    any([var.lower() in x[f['column_name']].lower() 
                        for var in f['positive_filter']]), articles))
                        
            # Changed on 2019-05-21 from elif to if:
            if 'negative_filter' in f.keys():
                articles = list(filter(lambda x: 
                    all([var.lower() not in x[f['column_name']].lower() 
                        for var in f['negative_filter']]), articles))

            Narticles = len(articles)
            if gs.debug:
                print('# filtered articles:', Narticles)
            # Exit early if current filter has already removed all articles:
            if Narticles == 0:
                return articles
                
    return articles
