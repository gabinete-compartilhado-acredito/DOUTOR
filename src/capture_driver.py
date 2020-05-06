import requests
# This project's functions:
import global_settings as gs
import get_articles_url as gu
import parse_dou_article as pa
import write_article as wa
import filter_articles as fa
import structure_article as sa
import post_to_slack as ps



def this_extra_edition_number(edicao):
    """
    Gets a string 'edicao' that states which is this DOU's edition 
    (e.g. 132-B or 154) and returns the number (int) of extra editions up
    to this current one. No extra editions (e.g. 154) is 0, first
    extra edition (134-A) is 1, and so on.
    """
    last_char = str(edicao)[-1]
    if last_char.isdigit():
        return 0
    else:
        return ord(last_char.lower()) - 96

    
def captured_article_ok(save_option, saved, post_option, posted):
    """
    Given four boolean variables, return whether or not the article 
    should be considered captured or not.
    
    save_option: Was the code required to save the article?
    saved:       Did the code save the article?
    post_option: Was the code required to post the article?
    posted:      Did the code post the article?
    """
    # Nothing to do with article, mark as done.
    if save_option == False and post_option == False:
        return True
    # Only requested saving and it saved:
    if saved == True and post_option == False:
        return True
    # Only requested posting and it posted:
    if posted == True and save_option == False:
        return True
    # Did both saving and posting:
    if saved == True and posted == True:
        return True

    return False


def capture_DOU_driver(event):
    """
    This is the driver that runs DOU articles' capture.
    It receives either a filename (string) for a configuration file 
    or a configuration as a dict with keywords:

    * storage_path:  the path to save DOU articles;
    * save_articles: BOOL that tells whether or not to write all articles to database; 
    * date_format:   the format of end_date (e.g. %Y-%m-%d);
    * end_date:      the last day to search for articles (cat be set to 'now');
    * secao:         a list with DOU sections to search immediately;
    * secao_all:     a list with all DOU sections that one is interested in searching in the future
                     (1, 2, 3, 'e', '1a'; only relevant for scheduler); 
    * timedelta:     the number of days in the pasr from end_date to start the search
                     (a negative number);
    * filter_file:   JSON filename that describes the filters to be applied to articles;
    * post_articles: BOOL that tells whether or not to post articles to Slack;
    * slack_token:   Filename for file containing Slack's authentication token.

    It returns an updated configuration file for the next capture (assuming one wants 
    to periodically capture the DOU publications.
    """    
        
    # Load configuration:
    if type(event) == str:
        config = gu.load_local_config(event)
    elif type(event) == dict:
        config = event
    else:
        raise Exception('capture_DOU_driver: unknown input event type.')
    
    # Get list of URLs and filenames (in case one wants to save the articles):    
    if gs.debug:
        print("Getting articles' URLs...")
    url_file_list, next_config = gu.get_articles_url(config)
    Nurls = len(url_file_list)
    if True or gs.debug:
        print('# URLs:', Nurls)
    if Nurls == 0:
        return next_config    
    
    # Load filters:
    if gs.debug:
        print("Loading filters...")    
    if gs.local:
        filters = fa.load_local_filters(config['filter_file'])
    else:
        filters = fa.load_remote_filters()
    bot_infos = fa.format_filters(filters)

    # Remove filters (that need to exist to select articles) that eliminate all downloaded sections:
    if gs.debug:
        Nfilters = len(bot_infos)
        print("Removing unecessary filters...")
    bot_infos = list(filter(lambda bot_info: len(fa.secao_left(config['secao'], bot_info))>0, bot_infos))
    if gs.debug:
        print("Removed " + str(Nfilters - len(bot_infos)) + " filters.")

    # Specifies number of retries for GET:
    session = requests.Session()
    session.mount('http://www.in.gov.br', requests.adapters.HTTPAdapter(max_retries=3))
    
    # The lists inside relevant_articles will receive the articles selected by each filter set:
    relevant_articles = [[]]*len(bot_infos)
    
    # Loop over urls to get articles:
    if gs.debug:
        counter = 0
        print("LOOP over URLs:")        
    for url_file in url_file_list:
        
        # GET one DOU article:
        if gs.debug:
            counter = counter + 1
            print("Get article...", counter)
        try:
            get_ok   = False
            response = session.get(url_file['url'], timeout=15)
            get_ok   = True      
        # Warn if GET crashes:
        except requests.exceptions.ReadTimeout:
            print('ReadTimeout in GET ' + url_file['url'])
        except requests.exceptions.ConnectTimeout:
            print('ConnectTimeout in GET ' + url_file['url'])
        except:
            print('Error in GET ' + url_file['url'])
        
        if get_ok:
            if response.status_code == 200:
                # SUCCESS in GET!
                
                # Parse article into a flexible structure that reads every key (html tag class) in the file:
                if gs.debug:
                    print("Parse article...")
                raw_article = pa.parse_dou_article(response, url_file['url'])

                # Organize article by capturing selected fields:
                if gs.debug:
                    print("Select relevant fields...")        
                article = sa.structure_article(raw_article)
                
                # Write raw article's file to database:
                wrote_return = 2   # (Preset status of 'save article' operation)
                if config['save_articles']:
                    if gs.debug:
                        print("Saving article...")
                    if gs.local:
                        wa.write_local_article(config, raw_article, url_file['filename'])
                        wrote_return = 200
                    else:
                        write_return = wa.write_to_s3(config, raw_article, url_file['filename'])
                        if write_return == 200:
                            wrote_return = wa.copy_s3_to_storage_gcp(config['bucket'], config['key'] + url_file['filename'])
                            if wrote_return != 200 and ds.debug:
                                print('Copy_s3_to_storage_gcp failed.') 
                        elif ds.debug:
                            print('Write_to_s3 failed.')
                            
                # Loop over filters:
                if gs.debug:
                    print("Filtering article...")
                for i in range(len(bot_infos)):
                    # Filter article:
                    relevant_articles[i] = relevant_articles[i] + fa.get_relevant_articles(bot_infos[i], [article])
                    # Slack crashes if message has more than 50 blocks.
                    # Avoid this by pre-posting long messages:
                    if config['post_articles'] and len(relevant_articles[i]) > 20:
                        if gs.debug:
                            print('Selected more than 20 articles.')
                        ps.post_article(config, bot_infos[i], relevant_articles[i])
                        relevant_articles[i] = []

                # Record URL in list of captured articles (for now, we will assume that the article always was posted):
                if captured_article_ok(config['save_articles'], wrote_return==200, config['post_articles'], True):
                    gu.register_captured_url(config['url_list'], url_file['url'])
                elif gs.debug:
                    print('Failed to record as done: ' + url_file['url'])
                  
            else:
                # GET ran but returned BAD STATUS:
                print('Bad status in GET ' + url_file['url'])  
    # End of Loop over URLs.

    if config['post_articles']:
        # Send the selected articles to Slack:
        for i in range(len(bot_infos)):
            if len(relevant_articles[i]) > 0:
                ps.post_article(config, bot_infos[i], relevant_articles[i])

    # Return the config for next capture try:
    return next_config
