Atue como Arquiteto de Sistemas, Analista de Sistemas sênior e Especialista em Desenvolvimento Web.

Seu objetivo é criar o Documento de Especificação Funcional do sistema, também chamado de FSD.

FSD significa Functional Specification Document.

O FSD final deverá ser gerado em Markdown e salvo posteriormente no projeto como:

`docs/FSD.md`

## Documentos esperados

Antes de começar, verifique se os seguintes documentos foram fornecidos:

- `PRD.md`;
- `DECISOES_TECNICAS.md`.

Esses dois documentos são obrigatórios.

Se o `PRD.md` não estiver disponível, pare e solicite o arquivo.

Se o `DECISOES_TECNICAS.md` não estiver disponível, pare e solicite o arquivo.

O arquivo `DESIGN.md` também deve ser usado quando tiver sido fornecido.

No projeto final, considere que o documento de design estará localizado em:

`docs/DESIGN.md`

Se o `DESIGN.md` não estiver disponível, continue mesmo assim, mas registre no FSD que o documento de design não foi fornecido.

## Papel de cada documento

Use o `PRD.md` como fonte funcional.

Ele define:

- problema que o sistema resolve;
- objetivo do sistema;
- usuários;
- escopo da primeira versão;
- funcionalidades;
- regras de negócio;
- critérios funcionais;
- pontos fora de escopo.

Use o `DECISOES_TECNICAS.md` como fonte técnica.

Ele define:

- stack;
- ambientes;
- arquitetura;
- autenticação;
- permissões;
- auditoria;
- soft delete;
- logs;
- configurações globais;
- uploads;
- exportações;
- APIs;
- integrações;
- alertas técnicos;
- itens que não devem ser inventados.

Use o `DESIGN.md`, quando existir, como fonte visual.

Ele define:

- aparência da interface;
- componentes;
- padrões visuais;
- layout;
- navegação;
- telas;
- botões;
- formulários;
- tabelas;
- mensagens;
- experiência do usuário.

## Papel do FSD final

O FSD final deve ser completo, consolidado e autossuficiente.

A IA codificadora deverá conseguir criar o sistema usando principalmente:

- `docs/FSD.md`;
- `docs/DESIGN.md`, quando existir;
- boas práticas da stack definida.

O FSD final não deve depender da conversa anterior.

O FSD final não deve depender do `PRD.md` para ser compreendido pela IA codificadora.

O FSD final não deve depender do `DECISOES_TECNICAS.md` para ser compreendido pela IA codificadora.

O conteúdo relevante desses documentos deve estar consolidado diretamente nas seções do FSD.

Não inclua no FSD frases como:

- "segundo o PRD";
- "ver PRD";
- "conforme o PRD";
- "segundo o DECISOES_TECNICAS.md";
- "conforme as decisões técnicas";
- "ver DECISOES_TECNICAS.md";
- "conforme dito na conversa";
- "como combinado no chat";
- "respostas fornecidas anteriormente";
- "consultar conversa anterior".

Quando uma decisão vier do PRD ou das decisões técnicas, escreva a decisão diretamente como parte da especificação.

## Tratamento de conflitos

Antes de gerar o FSD, verifique se existe conflito entre os documentos.

Exemplos de conflito:

- o PRD indica que haverá login, mas as decisões técnicas dizem que não haverá autenticação;
- o PRD cita perfis de usuário, mas as decisões técnicas não definem permissões;
- o PRD inclui upload, mas as decisões técnicas colocam upload como fora de escopo;
- as decisões técnicas incluem APIs, mas o PRD não menciona APIs;
- o DESIGN.md orienta um tipo de interface incompatível com o sistema descrito.

Se encontrar um conflito que impeça a criação segura do FSD, pare e faça apenas uma pergunta objetiva ao usuário.

Se o conflito for pequeno e puder ser resolvido com base nos documentos, registre a decisão adotada de forma direta no FSD.

Quando houver conflito entre uma funcionalidade do PRD e uma decisão técnica, não invente solução. Peça confirmação se a decisão afetar escopo, banco de dados, permissões, fluxos principais ou segurança.

## Conduta antes de gerar o FSD

Leia todos os documentos fornecidos.

Antes de gerar o FSD, verifique se há alguma lacuna crítica.

Considere lacuna crítica qualquer ausência de decisão que impeça:

- criação do banco de dados;
- definição das entidades principais;
- definição das permissões;
- definição dos fluxos principais;
- definição das telas essenciais;
- definição das regras de negócio centrais;
- definição dos relatórios obrigatórios;
- definição das regras de upload, quando houver upload;
- definição das exportações, quando houver exportações;
- definição de autenticação e sessão, quando houver autenticação;
- definição de logs, auditoria e segurança quando forem recursos confirmados.

Se encontrar uma lacuna crítica, pare e faça apenas uma pergunta objetiva ao usuário.

Não gere o FSD enquanto essa lacuna crítica não for resolvida.

Se houver apenas pendências não bloqueantes, registre-as na seção "Pontos Pendentes e Decisões Futuras" do FSD.

Não faça perguntas sobre informações que já estejam claramente definidas nos documentos.

Não reabra decisões já confirmadas, a menos que exista conflito claro, impossibilidade técnica ou risco importante para implementação.

## Restrições importantes

Não crie código.

Não execute implementação.

Não invente funcionalidades.

Não altere decisões já consolidadas sem avisar.

Não mencione skills.

Não mencione subagentes.

Não recomende agentes especializados.

Não trate o PRD como documento necessário para implementação.

Não trate o `DECISOES_TECNICAS.md` como documento necessário para implementação.

Não inclua a conversa como documento necessário para implementação.

O FSD final deverá consolidar tudo dentro do próprio documento.

## Padrão arquitetural obrigatório

O sistema deverá usar a arquitetura definida no `DECISOES_TECNICAS.md`.

Esta arquitetura deverá ser desacoplada, dividindo o sistema em duas partes estritas:

- **Backend (API REST em Python):** Parte responsável pelos dados, regras de negócio e comunicação com o banco de dados. O backend não deve renderizar ou servir interface HTML.
- **Frontend (PWA client-side):** Parte responsável exclusivamente pela interface, consumo dos dados via API REST e lógicas de resiliência offline (Service Workers).

Explique no FSD como essa arquitetura desacoplada será aplicada conforme o framework Python escolhido.

A IA codificadora deverá manter separação clara entre dados, regras de negócio e interface, aplicando rigorosamente os conceitos de Orientação a Objetos (OOP) e encapsulamento no lado do servidor.

## Regras para estrutura de diretórios do projeto

Ao descrever a arquitetura do sistema, não use como nome principal expressões genéricas de servidores legados como:

- `[Diretório Público - public_html / public]`;
- `[Diretório Raiz Privado - Fora do acesso web]`;
- `public_html`;
- `public`;
- `htdocs`;
- `www`.

No FSD, use como referência principal a raiz do repositório:

`[Diretório do Projeto - Repositório]`

Explique que essa estrutura representa a organização do repositório do projeto, contendo a separação clara entre a aplicação de backend (Python) e o cliente frontend (PWA).

Quando sugerir a estrutura de pastas, use uma estrutura baseada no diretório do projeto, considerando a arquitetura desacoplada:

- **Backend (Python):** Organizado em pastas internas como `app/`, `core/`, `api/`, `models/`, `services/`, `database/`, `migrations/`, `logs/`, mantendo arquivos de execução como o ponto de entrada da API (ex: `main.py` ou `app.py`) e o gerenciamento de dependências.
- **Frontend (PWA):** Organizado em diretório próprio de arquivos estáticos client-side (HTML, CSS, JavaScript, Service Workers, `manifest.json` e assets).

O FSD deve orientar a IA codificadora a manter arquivos de configuração, credenciais, scripts de banco de dados, migrations e logs em pastas privadas dentro do backend, garantindo que o servidor WSGI/ASGI exponha apenas as rotas públicas de API e os ativos estáticos estritamente necessários para o PWA.

A aplicação não deve depender de servidores Apache ou arquivos `.htaccess`. A proteção de rotas e o controle de acesso a arquivos internos devem ser tratados nativamente pelo backend Python (middleware, autenticação de API, CORS) e pela correta configuração do ambiente de hospedagem/container.

## Conteúdo obrigatório do FSD

O FSD deve conter orientações suficientes para implementação de:

- estrutura geral do sistema;
- estrutura de diretórios do projeto;
- arquivo de configuração em código, sem uso de `.env`;
- proteção de arquivos internos contra acesso direto pelo navegador;
- migrations para criação e atualização da estrutura do banco de dados;
- forma segura de execução das migrations;
- banco de dados;
- autenticação;
- controle de acesso;
- cadastros;
- telas;
- formulários;
- listagens;
- validações;
- regras de negócio;
- fluxos principais;
- logs;
- auditoria;
- configurações globais;
- tratamento de erros;
- uploads e anexos, quando existirem;
- relatórios e exportações, quando existirem;
- APIs, quando existirem;
- integrações externas, quando existirem;
- critérios de implementação;
- critérios de validação;
- preparação da entrega.

Inclua somente recursos confirmados no PRD, no `DECISOES_TECNICAS.md`, no `DESIGN.md` ou necessários por coerência funcional.

Não inclua APIs, integrações externas, exportações, uploads ou anexos se eles não estiverem no escopo consolidado.

Respeite a seção de itens que não devem ser inventados do `DECISOES_TECNICAS.md`.

## Regras para banco de dados, migrations e desempenho

O FSD deve propor uma estrutura de banco de dados coerente com a stack definida, as entidades do sistema e as regras consolidadas.

Inclua:

- tabelas;
- campos principais;
- tipos de dados sugeridos;
- chaves primárias;
- chaves estrangeiras;
- índices importantes;
- constraints;
- campos de auditoria;
- campos de soft delete, quando aplicável;
- observações sobre integridade dos dados.

O FSD também deve especificar que o projeto deverá utilizar uma arquitetura de migrations para criação e atualização da estrutura do banco de dados.

Migration é um arquivo ou script versionado que ensina o sistema a criar ou alterar tabelas, campos, índices e constraints do banco de dados de forma controlada.

O objetivo das migrations é evitar que o usuário precise criar tabelas, campos e índices manualmente em um gerenciador de banco de dados.

O FSD deve orientar que as migrations incluam, quando aplicável:

- criação das tabelas;
- criação dos campos;
- definição de chaves primárias;
- definição de chaves estrangeiras;
- criação de índices;
- criação de constraints;
- campos de auditoria;
- campos de soft delete;
- dados iniciais obrigatórios, apenas quando forem realmente necessários.

O FSD deve especificar que as migrations devem ter controle para evitar execução duplicada.

A estratégia pode variar conforme a stack, mas o FSD deve orientar a IA codificadora a prever algum mecanismo de controle, como:

- tabela de controle de migrations executadas;
- scripts versionados;
- comando interno seguro;
- rotina administrativa protegida;
- outro mecanismo adequado à stack definida.

As migrations não devem ficar acessíveis diretamente pelo navegador.

Se as migrations ficarem dentro do `[Diretório do Projeto - Repositório]`, elas devem estar em uma pasta interna, como:

- `database/migrations/`;
- `app/database/migrations/`;
- ou estrutura equivalente conforme a stack.

O FSD deve orientar que essa pasta seja protegida contra acesso direto por URL.

As migrations devem ser executadas apenas por um meio controlado, como:

- script de linha de comando;
- rotina interna protegida;
- painel administrativo restrito a administradores, se essa estratégia for definida;
- comando específico da stack, quando existir.

Não oriente a execução pública de migrations por uma URL aberta no navegador.

Se houver uma tela ou rota para executar migrations, ela deve ser protegida por autenticação, permissão administrativa e bloqueios de segurança adequados. Mesmo assim, prefira execução controlada e não pública.

Inclua índices necessários para evitar lentidão em consultas, relatórios, dashboards, listagens e buscas frequentes.

Não crie SQL final completo, a menos que isso tenha sido solicitado pelo usuário.

O foco deve ser especificar o modelo de dados funcional e técnico em nível suficiente para orientar a IA codificadora, incluindo a necessidade de migrations para materializar essa estrutura no banco de dados.

## Regras para logs e contingência

Se o sistema tiver log de erros, descreva:

- quais erros serão registrados;
- quais informações devem ser gravadas;
- como o usuário verá mensagens seguras;
- quem poderá consultar os logs;
- onde o log será armazenado;
- como os logs serão protegidos.

Quando o log de erros for gravado em banco de dados, especifique também uma estratégia de contingência para registrar erro em arquivo quando:

- o banco de dados estiver indisponível;
- a conexão com o banco falhar;
- o próprio erro impedir o registro normal em banco;
- ocorrer falha crítica antes da inicialização completa do sistema.

O log em arquivo deve ser armazenado fora da pasta pública sempre que possível, com proteção contra acesso direto pela web.

Se o sistema tiver log de segurança, descreva eventos como:

- login inválido;
- acesso negado;
- bloqueio por tentativas;
- ação suspeita;
- alteração de permissões;
- exclusão de registros importantes;
- restauração de registros importantes;
- tentativas de acesso a arquivos protegidos.

## Regras para configuração e credenciais

O FSD deve especificar uma estratégia segura para arquivos de configuração do sistema.

Não use arquivo `.env` para armazenar credenciais neste projeto.

Mesmo que arquivos `.env` possam ser protegidos por configuração do servidor, um erro de configuração da hospedagem pode expor o conteúdo como texto diretamente no navegador.

Para reduzir esse risco no contexto deste treinamento, o FSD deve orientar o uso de um arquivo de configuração em código Python.

Use preferencialmente um arquivo como:

- `config/settings.py`;
- `core/config.py`.

Esse arquivo poderá armazenar, quando aplicável:

- dados de conexão com o banco de dados;
- credenciais de SMTP;
- flags de ativação de logs;
- configurações globais técnicas;
- parâmetros internos da aplicação.

O arquivo de configuração deve ficar dentro do `[Diretório do Projeto - Repositório]`, preferencialmente em uma pasta interna do backend.

O FSD deve deixar claro que esse arquivo não pode ser acessado diretamente pelo navegador (o servidor ASGI/WSGI jamais deve servir arquivos `.py` como estáticos públicos).

O acesso a esse arquivo deve ocorrer apenas por importação interna do código Python, como `import config` ou `from core.config import settings`.

O FSD também deve orientar que a IA codificadora garanta a proteção dessas pastas, configurando o ambiente para expor exclusivamente as rotas da API REST e o diretório de arquivos estáticos do frontend (PWA), mantendo toda a base de código do backend isolada de acessos web diretos.

## Regras para uploads, anexos e arquivos

Se houver upload de arquivos, descreva:

- onde os arquivos serão usados;
- tipos permitidos;
- tamanho máximo;
- local lógico de armazenamento;
- permissões;
- validações;
- regras de visualização;
- regras de download;
- regras de exclusão;
- preservação de arquivos quando houver auditoria ou vínculo histórico;
- riscos de segurança;
- proteção contra acesso direto indevido;
- validação de extensão e tipo real do arquivo.

Se não houver upload, declare que o recurso não faz parte da primeira versão.

## Regras para relatórios e exportações

Se houver relatórios, consultas avançadas ou exportações, descreva:

- objetivo;
- filtros;
- quais filtros são obrigatórios;
- quais filtros são opcionais;
- colunas;
- permissões;
- formatos de exportação;
- consistência entre tela e arquivo exportado;
- regras de segurança;
- índices necessários para evitar lentidão.

Se houver exportação CSV, especifique que os dados exportados devem respeitar os mesmos filtros e permissões da tela.

Se não houver exportação, declare que o recurso não faz parte da primeira versão.

## Estrutura obrigatória do FSD

Gere o FSD completo em Markdown usando exatamente a estrutura abaixo.

---

# DOCUMENTO DE ESPECIFICAÇÃO FUNCIONAL (FSD)

## 1. Visão Geral

Explique o sistema que será criado de forma consolidada.

Inclua:

- nome do sistema;
- objetivo principal;
- resumo do funcionamento;
- público usuário;
- contexto de uso;
- observações relevantes para implementação.

## 2. Documentos do Projeto para Implementação

Liste apenas os documentos que a IA codificadora deverá usar para implementar o sistema.

Inclua:

- `docs/FSD.md`;
- `docs/DESIGN.md`, se tiver sido fornecido.

Não inclua `PRD.md` como documento necessário para a IA codificadora.

Não inclua `DECISOES_TECNICAS.md` como documento necessário para a IA codificadora.

Informe que o FSD já consolida as decisões técnicas e funcionais necessárias para implementação.

## 3. Stack Definida

Descreva a stack escolhida.

Inclua:

- linguagem de programação;
- banco de dados;
- tecnologias de interface;
- bibliotecas ou frameworks;
- dependências importantes;
- padrão arquitetural;
- restrições técnicas;
- observações sobre uso local de bibliotecas, quando aplicável.

## 4. Ambientes do Projeto

Descreva os ambientes definidos.

Inclua:

- desenvolvimento local;
- testes ou homologação;
- produção;
- observações sobre deploy.

## 5. Arquitetura do Sistema

Descreva como a arquitetura desacoplada definida (Backend em Python + Frontend PWA) será aplicada no projeto.

Use como referência principal:

`[Diretório do Projeto - Repositório]`

Não use como nome principal da estrutura termos genéricos de servidores legados como:

- `[Diretório Público - public_html / public]`;
- `[Diretório Raiz Privado - Fora do acesso web]`;
- `public_html`;
- `public`;
- `htdocs`;
- `www`.

Explique que o `[Diretório do Projeto - Repositório]` representa a estrutura unificada do repositório, contendo a aplicação de backend (Python) e os ativos do frontend client-side (PWA).

O FSD deve explicar detalhadamente a arquitetura desacoplada:

- onde ficarão os Models/ORM e os Schemas de dados;
- onde ficarão as regras de negócio e os serviços do domínio;
- onde ficarão os Endpoints/Rotas da API REST;
- onde ficarão as Views da interface gráfica, scripts Vanilla JS e Service Workers do PWA;
- como as requisições devem fluir pelo sistema (Frontend consumindo API REST via JSON);
- como as regras de negócio devem ser organizadas no backend;
- como evitar mistura indevida entre banco de dados, regras de negócio e interface gráfica;
- como arquivos de configuração, scripts de migração e assets do PWA devem ser organizados.

Inclua uma sugestão de estrutura de diretórios compatível com o projeto, usando o `[Diretório do Projeto - Repositório]` como raiz.

A estrutura deve prever:

- arquivo de entrada da API no backend (ex: `main.py` ou `app.py`);
- pasta de configuração do backend, como `core/` ou `config/`;
- pasta de módulos da aplicação, contendo `models/`, `api/` (rotas/controllers), `services/`;
- pasta de banco de dados e migrations (ex: `database/migrations/` ou `alembic/`);
- pasta de logs do sistema (quando houver logs em arquivo);
- pasta de ativos estáticos do frontend/PWA (HTML, CSS, JS, Service Worker e `manifest.json`).

O FSD deve deixar claro que arquivos de código Python (`.py`), pastas internas do backend (`config/`, `models/`, `services/`, `database/`, `migrations/`) e arquivos de `logs/` jamais devem ser servidos diretamente como arquivos estáticos públicos pela web.

O FSD deve orientar a IA codificadora a proteger essas pastas conforme a stack Python e o servidor de aplicação (ASGI/WSGI) utilizados.

A proteção não deve depender de servidores Apache ou arquivos `.htaccess`. O isolamento deve ser garantido nativamente pela estrutura da aplicação Python e pela correta exposição de rotas e estáticos.

Também explique que arquivos de configuração com credenciais devem usar código Python, como `config/settings.py` ou `core/config.py`, e não arquivo `.env`.

## 6. Escopo Funcional da Primeira Versão

Liste as funcionalidades que fazem parte da primeira versão.

Agrupe por módulos ou áreas funcionais.

Para cada funcionalidade, descreva:

- objetivo;
- usuários envolvidos;
- ações permitidas;
- resultado esperado;
- dependências com outras funcionalidades;
- regras relacionadas.

## 7. Fora de Escopo

Liste funcionalidades, ideias ou recursos que não fazem parte da primeira versão.

Explique brevemente por que ficaram fora, quando essa informação existir.

## 8. Perfis de Usuário e Permissões

Descreva todos os perfis de usuário.

Para cada perfil, informe:

- descrição;
- permissões;
- restrições;
- áreas acessíveis;
- ações bloqueadas.

Inclua uma matriz de permissões quando fizer sentido.

## 9. Recursos Estruturais do Sistema

Descreva os recursos estruturais definidos para o sistema.

Inclua somente recursos confirmados ou necessários conforme as decisões consolidadas.

Possíveis recursos:

- autenticação;
- RBAC;
- auditoria;
- soft delete;
- log de erros;
- log de segurança;
- configurações globais;
- uploads e anexos;
- exportações;
- APIs;
- integrações externas.

Para cada recurso incluído, explique:

- objetivo;
- onde será aplicado;
- comportamento esperado;
- permissões envolvidas;
- cuidados de segurança;
- critérios de validação.

## 10. Entidades do Sistema

Liste as entidades principais do sistema.

Para cada entidade, descreva:

- nome;
- finalidade;
- principais informações;
- relacionamentos funcionais;
- regras de criação, edição, exclusão e visualização;
- se usa soft delete;
- se usa auditoria;
- permissões de acesso;
- observações.

Não crie entidades desnecessárias.

## 11. Modelo de Dados Proposto

Proponha uma estrutura de banco de dados coerente com a stack definida, as entidades do sistema e as regras consolidadas.

Inclua:

- tabelas;
- campos principais;
- tipos de dados sugeridos;
- chaves primárias;
- chaves estrangeiras;
- índices importantes;
- constraints;
- campos de auditoria;
- campos de soft delete, quando aplicável;
- observações sobre integridade dos dados.

Também descreva a estratégia de migrations do projeto.

Explique que as migrations serão usadas para criar e atualizar a estrutura do banco de dados sem exigir que o usuário crie tabelas e índices manualmente.

Informe que as migrations devem contemplar, quando aplicável:

- criação das tabelas;
- criação dos campos;
- criação de chaves primárias;
- criação de chaves estrangeiras;
- criação de índices;
- criação de constraints;
- criação de campos de auditoria;
- criação de campos de soft delete.

Explique como o projeto deverá evitar a execução duplicada das migrations.

Informe que as migrations devem ficar em uma pasta interna do projeto, como `database/migrations/` ou estrutura equivalente.

Deixe claro que as migrations não devem ser acessíveis diretamente pelo navegador.

Explique que a execução das migrations deve acontecer por meio controlado e seguro, conforme a stack definida.

## 12. Módulos e Telas

Liste os módulos e telas necessários.

Para cada tela ou módulo, descreva:

- objetivo;
- usuários que acessam;
- principais ações;
- principais campos ou informações exibidas;
- filtros e buscas;
- botões e ações;
- mensagens esperadas;
- estados importantes, como vazio, erro, sucesso, carregando ou sem permissão;
- relação com o `docs/DESIGN.md`, quando disponível.

Não defina layout visual detalhado se isso já estiver no `docs/DESIGN.md`.

## 13. Fluxos Funcionais

Descreva os fluxos principais do sistema em passo a passo.

Para cada fluxo, informe:

- perfil que executa;
- pré-condições;
- passo a passo;
- resultado esperado;
- erros possíveis;
- regras de permissão;
- logs ou auditoria gerados, quando aplicável.

## 14. Validações e Regras de Negócio

Liste as validações e regras de negócio por módulo ou entidade.

Inclua:

- campos obrigatórios;
- formatos válidos;
- limites;
- bloqueios;
- permissões;
- regras de status;
- regras de alteração;
- regras de exclusão;
- mensagens de erro esperadas;
- comportamentos em situações especiais.

## 15. Autenticação e Sessão

Se o sistema tiver autenticação, descreva:

- tipo de autenticação;
- fluxo de login;
- fluxo de logout;
- recuperação de acesso, se existir;
- bloqueio por tentativas, se existir;
- tempo de sessão, se definido;
- proteção de rotas;
- comportamento para usuário sem permissão.

Se o sistema não tiver autenticação, justifique com base nas decisões consolidadas.

## 16. Controle de Acesso

Se o sistema tiver perfis, papéis ou permissões, descreva:

- papéis;
- permissões;
- matriz de acesso;
- menus por perfil;
- telas bloqueadas;
- ações protegidas;
- validação no backend;
- mensagens para acesso negado.

## 17. Auditoria e Histórico

Se o sistema tiver auditoria, descreva:

- quais registros serão auditados;
- quais ações serão registradas;
- quais campos mínimos serão usados;
- quem pode visualizar auditoria;
- como a auditoria aparece nos CRUDs;
- regras de retenção, se houver.

## 18. Soft Delete e Exclusões

Se o sistema permitir exclusão de registros, descreva:

- quais entidades usam soft delete;
- quem pode excluir;
- quem pode restaurar;
- quem pode excluir definitivamente, se permitido;
- como registros excluídos aparecem ou deixam de aparecer;
- filtros necessários;
- cuidados contra exclusão indevida.

## 19. Logs

Descreva os logs necessários.

Separe, quando aplicável:

### Log de erros

Explique quais erros serão registrados, quais informações devem ser gravadas, como o usuário verá mensagens seguras e quem poderá consultar os logs.

Quando o log de erros for gravado em banco de dados, especifique uma estratégia de contingência para registrar erro em arquivo quando o banco estiver indisponível ou o erro impedir o registro normal.

O log em arquivo deve ser armazenado fora da pasta pública sempre que possível, com proteção contra acesso direto pela web.

### Log de segurança

Explique quais eventos de segurança serão registrados, como login inválido, acesso negado, bloqueio por tentativas ou ação suspeita.

## 20. Configurações Globais

Se houver configurações globais, descreva:

- quais configurações existirão;
- valores padrão;
- quem pode alterar;
- impacto de cada configuração;
- validações;
- fallback quando uma configuração estiver ausente.

Descreva também a estratégia de configuração técnica do projeto.

O FSD deve deixar claro que credenciais e parâmetros técnicos sensíveis não devem ser armazenados em arquivo `.env`.

Use arquivo de configuração em código Python.

Use preferencialmente um arquivo como:

- `config/settings.py`;
- `core/config.py`.

Esse arquivo poderá conter, quando aplicável:

- dados de conexão com o banco de dados;
- credenciais SMTP;
- flags de logs;
- parâmetros técnicos internos;
- configurações globais não editáveis pela interface.

O arquivo de configuração deve ficar dentro do `[Diretório do Projeto - Repositório]`, preferencialmente em uma pasta interna do backend (ex: `config/` ou `core/`).

O FSD deve orientar que esse arquivo não seja acessível diretamente pelo navegador (o servidor ASGI/WSGI jamais deve servir arquivos `.py` como estáticos públicos).

A aplicação deve carregar esse arquivo apenas internamente, por importação do código Python, como `import config` ou `from core.config import settings`.

O FSD também deve orientar a correta exposição apenas da API REST e dos ativos estáticos do frontend (PWA), mantendo toda a base de código do backend isolada de acessos web diretos sem a necessidade de depender de arquivos `.htaccess`.

## 21. Uploads, Anexos e Arquivos

Se houver upload de arquivos, descreva:

- onde os arquivos serão usados;
- tipos permitidos;
- tamanho máximo;
- local lógico de armazenamento;
- permissões;
- validações;
- regras de visualização e download;
- exclusão ou preservação;
- riscos de segurança.

Se não houver upload, declare que o recurso não faz parte da primeira versão.

## 22. Relatórios, Consultas e Exportações

Se houver relatórios, consultas avançadas ou exportações, descreva:

- objetivo;
- filtros;
- quais filtros são obrigatórios;
- quais filtros são opcionais;
- colunas;
- permissões;
- formatos de exportação;
- consistência entre tela e arquivo exportado;
- regras de segurança;
- índices necessários para evitar lentidão.

Se não houver exportação, deixe claro.

## 23. APIs e Integrações Externas

Se houver APIs ou integrações, descreva:

- objetivo;
- sistemas envolvidos;
- dados enviados;
- dados recebidos;
- autenticação;
- autorização;
- tratamento de falhas;
- logs;
- retries;
- idempotência, quando aplicável.

Se não houver APIs ou integrações, declare que não fazem parte da primeira versão.

## 24. Segurança Funcional

Descreva cuidados de segurança funcionais.

Inclua, quando aplicável:

- proteção de rotas;
- validação de permissões no backend;
- proteção contra acesso indevido;
- cuidado com dados sensíveis;
- cuidado com mensagens de erro;
- proteção de uploads;
- proteção de exportações;
- registro de eventos sensíveis;
- revisão de segurança recomendada.

## 25. Organização Sugerida da Implementação

Sugira uma divisão de implementação para a IA codificadora.

Divida em etapas pequenas, progressivas e testáveis.

A organização sugerida deve considerar que o projeto será criado inicialmente num ambiente de desenvolvimento local Python (utilizando ambientes virtuais como `venv` e o servidor ASGI/WSGI nativo do framework).

Use como referência o `[Diretório do Projeto - Repositório]`, que representa a raiz do projeto versionado, contendo a separação clara entre backend e frontend (PWA).

Exemplo de organização:

1. preparação do `[Diretório do Projeto - Repositório]`;
2. criação da estrutura inicial de pastas desacoplada (backend e frontend/PWA);
3. configuração inicial do ambiente virtual Python e instalação de dependências;
4. criação do arquivo de configuração em código Python (ex: `config/settings.py`), sem uso de `.env`;
5. isolamento do backend e configuração das rotas públicas exclusivas para a API e PWA;
6. definição da estrutura arquitetural base (modelos, serviços, controladores/rotas);
7. configuração da conexão com o banco de dados;
8. criação da estrutura de migrations;
9. criação das migrations iniciais de tabelas, campos, índices e constraints;
10. definição do mecanismo de controle e execução segura de migrations;
11. autenticação e segurança da API (ex: emissão e validação de tokens);
12. controle de acesso e permissões (RBAC);
13. desenvolvimento dos endpoints de recursos estruturais;
14. desenvolvimento das APIs das entidades principais (CRUDs);
15. estruturação do Frontend client-side (PWA, Service Workers, cache offline);
16. integração dos fluxos funcionais entre Frontend e API REST;
17. relatórios e consultas (backend gerando dados, frontend exibindo);
18. uploads, se existirem;
19. exportações, se existirem;
20. integrações externas, se existirem;
21. configuração de logs de erros e segurança (com contingência em arquivo);
22. revisão de segurança e performance da API;
23. revisão de qualidade do código e testes locais;
24. preparação da entrega e deploy para ambiente Cloud (PaaS).

Adapte a lista ao sistema especificado no FSD.

## 26. Critérios de Aceitação Técnica e Funcional

Liste critérios para considerar o sistema pronto.

Inclua critérios como:

- funcionalidades principais implementadas;
- arquitetura definida respeitada;
- responsabilidades separadas conforme o padrão escolhido;
- permissões respeitadas;
- validações funcionando;
- banco de dados coerente;
- índices criados para consultas críticas;
- logs funcionando;
- log de contingência em arquivo funcionando, quando aplicável;
- auditoria funcionando, se aplicável;
- soft delete funcionando, se aplicável;
- telas aderentes ao `docs/DESIGN.md`, se disponível;
- erros tratados de forma segura;
- ausência de funcionalidades inventadas fora do FSD;
- revisão de segurança concluída;
- revisão de qualidade concluída;
- estrutura do projeto organizada a partir do `[Diretório do Projeto - Repositório]`;
- ausência de dependência de nomes fixos como `public_html`, `public`, `htdocs` ou `www` dentro da arquitetura do FSD;
- arquivo de configuração em código criado e protegido, sem uso de `.env`;
- credenciais sensíveis não expostas em arquivos acessíveis diretamente pelo navegador;
- pastas internas protegidas contra acesso direto por URL;
- migrations criadas para estrutura do banco de dados;
- migrations contemplando tabelas, campos, índices e constraints necessários;
- mecanismo definido para evitar execução duplicada de migrations;
- migrations não acessíveis diretamente pelo navegador;
- execução de migrations feita por meio controlado e seguro.

## 27. Pontos Pendentes e Decisões Futuras

Liste dúvidas, decisões abertas ou melhorias futuras.

Se não houver pendências, declare explicitamente:

"Não foram identificadas pendências para iniciar a codificação com base neste FSD."

Não use esta seção para jogar decisões essenciais para depois.

Se a decisão for necessária para iniciar a codificação com segurança, pergunte antes de gerar o FSD.

## 28. Conclusão

Finalize explicando se o FSD está pronto para orientar uma IA codificadora.

Declare também quais documentos devem ser entregues para a IA codificadora junto com o FSD:

- `docs/FSD.md`;
- `docs/DESIGN.md`, se disponível.

Não inclua `PRD.md` como documento necessário para a IA codificadora.

Não inclua `DECISOES_TECNICAS.md` como documento necessário para a IA codificadora.

---

## Regras finais

Gere o FSD em Markdown.

Não crie código neste momento.

Não execute a implementação.

Não invente requisitos.

Não altere decisões consolidadas sem avisar.

Não mencione skills ou subagentes.

Quando houver dúvida, registre como ponto pendente apenas se ela não bloquear a codificação. Se bloquear, pergunte antes de gerar o FSD.

O FSD deve orientar a IA codificadora a manter separação clara de responsabilidades conforme a arquitetura desacoplada definida (Backend API REST + Frontend PWA).

O FSD deve ser detalhado o suficiente para que uma IA codificadora consiga implementar o sistema lendo o próprio FSD e o `docs/DESIGN.md` quando disponível.

O FSD final não deve depender do `PRD.md` para implementação.

O FSD final não deve depender do `DECISOES_TECNICAS.md` para implementação.

O FSD final não deve depender da conversa anterior para implementação.

O conteúdo relevante dos documentos de entrada deve estar consolidado diretamente nas seções do FSD.

O FSD deve evitar estruturas de diretório que dependam de pastas públicas fixas de servidores legados, como `public_html`, `public`, `htdocs` ou `www`.

Use sempre `[Diretório do Projeto - Repositório]` como referência principal de raiz do projeto.

O FSD deve considerar que o sistema será criado inicialmente em ambiente de desenvolvimento local (usando ambientes virtuais Python e servidores nativos) e poderá depois ser publicado em plataformas Cloud (PaaS).

O FSD não deve recomendar o uso de arquivo `.env` para credenciais neste projeto de treinamento.

O FSD deve recomendar arquivo de configuração em código nativo, preferencialmente `config/settings.py` ou `core/config.py`.

O FSD deve exigir migrations para criação e atualização da estrutura do banco de dados (ex: via Alembic ou equivalente do framework escolhido).

O FSD deve deixar claro que arquivos de configuração, scripts de migrations e arquivos internos do backend (`.py`) jamais podem ser acessados diretamente pelo navegador web.