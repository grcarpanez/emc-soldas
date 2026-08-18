# DECISÕES TÉCNICAS DO PROJETO

## 1. Documentos recebidos

* O documento funcional `PRD.md` foi recebido e analisado com sucesso.
* O documento de interface `DESIGN.md` foi recebido e analisado com sucesso.
* **Observações relevantes:** Ambos os documentos são coesos e delimitam claramente o escopo funcional da V1 (sem integrações bancárias ou fiscais automáticas, sem auto-cadastro de clientes) e a diretriz visual (*Industrial Integrity* com bordas rígidas e tema escuro).

## 2. Identificação do sistema

* **Nome do Sistema:** EMC Soldas
* **Objetivo Principal:** Organizar o fluxo financeiro e operacional da oficina, unindo orçamentos (chão de fábrica) ao faturamento (financeiro), controlando custos e maximizando lucros.
* **Público Usuário (v1):** Equipe interna (Administradores e Operadores). Acesso restrito por convite.
* **Contexto de Uso:** Uso híbrido (computadores de escritório e celulares/tablets no pátio da oficina sujeitos a oscilação de internet).
* **Resumo Funcional:** Criação dinâmica de orçamentos, faturamento aglutinado (conta corrente do cliente), recebimentos parciais, controle de custos via "snapshot" e conciliação bancária manual (OFX/CSV).

## 3. Decisões técnicas confirmadas

### Stack e Ambientes

* **Linguagem Backend:** Python.
* **Framework Backend:** Django (com Django REST Framework para APIs).
* **Banco de Dados:** MySQL.
* **Tecnologias de Interface:** PWA com Frontend desacoplado (HTML, CSS, Vanilla JS) consumindo a API REST.
* **Ambiente Local:** XAMPP (MySQL) + Servidor Nativo do Django.
* **Ambiente de Testes:** Não haverá ambiente em nuvem na V1. Testes locais apenas.
* **Ambiente de Produção:** Plataforma Cloud PaaS (ex: Render ou PythonAnywhere), com arquitetura preparada para migração futura para AWS.

### Autenticação e Usuários

* **Tipo de Autenticação:** E-mail e senha, restrito a convidados (sem auto-cadastro).
* **Perfis e Permissões:** Controle Baseado em Papéis (RBAC) com dois níveis estritos: Administrador e Operador.

### Arquitetura, Dados e Segurança

* **Soft Delete:** Obrigatório. Nenhuma exclusão real ocorre no banco, preservando o histórico para relatórios antigos.
* **Snapshot de Custos:** Ao orçar um serviço, os valores de custo e venda são congelados naquele milissegundo, desvinculando reajustes futuros do catálogo.
* **Log de Auditoria:** Registro silencioso obrigatório de "Quem criou/atualizou/inativou" e "Quando" em todos os eventos do sistema.
* **Log de Erros:** Gravação física em arquivos (fora do acesso web público), segmentados por data, com retenção configurável e expurgo deliberado restrito ao Administrador.

### Arquivos e Exportações

* **Uploads:** PDFs (DANFE, comprovantes bancários) e arquivos de conciliação (OFX/CSV).
* **Exportações:** PDF e CSV para relatórios financeiros e orçamentos comerciais.
* **Design PDF:** O documento gerado para o cliente não deve renderizar o campo desconto caso ele seja nulo ou zero.

## 4. Decisões adotadas por padrão (com autorização)

* **Django:** Adotado como padrão por ser a opção mais robusta em Python para tratar o RBAC, ORM e as pesadas lógicas de negócio de um ERP.
* **Testes Locais:** Adotado o padrão de simplificar o fluxo de *deploy* da v1, sem ambiente de *staging*.
* **PaaS (Render/PythonAnywhere):** Adotado como porta de entrada de baixo custo e fácil manutenção, postergando a complexidade da AWS.
* **Comunicação PWA Desacoplada (Vanilla JS + API REST):** Escolhida expressamente para garantir a resiliência offline exigida pelo uso no pátio e a segurança dos dados.

## 5. Arquitetura e Padrões

O sistema seguirá rigorosamente a arquitetura provida pelo ecossistema Django/DRF, respeitando as seguintes premissas obrigatórias no FSD:

* **Orientação a Objetos (OOP):** O código deve ser estruturado usando *Class-Based Views* e *Models* bem definidos.
* **Separação de Responsabilidades (Separation of Concerns):** A lógica de interação com o banco (*Models*), a regra de negócio/API (*Views/Serializers*) e o *Frontend* (consumidor REST) devem estar completamente isolados.
* **Desacoplamento:** O Django não renderizará telas HTML. Ele funcionará puramente como um fornecedor de JSON.

## 6. Recursos estruturais definidos

* **Autenticação JWT/Session:** Necessário definir no FSD como o frontend PWA manterá o usuário logado com segurança consumindo a API.
* **Service Workers:** Responsáveis pelo cacheamento de interface e avisos de perda de conexão da internet.
* **Dicionário de Atributos:** Tabela centralizada (chave-valor) para evitar erros de digitação na composição das fichas de produtos/itens.

## 7. Perfis e permissões em nível alto

* **Administrador:** Acesso absoluto. Gerencia configurações globais, dita o tempo de log, convida/rebaixa usuários e aplica restauração (Soft Delete) de qualquer registro.
* **Operador:** Linha de frente. Realiza toda a rotina financeira (orçamentos, faturas, conciliação). Não gerencia usuários, não edita configurações globais e só pode restaurar registros que ele mesmo excluiu.

## 8. Entidades prováveis em nível alto (para o FSD)

* Usuários (Equipe)
* Clientes e Fornecedores
* Equipamentos/Veículos (com tabela de Log de Vínculos/Transferência)
* Produtos e Itens (com vínculo ao Dicionário de Atributos)
* Orçamentos (Status Operacional Duplo, Snapshots de Valores)
* Faturas (Aglutinador de orçamentos)
* Lançamentos Financeiros (Contas a Pagar/Receber, Recebimentos Parciais)
* Contas Bancárias, Categorias e Formas de Pagamento
* Documentos Fiscais (Armazenamento de XML/PDF)

## 9. Módulos, telas e fluxos esperados em nível alto (para o FSD)

* **Login & Dashboard:** Painel executivo com *Flip Cards* de metas, orçamentos atrasados e relatórios de fluxo de caixa.
* **Operação Comercial:** Criação de orçamentos dinâmicos (texto livre ou catálogo) com alertas de inadimplência e alertas de margem de custo.
* **Workflow Oficina:** Painel estilo *Kanban/List* acompanhando status do orçamento (Gerado a Concluído).
* **Faturamento (Conta Corrente):** Seleção múltipla de orçamentos via *checkbox* para gerar a Fatura consolidada e informar pagamentos parciais.
* **Financeiro Interno:** Lançamentos de caixa avulsos, transferências e conciliação bancária (CSV/OFX) com ferramenta de "match" de linhas.
* **Administração:** Configurações globais e políticas de retenção/expurgo de *logs*.

## 10. Alertas para relatórios, consultas, exportações e desempenho

* **Filtros Frequentes:** O FSD deverá prever índices de banco de dados, especialmente para consultas de *status* de orçamentos e filtro por datas (vencimentos e conciliações).
* **Consulta Pesada:** A tela de Faturamento Agregado buscará diversos orçamentos simultâneos e executará matemática no frontend; a API deve fornecer os dados já higienizados.
* **Exportações:** PDF de orçamento precisa ser gerado sob demanda, suprimindo logicamente campos zerados (desconto).

## 11. Alertas para uploads, anexos e arquivos

* **PDFs/XML:** Utilizados para cadastro de documentos fiscais e faturas de cartão.
* **CSV/OFX:** Utilizados para a conciliação bancária.
* O FSD deve detalhar o tamanho máximo dos arquivos, os tipos mime (MIME types) permitidos e garantir que esses arquivos fiquem protegidos contra acesso público via URL direta.

## 12. Alertas para logs, auditoria e segurança

* **Auditoria de Banco:** O FSD deve prever os campos `created_by`, `updated_by`, `deleted_by` e os respectivos *timestamps* em todas as entidades cruciais.
* **Limpeza de Log:** A regra de expurgo (ex: mudar de 90 para 30 dias) exige um fluxo de confirmação estrito de segurança (retroagir ou aplicar apenas aos novos).
* **Contingência:** Os logs físicos de desenvolvedor devem ser gravados em diretório protegido; caso o servidor falhe, garantir que não derrube a aplicação principal.

## 13. Itens que não devem ser inventados no FSD

* Controle Físico Avançado de Estoque (Baixa metro a metro).
* Integrações diretas via API com Bancos (Open Finance) ou Receita Federal/SEFAZ.
* Área Logada Externa para Clientes Finais.
* Apontamento Industrial de Tempo (Timesheet em tempo real de funcionários).
* *Hard Delete* (Deleção permanente de registros de usuários ou orçamentos do banco).
* Qualquer tipo de auto-cadastro na tela de login.

## 14. Pendências não bloqueantes

Não foram identificadas pendências não bloqueantes para a criação do FSD. Todas as definições de infraestrutura, arquitetura de PWA e segurança foram validadas.

## 15. Pronto para o FSD

As decisões técnicas estão prontas e consolidadas.
O próximo passo será gerar o arquivo final: `docs/FSD.md`.

O FSD deverá ser criado com base estrita no `PRD.md`, nestas `DECISOES_TECNICAS.md` e na estética funcional do `DESIGN.md`. Deverá, inclusive, contemplar uma sugestão de particionamento da codificação em etapas lógicas para alimentar a IA codificadora.