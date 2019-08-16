def get_key_value(key, article_raw):
    """
    Searches for an entry in article_raw (which is a list of dicts) that
    has the 'key'. Then it returns the value associated to that key. 
    If the key is not found, return None.
    """ 
    sel = list(filter(lambda d: d['key']==key, article_raw))
    if len(sel)==0:
        return None
    return sel[0]['value']


def structure_article(article_raw):
    """
    Takes a list of dicts that represent a DOU article with the keywords
    key, value, capture_date, url and url_certificado and select relevant 
    keys (hard-coded), rename them and output a dict with only the relevant 
    keys.
    """
    relevant_keys = ['secao-dou', 'orgao-dou-data', 'assina', 'identifica', 'cargo', 'secao-dou-data', 
                     'edicao-dou-data', 'dou-em', 'ementa', 'dou-strong', 'titulo', 'subtitulo', 
                     'dou-paragraph', 'publicado-dou-data']
    new_keys      = ['secao', 'orgao', 'assina', 'identifica', 'cargo', 'pagina',
                     'edicao', 'italico', 'ementa', 'strong', 'ato_orgao', 'subtitulo', 
                    'paragraph', 'pub_date']
    
    relevant_values = [get_key_value(key, article_raw) for key in relevant_keys]
    struct = dict(zip(new_keys, relevant_values))
    
    # Join with identifying fields:
    struct['capture_date']    = article_raw[0]['capture_date']
    struct['url']             = article_raw[0]['url']
    struct['url_certificado'] = article_raw[0]['url_certificado']
    
    # Format selected fields:
    struct['secao'] = struct['secao'].split('|')[0].split(':')[1].strip()
    
    # Create new field (all the text):
    fields_list = filter(lambda s: s!=None, [struct['ato_orgao'], struct['subtitulo'], struct['ementa'], 
                                            struct['strong'], struct['italico'], struct['paragraph']])
    struct['alltext'] = ' | '.join(fields_list)
    # Another new field (a clipping):
    if type(struct['paragraph']) == str:
        paragraph_list = struct['paragraph'].split('|')
        if len(paragraph_list) > 1:
            struct['resumo'] = paragraph_list[0][:200] + '... | ...' + paragraph_list[1][:200]
        else:
            struct['resumo'] = paragraph_list[0][:300]
    else:
        struct['resumo'] = None
        
    return struct
