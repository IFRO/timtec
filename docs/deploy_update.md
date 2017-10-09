## Atualizando para uma nova versão

> Atenção: estas orientações são para atualizar a partir da versão 3.1 ou superior. Se seu ambiente é inferior a esta versão, não siga estes passos. 

### 1. Faça um backup de todos os seus arquivos e de sua base de dados
* 1.1 Recomendamos que faça uma cópia dos diretório /timtec e /webfiles antes de começar esse processo:
```
timtec-production@server:$ cp ~/timtec-production/timtec /SEU-DIRETORIO-DE-BACKUP/
timtec-production@server:$ cp ~/timtec-production/webfiles /SEU-DIRETORIO-DE-BACKUP/
```
* 1.2 Faça um backup da base de dados e salve no mesmo diretório de backup da aplicação:
```
timtec-production@server:$ pg_dump timtec-production > yyyy_mm_dd_timtec_backup_database.sql
```

### 2. Verifique qual é a sua versão

* 2.1. As versões do TIMTec estão disponíveis aqui: https://github.com/hacklabr/timtec/releases Cada versão do TIMTec é uma tag no repositório git.
* 2.2. No seu servidor, logado com usuário da aplicação (se você seguiu a documentação deve ser o usuário timtec-production), entre na pasta da aplicação e de um git status:

```
timtec-production@server:$ git status
HEAD detached at v3.2
```
### 3. Refaça o enviroment

* 3.1. Delete o env já existente. No contexto da documentação padrão, o env deve estar em /home/timtec-production/env. Veja:
```
timtec-production@server$ rm -rf /home/timtec-production/env
```
* 3.2. Recrie o env com o comando abaixo: 
```
timtec-production@server$ virtualenv /home/timtec-production/env
```

### 4. Baixe as atualizações e mude o checkout
No seu servidor, logado com usuário da aplicação (se você seguiu a documentação deve ser o usuário timtec-production), entre na pasta da aplicação e de um git pull:

```
timtec-production@server:$ git fetch --all
timtec-production@server:$ git checkout 4.1.2
```
### 5. Faça o update

* 5.1 ative o ambiente virtual python:

```
timtec-production@server:$ virtualenv /home/NOME-DO-SEU-USUARIO-OU-DIRETORIO/env
timtec-production@server:$ source /home/NOME-DO-SEU-USUARIO-OU-DIRETORIO/env/bin/activate
```

Se você estiver seguindo a documentação, você pode deverá dar o comando da seguinte maneira: 
```
timtec-production@server:$ virtualenv /home/timtec-production/env
timtec-production@server:$ source /home/timtec-production/env/bin/activate
```

* 5.2 Rode o make update na pasta da aplicação:
```
timtec-production@server:$ cd ~/timtec/
timtec-production@server:$ make update
```

Feito isso, o software estará atualizado.
