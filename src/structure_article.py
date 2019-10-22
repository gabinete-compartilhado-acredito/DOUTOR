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


def get_excert(paragraph):
    """
    Gets a string "paragraph", split it by " | " (which we used to 
    separate multiple paragraphs), and returns the combination of parts of the first 
    and second paragraphs. If there is just one paragraph, returns a part of it.
    """
    paragraph_list = paragraph.split('|')
    if len(paragraph_list) > 1:
        return paragraph_list[0][:200] + '... | ...' + paragraph_list[1][:200] 
    else:
        return paragraph_list[0][:300]
    

def make_resumo(paragraph):
    """
    Given a string 'paragraph' with all paragraphs of the DOU's article
    (separated by ' | '), creates a excert that acts as an abstract of 
    the article and return it.
    """
    if type(paragraph) == str:
        # Look for a marker of start of a possible resumo:
        marker = 'resolve: | '
        marker_start = paragraph.find(marker)
        # If no marker, just take the first paragraphs:
        if marker_start == -1:
            resumo = get_excert(paragraph)
        # If marker, get the following paragraphs:
        else:
            marker_end = marker_start + len(marker)
            paragraph  = paragraph[marker_end:]
            resumo = get_excert(paragraph)
        # Add ... to end of resumo if not the end of a phrase:
        if resumo[-1] != '.' and resumo[-2:] != '. ':
            resumo = resumo + '...'
        return resumo
    else:
        return None
    

def structure_article(article_raw):
    """
    Takes a list of dicts that represent a DOU article with the keywords
    key, value, capture_date, url and url_certificado and select relevant 
    keys (hard-coded), rename them and output a dict with only the relevant 
    keys.
    """
    relevant_keys = ['secao-dou', 'orgao-dou-data', 'assina', 'identifica', 'cargo', 'secao-dou-data', 
                     'edicao-dou-data', 'dou-em', 'ementa', 'dou-strong', 'titulo', 'subtitulo', 
                     'dou-paragraph', 'publicado-dou-data', 'assinaPr', 'fulltext']
    new_keys      = ['secao', 'orgao', 'assina', 'identifica', 'cargo', 'pagina',
                     'edicao', 'italico', 'ementa', 'strong', 'ato_orgao', 'subtitulo', 
                     'paragraph', 'pub_date', 'assinaPr', 'fulltext']
    
    relevant_values = [get_key_value(key, article_raw) for key in relevant_keys]
    struct = dict(zip(new_keys, relevant_values))
    
    # Join with identifying fields:
    struct['capture_date']    = article_raw[0]['capture_date']
    struct['url']             = article_raw[0]['url']
    struct['url_certificado'] = article_raw[0]['url_certificado']
    
    # Format selected fields:
    struct['secao']  = struct['secao'].split('|')[0].split(':')[1].strip()
    if struct['assinaPr'] != None:   # Existe assinatura do presidente.
        if struct['assina'] != None: # Existe as duas assinaturas.
            struct['assina'] = struct['assinaPr'] + ' | ' + struct['assina']
        else:                        # Só existe a assinatura do presidente.
            struct['assina'] = struct['assinaPr']
    
    # Create new field (all the text):
    fields_list = filter(lambda s: s!=None, [struct['ato_orgao'], struct['subtitulo'], struct['ementa'], 
                                            struct['strong'], struct['italico'], struct['paragraph']])
    struct['alltext'] = ' | '.join(fields_list)
    # Another new field (a clipping):
    struct['resumo'] = make_resumo(struct['paragraph'])
        
    return struct
