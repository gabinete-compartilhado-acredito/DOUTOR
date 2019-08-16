import global_settings as gs
from slackclient import SlackClient
from collections import defaultdict

if not gs.local:
    import json
    import boto3 


# The docstrings below form a template for Slack bot messages:
# Header:
blocks = """[
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*%(descricao_post)s*"
        }
    },
    {
        "type": "divider"
    },
        %(fields)s
]"""
# Below is a model for a post in slack, properly formatted.
# It is a string where python will replace place-holders 
# for variables (that start with %) with actual values:
fieldDOU = """
    {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "*%(identifica)s*\\n *Órgão*: %(orgao)s\\n\\n *%(resumo_tipo)s:* %(resumo)s\\n\\n"
        }
    },
    {
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "*Assina:* %(assina)s (%(cargo)s)\\n*Publicado em:* %(pub_date)s | Edição: %(edicao)s | Seção: %(secao)s | Página: %(pagina)s\\n<%(url)s|Artigo completo>  |  <%(url_certificado)s|Versão certificada>\\n\\n\\n"
            }
        ]
    }
"""
# For system messages:
fieldSys = """	
    {
		"type": "section",
		"text": {
			"type": "mrkdwn",
			"text": "*%(function)s:* %(message)s"
		}
	}
"""


def post_to_slack(payload, slack_token):
    """
    Get the 'payload' (a dict that contains the information for the post
    in Slack) and and send it to Slack. 
    """
    
    # Create a series of slack posts (one for each new tramitação, separated 
    # by commas) using the info in payload data:
    if payload['casa'] == 'dou':
        fields = ','.join(map(lambda x: fieldDOU % x, payload['data']))
    elif payload['casa'] == 'sys':
        fields = ','.join(map(lambda x: fieldSys % x, payload['data']))
    else:
        fields = ','.join(map(lambda x: field % x, payload['data']))
    
    if len(fields) == 0:
        print('No updates')
        return 0
        
    payload.update({'fields': fields})
    
    # Username and password for Slack:
    with open(slack_token, 'r') as token_file:
        slack_token = token_file.read()
    sc = SlackClient(slack_token)
    
    res = sc.api_call(
      "chat.postMessage",
      channel=payload['media']['channel'],
      blocks=blocks % payload
    )
    
    if not res['ok']:
        print('Call to Slack post message failed!')
        print(res)
        print(payload)


def translate_to_slack(datum, casa):
    """
    For a single entry in the query results, create a dict with the relevant information.
    """
    
    if datum['ementa'] == 'None':
        resumo_tipo0 = 'Excerto'
        resumo0 = datum['resumo']
    else:
        resumo_tipo0 = 'Ementa'
        resumo0 = datum['ementa']
    return dict(
        identifica=      datum['identifica'],
        orgao=           datum['orgao'],
        assina=          datum['assina'],
        cargo=           datum['cargo'],
        pub_date=        datum['pub_date'],
        edicao=          datum['edicao'],
        secao=           datum['secao'],
        pagina=          datum['pagina'],
        url=             datum['url'],
        url_certificado= datum['url_certificado'],
        resumo_tipo=     resumo_tipo0,
        resumo=          resumo0)


def to_slack_format(bot_info, result):
    """
    Takes the bigQuery result and transforms it into a new structure that
    contains metadata about the media destination.
    """
    if gs.debug:
        print('# articles to format:', len(result))
    
    # Remove double quotes from bigQuery results (list of dicts which are new tramitações)
    # to avoid bugs:
    result = map(lambda x: {k: str(v).replace('"', '') for k, v in x.items()}, result)
    
    # Add default dict to avoid error if chosen key is inexistent 
    # (in this case, return ''):
    result = list(map(lambda x: defaultdict(lambda: '', x), result))
    
    # Reorganize and rename dict:
    result = map(lambda x: translate_to_slack(x, bot_info['casa']), result)
    
    # Create a dict with metadata and the data as a list inside a key:
    payload = dict(
        casa = bot_info['casa'],
        descricao_post= bot_info['media']['description'],
        media={'type': bot_info['media']['type'],
                'channel': bot_info['media']['channel']},
        data=list(result))
    
    # Create a json from the structure above:
    return payload


def post_to_sns(bot_info, payload):
    """
    Sends the message ('payload') to AWS SNS, under the topic
    set in bot_info['sns-topic'].
    """
    
    print('Sending to SNS')
    sns = boto3.client('sns')
    # Create a topic in the SNS if it does not exist:
    res = sns.create_topic(Name=bot_info['sns-topic'])
    # Subscribe the Lambda function to the topic created above:
    sns.subscribe(TopicArn=res['TopicArn'],
                  Protocol='lambda',
                  Endpoint='arn:aws:lambda:us-east-1:085250262607:function:post-to-slack:JustLambda')
    
    # Send the payload to the topic. Everyone subscribed (in this case, the Lambda 
    # function 'post-to-slack') will receive the Message:
    payload = json.dumps(payload, ensure_ascii=False)
    sns.publish(TopicArn=res['TopicArn'],
                Message=payload)


def post_article(config, bot_info, articles):
    """
    Wrapper for functions 'post_to_sns' (post articles using remote service from AWS) and
    'post_to_slack' (post articles directly to Slack). The function called 
    depends on 'gs.local'.
    """
    if gs.debug:
        print("Will post in " + str(bot_info['media']))
    payload = to_slack_format(bot_info, articles)
    if gs.debug:
        print("Posting...")                
    if gs.local:
        post_to_slack(payload, config['slack_token'])
    else:
        post_to_sns(bot_info, payload)
