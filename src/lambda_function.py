import time
import capture_driver as cd
import global_settings as gs
# Packages only required for remote implementation:
if not gs.local:
    import boto3                                  
    from dynamodb_json import json_util as dyjson


def lambda_handler(event, context):
    """
    Wrapper for remote (AWS) implementation of DOU articles capture. No input is required.
    This function loads the configuration from DynamoDB, runs the capture driver and 
    updates the configuration in DynamoDB. The schedule is controled from outside by cron 
    from CloudWatch.
    """
    client = boto3.client('dynamodb')
    
    # Load config from AWS DynamoDB:
    config = client.get_item(TableName="configs",  Key={'name': {'S': 'capture_DOU'}})
    config = dyjson.loads(config)['Item']
    
    # Run DOU articles capture:
    updated_config = cd.capture_DOU_driver(config)
    
    # Save config to AWS DynamoDB:
    response = client.put_item(TableName="configs", Item=dyjson.dumps(updated_config, as_dict=True))

    # Immediately call this function again if capturing next article batch in AWS:
    if gs.local == False and updated_config['next_batch'] == True:
        time.sleep(5)
        print('Calling next batch')
        lambd = boto3.client('lambda')
        lambd.invoke(
             FunctionName='arn:aws:lambda:us-east-1:085250262607:function:capture_dou:PROD',
             #FunctionName='arn:aws:lambda:us-east-1:085250262607:function:capture_dou:DEV',
             InvocationType='Event')

def local_scheduler(config):
    """
    Scheduler (daemon) for running DOU articles capture. It takes as input
    a configuration (dict) or a JSON filename containing the configuration.
    
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
    """
    while True:
        print(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
        config = cd.capture_DOU_driver(config)
        if gs.debug:
            print("Next config:")
            print(config)
        time.sleep(60*config['sched_interval'])
