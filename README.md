# *DOUTOR* - DOU Tracker, Obtainer & Reporter

*DOUTOR* é um código em Python 3.6 que escaneia o Diário Oficial da União (DOU), salva seus artigos numa base de dados,
filtra os artigos de acordo com filtros definidos pelo usuário (em formato [JSON](https://pt.wikipedia.org/wiki/JSON))
e publica aqueles selecionados em canais do [Slack](https://slack.com/intl/en-br/). É o seu monitor de código aberto do DOU!


## Estrutura do projeto

    .
    ├── LICENSE       <- Licença de uso, cópia e modificações
    ├── README.md     <- Este documento
    ├── configs       <- Arquivos de configuração que controlam as tarefas do DOUTOR
    ├── exe           <- Links para scripts executáveis diretamente do terminal
    ├── filters       <- Arquivos JSON com filtros aplicados aos artidos do DOU
    ├── keys-configs  <- Pasta de senhas e tokens de acesso
    ├── src           <- Códigos fonte (scripts de python 3.6)
    └── temp          <- Pasta para arquivos baixados e registros (logs)

## Instalação

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

