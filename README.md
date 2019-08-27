# *DOUTOR* - DOU Tracker, Obtainer & Reporter

*DOUTOR* é um código em Python 3.6 que escaneia o Diário Oficial da União (DOU), salva seus artigos numa base de dados,
filtra os artigos de acordo com filtros definidos pelo usuário (em formato [JSON](https://pt.wikipedia.org/wiki/JSON))
e publica aqueles selecionados em canais do [Slack](https://slack.com/intl/en-br/). É o seu monitor do DOU em código aberto!


## 1. Estrutura do projeto

    .
    ├── LICENSE       <- Licença de uso, cópia e modificações
    ├── README.md     <- Este documento
    ├── configs       <- Arquivos de configuração que controlam as tarefas do DOUTOR
    ├── exe           <- Links para scripts executáveis diretamente do terminal
    ├── filters       <- Arquivos JSON com filtros aplicados aos artidos do DOU
    ├── keys-configs  <- Pasta de senhas e tokens de acesso
    ├── src           <- Códigos fonte (scripts de python 3.6)
    └── temp          <- Pasta para arquivos baixados e registros (logs)

## 2. Instalação

### 2.1 Código python

O DOUTOR não precisa ser instalado; entretanto ele precisa que você tenha python 3 instalado, junto com os seguintes pacotes:
`sys`, `requests`, `json`, `collections`, `lxml`, `datetime`, `time`, `re`, `slackclient` e `os`.
No [Anaconda](https://www.anaconda.com), esses pacotes podem ser instalados com a linha de comando:

    conda install -c conda-forge <pacote>

onde `<pacote>` é substituído pelo pacote em questão (parte deles já vem no Anaconda).

### 2.2 Configurando seu Slack

* Se você não tem um workspace do Slack, acesse o site <https://slack.com/create> e siga as instruções para criar um.
* Crie os canais desejados clicando no símbolo de mais "+" ao lado de "canais" (ou "channels") no menu esquerdo.
Canais são espaços temáticos onde as mensagens serão publicadas. Maiores informações,
[aqui](https://get.slack.help/hc/en-us/articles/201402297-Create-a-channel).
* [Crie um app](https://api.slack.com/apps?new_app) no seu workspace com o nome desejado.
Ele será o responsável por publicar mensagens nos canais sobre os artigos do DOU selecionados pelo DOUTOR.
* Na página do seu novo app, clique em "Adicionar funcionalidades" e selecione "Permissões".
* Na seção "Escopo", adicione a permissão "Enviar mensagem como `<app-name>`", onde `<app-name>` é o nome do seu novo app; salve as alterações.
* No topo da mesma página, clicar no botão "Instalar no workspace"; em seguida, clique em "Permitir".
* Copie o token de acesso "OAuth" e salve em um arquivo dentro do sub-diretório "keys-configs", no diretório do DOUTOR;
essa será a "senha de acesso" do DOUTOR ao Slack.


These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

#### Prerequisites

You need to have the packages on `requirements.txt` installed. To do that, open the terminal and run:

```
pip3 install -U -r requirements.txt
```

#### Changing author

You need change to your name on the files: [LICENSE.md](LICENSE.md), here (below) and optionally put on your code files :)

### Authors

* **You** - *Code maker* - [@you](https://github.com/@you)

### License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

### Acknowledgments

* This README was adapted from [*A template to make good README.md*](https://gist.github.com/PurpleBooth/109311bb0361f32d87a2)
* The structure of this repository was adapted from [*Fast Project Templates*](https://github.com/JoaoCarabetta/project-templates)

