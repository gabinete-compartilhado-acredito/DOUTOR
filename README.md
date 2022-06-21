# *DOUTOR* - DOU Tracker, Obtainer & Reporter

*DOUTOR* é um código em Python 3.6 que escaneia o Diário Oficial da União (DOU), salva seus artigos numa base de dados,
filtra os artigos de acordo com filtros definidos pelo usuário (em formato [JSON](https://pt.wikipedia.org/wiki/JSON))
e publica aqueles selecionados em canais do [Slack](https://slack.com/intl/en-br/). É o seu monitor do DOU em código aberto!

**PS:** A [imprensa oficial](http://www.in.gov.br) pode alterar a estrutura HTML do DOU e, com isso, prevenir
o correto funcionamento do *DOUTOR*. Embora perfeitamente funcional na data de publicação, a qualidade posterior
pode depender da manutenção do código que não estará, necessariamente, atualizada.

Este projeto pode ser combinado com nosso modelo de _machine learning_ que ordena as matérias da seção 1 e 2 por
relevância, para facilitar o monitoramento dos conteúdos mais importantes:
<https://github.com/gabinete-compartilhado-acredito/dou-ml>

## 1. Estrutura do projeto

    .
    ├── LICENSE           <- Licença de uso, cópia e modificações
    ├── README.md         <- Este documento
    ├── requirements.txt  <- Pacotes python necessários, junto com suas versões
    ├── configs           <- Arquivos de configuração que controlam as tarefas do *DOUTOR*
    ├── exe               <- Links para scripts executáveis diretamente do terminal
    ├── filters           <- Arquivos JSON com filtros aplicados aos artidos do DOU
    ├── keys-configs      <- Pasta de senhas e tokens de acesso
    ├── src               <- Códigos fonte (scripts de python 3.6)
    └── temp              <- Pasta para arquivos baixados e registros (logs)

## 2. Instalação

### 2.1 Código python

O *DOUTOR* não precisa ser instalado; entretanto ele precisa que você tenha python 3 instalado, junto com os seguintes pacotes:
`sys`, `requests`, `json`, `collections`, `lxml`, `datetime`, `time`, `re`, `slackclient` *(versão < 2)* e `os`.
No [Anaconda](https://www.anaconda.com), esses pacotes podem ser instalados com a linha de comando:

    conda install -c conda-forge <pacote>

onde `<pacote>` é substituído pelo pacote em questão (parte deles já vem no Anaconda).

Também é possível instalar as dependências do código com o comando:

    pip install -r requirements.txt

**PS:** É importante que a versão do pacote `slackclient` seja anterior à 2, pois as mudanças feitas na versão 2
inviabilizam a execução do *DOUTOR*. Uma versão adequada do pacote é listada em `requirements.txt` e pode ser instalada
com o comando acima ou via Anaconda:

    conda install -c conda-forge slackclient=1.3.1


### 2.2 Configurando seu Slack

* Se você não tem um workspace do Slack, acesse o site <https://slack.com/create> e siga as instruções para criar um.
* Crie os canais desejados clicando no símbolo de mais "+" ao lado de "canais" (ou "channels") no menu esquerdo.
Canais são espaços temáticos onde as mensagens serão publicadas. Maiores informações,
[aqui](https://get.slack.help/hc/en-us/articles/201402297-Create-a-channel).
* [Crie um app](https://api.slack.com/apps?new_app) no seu workspace com o nome desejado.
Ele será o responsável por publicar mensagens nos canais sobre os artigos do DOU selecionados pelo *DOUTOR*.
* Na página do seu novo app, clique em "Adicionar funcionalidades" e selecione "Permissões".
* Na seção "Escopo", adicione a permissão "Enviar mensagem como `<app-name>`", onde `<app-name>` é o nome do seu novo app; salve as alterações.
* No topo da mesma página, clicar no botão "Instalar no workspace"; em seguida, clique em "Permitir".
* Copie o token de acesso "OAuth" e salve em um arquivo dentro do sub-diretório "keys-configs", no diretório do *DOUTOR*;
essa será a "senha de acesso" do *DOUTOR* ao Slack.

Pronto! Se quiser, você pode mudar o ícone do seu app para deixá-lo mais bonito.

## 3. Configuração dos filtros

Os filtros são salvos em arquivos JSON, dentro do sub-diretório "filters". Cada filtro é composto por um conjunto
de objetos (ou dicionários, em termos de linguagem Python) -- isto é, o que tem a forma `{...}` -- com as seguintes chaves (keys) em comum:
`nome`, `casa`, `channel`, `description` e `filter_number`. Ou seja: um filtro é um conjunto de objetos
com os mesmos valores nessas chaves.

Para cada filtro, `nome` serve de etiqueta (label) para o filtro em questão; `casa` recebe o valor `dou` (por motivos históricos);
`channel` especifica em qual canal as mensagens filtradas serão publicadas; e `description` serve como descrição, na
publicação do Slack, a quê os artigos publicados se referem. Todas essas chaves recebem strings. Por fim,
`filter_number` é um número natural que identifica univocamente o filtro.

Cada objeto tem ainda as chaves `column_name`, `positive_filter`, `negative_filter`.
A chave `column_name` recebe uma string que especifica em qual campo semântico do artigo a procura por termos-chave vai atuar.
Já as chaves `positive_filter` e `negative_filter` especificam os termos-chave que devem estar presentes e que não podem estar presentes para
que o artigo seja selecionado pelo objeto, respectivamente. Tanto o `positive_filter` quanto o `negative_filter` recebem strings podendo conter
múltiplos termos-chave separados por ponto-e-vírgula (`;`). Os termos-chave são combinados com a operação lógica OU (OR), isto é:
qualquer termo-chave em `positive_filter` serve para selecionar um artigo e qualquer termo-chave em `negative_filter` serve para descartar
um artigo. As seleções feitas por `positive_filter` e `negative_filter` são combinadas com a operação lógica E (AND).

Os campos semânticos disponíveis para busca são similares aos utilizados no HTML de artigos do DOU (veja este
[exemplo](http://www.in.gov.br/web/dou/-/medida-provisoria-n-894-de-4-de-setembro-de-2019-214566522)):

* `secao`, a seção do DOU (que pode incluir os termos "1", "2", "3", "Extra" e "Suplemento");
* `orgao`, que especifica o órgão público responsável pelo artigo (e.g. "Ministério da Infraestrutura", "Tribunal de Contas da União");
* `assina`, a pessoa que assina o artigo;
* `identifica`, o título do artigo (que pode conter, por ex.: "Decreto" e "Resolução");
* `cargo`, que define o cargo do assinante (e.g. "Presidente da Mesa do Congresso Nacional");
* `pagina`, a página do DOU no qual o artigo foi publicado;
* `edicao`, a edição do DOU;
* `ementa`, a ementa do artigo;
* `pub_date`, a data de publicação do artigo;
* `fulltext`, todo o texto do artigo, sem diferenção entre campos semânticos;
* e `alltext`, um campo criado pelo *DOUTOR* que combina os demais existentes no HTML de artigos do DOU:
`italico`,  `strong`, `ato_orgao`, `subtitulo` e `paragraph`. Esses campos também estão disponíveis para busca.

**PS:** As diferenças entre `fulltext` e `alltext` é que o primeiro mantém a ordem original do texto, remove quebras de linha,
e não diferencia múltiplas entradas do mesmo campo semântico. Já o segundo agrupa os vários campos semânticos combinados e os
coloca na ordem descrita acima, sendo que cada ocorrência é sepadada por um *pipe* (`|`).

Por fim, os objetos que compõem um mesmo filtro são combinados com a operação lógica E (AND). O *DOUTOR* vem acompanhado
por alguns filtros em formato JSON como exemplos.

## 4. Executando o *DOUTOR*

Você pode executar o *DOUTOR* em dois modos diferentes via os atalhos disponíveis no sub-diretório `exe`: `capture_dou` e `monitore_dou`.
Ambos recebem como parâmetro o nome de um arquivo de configuração (guardados no sub-diretório `configs`), descritos na seção seguinte.
A rotina `capture_dou` varre o DOU apenas uma vez e encerra imediatamente em seguida. Já a rotina `monitore_dou` faz uma
primeira varredura e permanece ativa, esperando o intervalo especificado no arquivo de configuração para varrer o DOU de novo.
Essa rotina nunca se encerra sozinha, mas pode ser terminada apertando `CTRL+C`; além disso, ela será encerrada se o computador
em questão for desligado.

## 5. Configuração do *DOUTOR*

O comportamento do *DOUTOR* é controlado por arquivos de configuração em formato JSON guardados no sub-diretório `configs`
(veja os exemplos fornecidos). Esses arquivos contém um único objeto com as seguintes chaves:

* `sched_interval`: o intervalo (em minutos) entre cada varredura do DOU, no caso da rotina `monitore_dou`;
* `date_format`: uma string definindo o [formato](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior)
(em padrão `datetime`, e.g. `%Y-%m-%d`) da data especificada em `end_date` abaixo;
* `end_date`: string representando a data da edição do DOU que deve ser varrida, no formato dado por `date_format` (mas também
pode ser "now" para a data do dia corrente ou "yesterday" para o dia anterior);
* `timedelta`: número inteiro de dias que devem ser também varridos a partir de `end_date` (utilize números negativos para varrer
dias anteriores a `end_date`, ou 0 para apenas varrer a data em `end_date`);
* `secao`: lista (isto é, `[...]`) de seções a serem varridas na próxima execução da captura, que pode conter os elementos 1, 2, 3,
"e" e "1a" (para as seções 1, 2, 3, Extra e Suplemento);
* `secao_all`: esta chave só é utilizada no caso da execução via `monitore_dou`, para especificar quais seções devem ser selecionadas
para a próxima varredura quando ela é executada em um novo dia (mesmo formato de `secao`);
* `last_extra`: um número natural que especifica quantas edições extras (e.g. A, B, C...) do DOU devem ser ignoradas na varredura (para evitar repetir a publicação
de artigos já publicados);
* `storage_path`: caso se escolha salvar localmente os artigos (via `save_articles` abaixo), o caminho (path) para o diretório onde salvar os artigos;
* `save_articles`: uma variável booleana (`true`, `false`) que determina se os artigos são salvos localmente ou não;
* `filter_file`: uma string que especifica o arquivo JSON de filtros que será utilizado na varredura;
* `post_articles`: uma variável boolenada que especifica se o *DOUTOR* deve publicar os artigos selecionados ou não;
* `slack_token`: uma string que determina o arquivo com o token do Slack, que permite seu acesso ao *DOUTOR*.

## 6. Scripts auxiliares

### 6.1 `list_articles`

Este script pode ser executado no terminal e recebe dois parâmetros: a data no formato `%Y-%m-%d` (e.g. `2020-03-30`) e
as seções do DOU sem espaçamentos (e.g. `1` ou `13` ou `123e`). Ela retorna as URLs dos artigos desse dia e dessas seções.
Mais informações na docstring.

## 7. Finalmentes

### Autores

* **Henrique S. Xavier** - [@hsxavier](https://github.com/hsxavier)
* **João Carabetta** - [@JoaoCarabetta](https://github.com/JoaoCarabetta)

### Licença

Este projeto é distribuído sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes.

### Agradecimentos

Este README foi levemente baseado em: [*A template to make good README.md*](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)

