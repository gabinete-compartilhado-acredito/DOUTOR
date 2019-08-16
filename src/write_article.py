import json
import datetime as dt
import os
import global_settings as gs

if not gs.local:
    import boto3


def last_slash(path):
    """
    Takes a file path and returns the path with a tailing slash
    if that is missing.
    """
    result = path if path[-1] == '/' else  path + '/'
    return result


def get_pub_date(article_raw):
    """
    Given a list of dicts with key-value pairs 'article_raw' that describe a DOU's article, 
    returns a string that states the article's date of publication. If the hard-coded key 
    is not found, return capture date instead (with the 'capt' prefix).
    """
    # Find dict in list that contains publication date:
    pub_date_entry = list(filter(lambda d: d['key']=='publicado-dou-data', article_raw))
    
    if len(pub_date_entry)==0:
        # If no publication date was found, use capture date instead
        pub_date_entry = 'capt_' + article_raw[0]['capture_date'].split()[0]
    else:
        # If it was found, format it to '%Y-%m-%d':
        pub_date_entry = dt.datetime.strptime(pub_date_entry[0]['value'], '%d/%m/%Y').strftime('%Y-%m-%d')
    
    return pub_date_entry


def write_local_article(config, article_raw, filename):
    """
    Given the input:
    * config      -- a dict that contains the storage path;
    * article_raw -- a list of dicts that stores the information in an article;
    * filename    -- the name for the article's file.    
    Writes the article as json to a file in a sub-directory given by the publication date, 
    inside the directory given by storage_path in config.
    """
    if len(article_raw) == 0:
        print('len(article_raw)=0: do not write locally.')
        return None
    
    # Replace slashes by underscores in filenames to avoid crash:
    filename = filename.replace('/','_')
    
    # Get publication date to use as sub-folder in local storage:
    pub_date = get_pub_date(article_raw)
    
    # Creates subdirectory if needed:
    path = last_slash(config['storage_path']) + pub_date + '/' 
    if not os.path.exists(path):
        os.makedirs(path)
   
    # dump json to file:
    with open(path + filename, 'w') as f:
        json.dump(article_raw, f)


def write_to_s3(config, article_raw, filename):
    """
    Given the input:
    * config      -- a dict that contains the S3 bucket and path for the article (key);
    * article_raw -- a list of dicts that stores the information in an article;
    * filename    -- the name for the article's file.    
    It prepares a json ('body') and save it to AWS S3. It returns the S3 
    HTTP status code.
    """
    if len(article_raw) == 0:
        print('len(article_raw)=0: do not save to S3.')
        return None

    # record is one dict, json is a python package.
    # First it transforms the list of dicts in a list of jsons
    # (json is a string):
    print ('Creating json list...')
    result = [json.dumps(record, ensure_ascii=False) for record in article_raw] 
    # Cria um arquivo texto com vários jsons:
    body = '\n'.join(result)
    
    # Salva no S3 os jsons:
    client = boto3.client('s3')
    s3_log = client.put_object(
                  Body=body,
                  Bucket=config['bucket'], 
                  Key=config['key']+filename)
    
    return s3_log['ResponseMetadata']['HTTPStatusCode']
