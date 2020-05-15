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


def make_resumo(fulltext):
    """
    Given a string (fulltext), this function aims to extract 
    the most important part of it as a abstract.
    """

    # Termos a serem pesquisados:
    termos = ['resolve:', 'onde se l', 'objeto:', 'espécie']
    # Tamanho do resumo:
    resumo_size = 300
    
    # Alterando o texto para minúsculo    
    fulltext  = str(fulltext)
    paragraph = fulltext.lower()
         
    for termo in termos:
        
        pos = paragraph.find(termo)
        
        if pos != -1: 
            # Se encontra algum dos termos, resume o texto com os 300 primeiros caracteres 
            # a partir do termo encontrado.
            abstract = fulltext[pos:pos + resumo_size]    
            break            # O break aqui serve para garantir que, caso um termo seja encontrado, 
                             # não busque pelos demais.
        
    if pos == -1:
            abstract = fulltext[:resumo_size]   # Se não encontra nenhum dos termos, resume o texto 
                                                # nos primeros 300 caracteres.          
    
    if len(fulltext[pos:]) > len(abstract):
        abstract = abstract + '...'
    
    return abstract


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
    struct['resumo'] = make_resumo(struct['fulltext'])
        
    return struct
