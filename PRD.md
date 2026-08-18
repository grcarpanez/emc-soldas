# DOCUMENTO DE REQUISITOS DO PRODUTO (PRD)

## 1. Visão Geral do Produto

O sistema, que receberá o nome **EMC Soldas** , será uma aplicação web ERP de gestão modular, voltada para otimizar as operações diárias e financeiras da empresa. O sistema será focado em dispositivos variados (PWA, responsivo para uso em computadores, celulares, tablets, até mesmo no pátio da oficina).

O público principal que usará o sistema, nessa primeira versão (v1), será exclusivamente a equipe interna da empresa (colaboradores autorizados e gestores), com previsão para acesso do cliente, à sua área logada, onde ele poderá acompanhar seus orçamentos, status individuais, faturamento e informações pertinentes à sua conta.

O principal benefício esperado é conectar o processo operacional do chão de fábrica (orçamentos de serviços de solda, embuchamento, usinagem) ao departamento financeiro de forma simples e visual. O sistema visa garantir maior previsibilidade nos recebimentos, acompanhamento de custos de materiais e agilidade nas cobranças, sem jargões contábeis complexos.


## 2. Problema que o Sistema Resolve

Atualmente, sem a centralização tecnológica adequada, empresas desse setor enfrentam dificuldades operacionais e financeiras críticas, tais como:

* O controle de orçamentos se perde ou fica fragmentado, dificultando saber com exatidão o que está pendente, o que está na oficina em execução e o que já pode ser faturado.
* Há grande retrabalho comercial quando clientes recorrentes aprovam vários pequenos serviços ao longo do mês, exigindo que a oficina agrupe os serviços prestados manualmente para cobrar o cliente de uma só vez.
* É difícil prever se a precificação da oficina está dando lucro ou prejuízo, devido à falta de registros rápidos sobre altas nos preços dos materiais de consumo e insumos.
* A equipe corre o risco de iniciar serviços para clientes que estão com pagamentos atrasados ou inadimplentes, devido à falta de avisos preventivos na hora da cotação.


## 3. Objetivos do Sistema

### Objetivo principal

Organizar o dia a dia da empresa de forma visual e prática, unindo a gestão de orçamentos operacionais ao controle financeiro e calculando custos para maximizar lucros. Versões futuras têm previsão de controle de estoque e controles fiscais e financeiros mais complexos integrados, como emissão de nota fiscal através de API, conciliação de extrato, conexão via Open Finance.

### Objetivos específicos

* Substituir cotações informais por orçamentos profissionais em PDF, acompanhando o status dos fluxos de produção e financeiro desde a sua abertura até a finalização.
* Controlar a "conta corrente" do cliente, permitindo o acúmulo de serviços prontos para um faturamento unificado.
* Centralizar despesas, receitas, contas bancárias, cartões de crédito e categorias para simplificar a resposta a perguntas como "O saldo é positivo?" ou "Quais receitas estão pendentes?", "Qual o saldo unificado das contas?", "Qual o saldo unificado das faturas de cartão?", "Qual a previsão de valor da fatura do cartão x no fechamento?".
* Rastrear a variação dos preços de compra nos fornecedores, justificando eventuais reajustes nos valores dos serviços prestados.


## 4. Personas e Perfis de Usuário

Na v1, o sistema não permitirá auto-cadastro e o acesso é restrito aos colaboradores convidados. Planejaremos para a v2, incrementação de área de cadastro, login com OAuth, utilizando login com conta Google ou cadastro por e-mail e senha e efetivação em duas etapas obrigatória (2FA).

| Perfil | Descrição simples | Principais ações no sistema | Permissões básicas |
| --- | --- | --- | --- |
| **Administrador** | Gestor principal com acesso total ao sistema. | Aprova entradas de novos usuários, gerencia todas as configurações globais, dita tempo de log e possui poder total de restauração de dados. | Pode fazer tudo no sistema. É o único que cria usuários e edita parâmetros globais de configuração.|
| **Operador** | Colaborador da operação diária, linha de frente do caixa e da oficina. | Cadastra clientes, equipamentos, orçamentos, lançamentos financeiros, altera status dos serviços e emite fechamentos de fatura. | Opera toda a rotina financeira e de cadastro. Pode restaurar apenas os registros que ele mesmo excluiu. Não pode acessar configs globais nem gerir usuários. |

## 5. Escopo da Primeira Versão

As funcionalidades estão divididas pelas seguintes áreas operacionais da EMC Soldas:

**Cadastros Básicos**

* **Gestão de Categorias, Contas, Cartões e Formas de Pagamento:** Permite configurar a espinha dorsal financeira (dinheiro, Pix, banco, despesas fixas).

* **Gestão de Clientes e Fornecedores (CRUD):** Cadastro completo contendo CNPJ, Razão Social, Nome Fantasia, contato (responsável), telefones (com flag de whatsapp), e-mail, endereço, equipamentos e anotações. No fornecedor, inclui o registro das entradas de insumos (compras) para observar a variação de preço dos materiais.

* **Cadastro de Equipamentos/Veículos e Histórico de Propriedade:** Cadastro completo contendo Placa, Identificação,  Descrição e Observação. O equipamento pode ser avulso ou vinculado a um ou múltiplos clientes simultaneamente (ex: frotas terceirizadas). Para evitar perda de histórico (ex: quando um caminhão é vendido de um cliente para outro), o sistema manterá um Log de Transferência/Vínculos. Alterar o dono de um equipamento hoje não alterará o cliente impresso em orçamentos do passado. A edição dos dados físicos do equipamento só ocorre em sua área própria, enquanto a vinculação ocorre na ficha do cliente.

* **Gestão de Itens e Produtos (CRUD com Dicionário de Atributos):** Cadastros contendo campos fixos (Descrição, Preços, Históricos de compra/venda). Para evitar poluição visual e erros de digitação (ex: "altura" vs "ALTURA"), o sistema possuirá um Dicionário de Atributos centralizado. O usuário poderá criar atributos padronizados (ex: Peso, Altura, Espessura) de forma universal. Ao cadastrar um novo Item ou Produto, a interface exibirá um botão "+" e um combobox listando esse dicionário. O usuário seleciona apenas os atributos pertinentes àquele item específico, preenche o valor, e apenas esses campos farão parte da ficha daquele material. Além dos itens físicos, o cadastro incluirá o campo "Tempo Estimado de Execução". O Preço de Custo do Produto será calculado automaticamente pela fórmula: (Soma do custo dos Itens) + (Tempo de Execução × Taxa da Mão de Obra definida pelo Admin).

* **Gestão Financeira de Clientes:** Área dedicada à geração e controle de orçamentos, agregação de orçamentos para geração de faturas, upload do PDF da nota fiscal e boletos emitidos para o cliente com vinculação de ORÇAMENTO-NOTA-BOLETO-COMPROVANTE, montando o fluxo financeiro completo, desde a geração de uma expectativa de receita até o controle de recebimento do pagamento do cliente, sendo o comprovante opcional (no caso de boleto, por exemplo, não temos comprovante, no caso de pix, o cliente pode enviar um comprovante). A liquidação do pagamento não depende da inserção de um comprovante de pagamento.

* **Gestão de Documentos Fiscais:** O sistema deve ter uma área de cadastro de documentos fiscais para importação do PDF da DANFE e xml das notas de compra (que serão utilizados para alimentação de estoque na v2).


**Operação Principal (Gestão de Orçamentos)**

* **Elaboração Dinâmica:** Inclusão de itens no orçamento podendo ser de forma flexível usando campos de texto descritivos, valores numéricos livres, quantidade e também podendo ser inseridos tanto itens quanto produtos no orçamento, vindo com o valor pré-preenchido com o valor de compra do item ou com o valor de custo do produto.

* **Validade e Desconto:** Controle automático de prazo de vencimento da cotação (padrão de 15 dias, prorrogável e personalizável na área restrita do Administrador) e capacidade de aplicar descontos, garantindo que o campo desconto não apareça no PDF impresso gerado para o cliente, caso não tenha nehum desconto preenchido.

* **Valores e Forma de Pagamento:** Opção de inserir mais de uma forma de pagamento, personalizável no orçamento, com possibilidade de inserir descontos personalizáveis para cada forma de pagamento. As formas de pagamento com seus respectivos descontos devem vir de um cadastro, que deve ser feito em uma área específica de configuração do sistema, sendo permitido ao usuário alterar o dado padrão no momento de lançar no orçamento as formas de pagamento.

* **Geração e Compartilhamento de PDF:** Emissão de um PDF profissional com a identidade da empresa para o usuário salvar no dispositivo ou enviar manualmente ao cliente pelas ferramentas nativas do seu próprio dispositivo. (Prevendo para a v2 envio automático opcional pelo whatsapp e e-mail)

* **Aviso de Inadimplência:** Ao selecionar um cliente para novo orçamento, o sistema exibe um banner preventivo se houver boletos antigos vencidos em aberto (não trava a criação, apenas alerta).


**Acompanhamento de Fluxo e Faturamento (Conta Corrente)**

* **Workflow de Status Duplo (Operacional e Financeiro):** Para refletir a realidade da oficina, o orçamento terá duas trilhas de status independentes, permitindo faturar algo que ainda está em produção.

    * Status Operacional (Oficina): GERADO ➔ ENVIADO ➔ APROVADO ➔ EM EXECUÇÃO ➔ CONCLUÍDO.
    * Status Financeiro (Caixa): A FATURAR ➔ FATURADO ➔ PAGO (O status CANCELADO pode interromper ambas as trilhas a qualquer momento).

* **Faturamento Agregado:** Acesso interno a um painel que lista todos os orçamentos de um cliente marcados como "CONCLUÍDO" ou "EM EXECUÇÃO". O Operador marca caixas de seleção (checkboxes) nos orçamentos desejados, o sistema soma o total em tempo real e gera o faturamento unificado, podendo nesse momento, assim como no momento de geração do orçamento individual, o usuário informar a forma de pagamento escolhida pelo cliente com seu respectivo desconto, caso haja, mantendo aqui a mesma regra do orçamento, de não exibir campos de desconto caso estejam em branco ou zerados. O fluxo de faturamento deve gerar um resumo de faturamento com todos os orçamentos incluídos e formas de pagamento, em um PDF para ser enviado ao cliente. A fatura deve ter um campo para informar o número da nota fiscal.

* **Recebimentos Parciais e Liquidação:** Capacidade de registrar múltiplos pagamentos adiantados ou parcelados, alterando o status final para PAGO ao atingir 100%.

* **Liquidação por Cortesia:** Opção de quitar uma fatura integralmente como "CORTESIA". Esta ação altera o status para PAGO, registra o serviço na ficha de "Histórico de Cortesias" do cliente, mas não gera entrada de valor no Caixa Real (ignora o Espelhamento de Caixa), garantindo que o DRE e os saldos não sejam corrompidos por dinheiro que nunca existiu.


**Gestão de Tesouraria e Conciliação (Preparação Open Finance)**

* **Cadastro de Contas e Cartões (Caixas Físicos):** Área dedicada para gerenciar as "gavetas" de dinheiro da empresa (ex: Conta Itaú, Conta Nubank, Caixa Físico, Cartão de Crédito Corporativo). Cada conta/cartão terá seu saldo isolado.

* **Área de Conciliação Individualizada:** Para cada conta, haverá uma tela dividida ao meio: de um lado, as linhas do extrato importado; do outro, os lançamentos de "Contas a Pagar/Receber" cadastrados no sistema. A partir daqui, o usuário fará o "Match" (liquidando títulos pendentes) ou criará despesas não identificadas (tarifas) no ato. Esta estrutura modular deixará o ERP pronto para plugar APIs de Open Finance (v2) diretamente em cada conta cadastrada.


**Relatórios e Financeiro (Caixa Real)**

* **Painel Unificado de Contas a Receber e a Pagar:** Área financeira central que exibe lançamentos manuais de despesas/receitas avulsas e consolida automaticamente as Faturas geradas pelo setor de orçamentos (evitando duplicidade). Permite visualizar títulos pendentes, a vencer e vencidos, dando baixa (liquidação) com recálculo automático de saldos.

* **Registro de Transferências:** Registro de transferências de saldos entre contas bancárias internas sem alterar o resultado (DRE) da empresa.

* **Dashboard e Consultas:** Um painel executivo exibindo total de orçamentos pendentes, valor acumulado pendente em faturamento de clientes, boletos atrasados, lucro/prejuízo mensal, exportações em CSV, PDF, entre outros.


**Histórico, Infraestrutura e Auditoria**

* **Soft Delete e Recuperação:** Nenhuma exclusão real ocorre no banco de dados. O registro excluído fica oculto de listagens novas mas visível para relatórios antigos. Exclusões que impactem no histórico do sistema, como, por exemplo, exclusão de uma categoria de caixa, devem se manter intácta nos registros já salvos.

* **Log de Ações (Auditoria):** O sistema marca silenciosamente "Quem criou, Quando criou, Quem inativou, quando inativou e Quem atualizou, quando atualizou" em todos os eventos do sistema.

* **Log de Erros e Expurgo:** Gravação física de arquivos de erro no servidor. O Administrador define um prazo de retenção (ex: 90 dias) e o sistema deleta automaticamente arquivos mais velhos. Se o Administrador reduzir esse prazo nas configurações (ex: mudar para 30 dias), o sistema exibirá um modal de confirmação exigindo que ele escolha: (A) Aplicar retroativamente, apagando os logs antigos imediatamente, ou (B) Manter a validade original dos antigos e aplicar a nova regra apenas para novos logs.

* **Auditoria de Lançamentos Não Conciliados:** Uma tela de verificação e revisão (Relatório de Divergências) que lista todos os lançamentos financeiros inseridos manualmente pelo Operador e marcados como "Realizados" no ERP, mas que não encontraram correspondência (match) no extrato importado (OFX/CSV). Isso permite ao gestor identificar falhas operacionais (ex: lançou que pagou no Banco X, mas o dinheiro saiu do Banco Y; ou achou que pagou e esqueceu), garantindo que o saldo do ERP seja um reflexo exato da realidade bancária.


## 6. Funcionalidades Fora de Escopo

* **Controle Físico Avançado de Estoque:** Na v1 não haverá contagem de insumos ou baixa de rolos de arame metro a metro. O cálculo se dará via "Custo Base Padrão/Estimado" por serviço.

* **Integração Bancária e Fiscal Direta:** A conciliação de faturas será por importação manual de CSV/OFX; a emissão de Notas Fiscais e Boletos ocorrerá fora do sistema (com registro numérico anotado no sistema pelo usuário).

* **Área Logada Externa do Cliente:** O acompanhamento é estritamente de uso da equipe da oficina e gestão; não haverá um portal com senha para que o cliente final interaja (sendo essa uma funcionalidade a ser implementada na v2).

* **Exclusão Física:** A deleção permanente de usuários e registros não existirá em nenhuma área do sistema, preservando o histórico geral.


## 7. Regras de Negócio

* **Privilégios Invioláveis:** Operadores jamais poderão promover seu acesso a Administrador, tampouco acessar as configurações do núcleo do sistema.

* **Restrição de Ocultação Financeira:** Itens como Contas Bancárias ou Categorias, quando inativados/excluídos, deixam de aparecer em formulários de novos cadastros, mas permanecem visíveis forçadamente em relatórios que consultem o passado.

* **Mudança para PAGO:** O "Status do Lançamento Financeiro" será determinado automaticamente; um orçamento ou fatura só pode mudar o status comercial para "PAGO" se todos os recebimentos parciais baterem exatamente 100% da dívida daquela fatura - deveremos pensar em um lançamento de quitação como DESCONTO ou prever a possibilidade de alterar o desconto na fatura, depois de gerada, atualizando a geração da fatura. A quitação como cortesia, lança normalmente um pagamento na fatura, do valor total, permitindo assim que a fatura seja atualizada para o status "PAGO".

* **Condição Visual de Impressão:** Todo desconto gerado na tela do orçamento atua sobre o resultado final e é bloqueado de aparecer impresso no espelho do PDF gerado para envio ao cliente, caso o desconto seja zero ou nulo (em branco).

* **Limpeza Deliberada de Logs:** Caso um Administrador reduza a regra de retenção de retenção de logs (ex: de 90 dias para 30), o sistema deve pausar e forçar o administrador a declarar se deseja retroagir a exclusão no mesmo instante ou aplicar só para logs futuros.

* **Independência Financeira da Fatura:** O orçamento atua como pré-contrato e seu valor bruto é transferido para a Fatura. A Fatura é o documento soberano financeiro. Qualquer desconto adicional aplicado no momento de gerar a Fatura (ex: desconto extra por escolher pagamento antecipado no Pix) incidirá sobre o valor total da Fatura, sem alterar retroativamente os itens ou os valores dos orçamentos originais que a compõem.

* **Snapshot (Congelamento de Histórico e Alerta de Margem)**: Ao gerar um orçamento ou inserir um Produto/Item nele, o sistema tira uma "fotografia" exata (snapshot) do custo de produção (soma dos custos dos materiais e mão de obra) e do preço de venda naquele milissegundo. Reajustes futuros no catálogo de Produtos ou Itens não devem retroagir nem alterar o valor de orçamentos ou faturas emitidas no passado. Além disso, o alerta visual de margem funcionará comparando o Custo de Produção atual do catálogo com o Custo salvo nesse snapshot da última vez que o produto foi orçado.

* **Espelhamento de Caixa:** Para evitar dupla digitação, a liquidação de qualquer Recebimento Parcial (vinculado a uma Fatura) ou o pagamento de uma Nota de Fornecedor deve gerar automaticamente a movimentação correspondente (Entrada/Saída) no módulo de Lançamentos Financeiros (Caixa Real), alimentando o saldo bancário da empresa.

* **Estorno e Regressão de Faturas:** Caso uma Fatura seja cancelada por erro, ela permanece no sistema com o status "CANCELADA" (para auditoria). Os orçamentos que estavam contidos nela são "desvinculados" e regridem para o Status Financeiro "A FATURAR", voltando a ficar disponíveis na conta corrente do cliente.

* **Renovação Inteligente de Prazo:** Orçamentos vencidos ficam bloqueados para aprovação. Ao solicitar a renovação do prazo de validade, o sistema compara o Snapshot (custo de produção antigo salvo) com o Custo de Produção atualizado no catálogo de produtos e itens. Caso o custo tenha subido, o sistema não altera o preço de venda automaticamente, mas exibe um alerta detalhado (ex: "O custo de produção subiu X% desde a última emissão"). O usuário visualizará o custo antigo e o novo, cabendo a ele decidir se apenas renova o prazo (mantendo os preços) ou se reabre o orçamento para edição manual, gerando ao final um novo Snapshot.


## 8. Informações que o Sistema Precisa Controlar

| Informação | Para que serve no sistema | Observações importantes |
| --- | --- | --- |
| Usuários de Equipe | Controle de login, acesso restrito e histórico de ações. | Não possuem auto-cadastro. |
| Clientes e Veículos | Referência para emissão de PDF e cobrança financeira agregada. | Campo de identificação textual pode substituir a placa da máquina/equipamento. |
| Fornecedores e Insumos | Cadastrar parceiros de compra e rastrear preço pago em insumos base. | Serve para identificar necessidade de reajuste do valor dos serviços. |
| Orçamentos | Detalhamento do que será consertado, construído ou reformado. | Possui sequencial fixo iniciando em 1 e status de acompanhamento duplo (Operacional/Financeiro). |
| Faturas (Fechamentos) | Aglutina serviços concluídos de um mesmo cliente em uma cobrança. | Armazena a transcrição da NF, Linha digitável e comprovantes PDF, vinculando orçamentos. |
| Recebimentos Parciais | Trilha de auditoria das parcelas ou dos adiantamentos (sinais). | Fica vinculada à Fatura/Orçamento e acumula até totalizar 100% da dívida. |
| Lançamentos Livres | Receitas e Despesas de fluxo de caixa (luz, salário, recebimentos diversos). | Filtro de situação Pendente/Realizada baseado em data. |


## 9. Fluxos Principais de Uso

### Criação Rápida de Orçamento e Envio

1. O usuário acessa a área de orçamentos e inicia um novo cadastro.
2. O usuário escolhe o cliente (recebendo notificação preventiva se houver inadimplência).
3. O usuário seleciona o veículo ou equipamento desejado e lança os itens abertos informando a descrição, quantidade, e preço.
    * Fluxo Alternativo: Caso a máquina não exista, o usuário clica em "Novo Equipamento". Um Modal (janela sobreposta) se abre, permitindo o cadastro rápido com dupla validação: validação contra Placas duplicadas no cadastro geral do sistema (pois placas são únicas de DETRAN) e validação contra Identificadores duplicados no mesmo cliente (pois números de patrimônio podem se repetir em clientes diferentes). Ao salvar, o modal se fecha e o equipamento já aparece selecionado no orçamento sem perda de dados digitados na tela de fundo.
4. O usuário lança os itens abertos informando a descrição, quantidade, e preço.
5. O usuário valida as condições (validade, descontos em R$ ou %).
6. O sistema registra o orçamento sob o status de GERADO, criando o Snapshot de custos.
7. O usuário emite o PDF e envia ao cliente.


### Aglutinação (Faturamento Agregado) de Serviços

1. O usuário entra na ficha financeira central do cliente.
2. O usuário visualiza a lista de todos os serviços que constam como CONCLUÍDOS ou EM EXECUÇÃO (podem ser inseridos na fatura, orçamentos que ainda não foram concluídos) na oficina e pendentes de cobrança, o usuário pode filtrar por data ou por outros filtros variádos, pertinentes.
3. O usuário marca (clique nos orçamentos mostra eles marcados, mais escuros) os orçamentos acordados para fechamento de mês.
4. O sistema soma, no mesmo instante em tela, o montante daqueles serviços unidos.
5. O usuário confere a consolidação e insere as (já pré cadastradas pelo administrador) formas de pagamento e seus respectivos descontos, caso existam na configuração do sistema.
6. O usuário confirma a consolidação, gerando um Faturamento.
7. O sistema altera o Status Financeiro de todos os orçamentos internos incluídos para FATURADO, mas mantém o Status Operacional intacto (seja "Em Execução" ou "Concluído"), permitindo que a oficina continue acompanhando o serviço fisicamente. O sistema aguarda o lançamento do PDF do Boleto/Comprovante.


## 10. Histórias de Usuário

* "Como Operador, eu quero selecionar diversos orçamentos num único painel usando caixas de seleção, para que eu possa somar rapidamente seus valores e emitir um único recebimento unificado no final do mês ou na data desejada." 
* "Como Operador, eu quero inserir itens de serviço em texto livre, para que eu possa detalhar customizações de peças sem depender de um catálogo quadrado de produtos de loja, além de poder inserir no orçamento, itens do catálogo (Produtos)." 
* "Como Administrador, eu quero visualizar um relatório com as últimas compras e preços informados por fornecedor, para que eu saiba exatamente quando os insumos básicos subiram e seja hora de encarecer a precificação da oficina." 
* "Como Operador, eu quero que haja um alerta quando eu for inserir um item do catálogo (Produto) em um orçamento e o valor calculado de custo esteja maior do que o valor calculado na última vez que inseri esse item em um orçamento, seja por aumento dos preços dos insumos, por aumento do preço da mão de obra, pra que eu possa me atentar que devo verificar corretamente o valor a inserir no orçamento."
* "Como Gestor Comercial, eu quero que apareça um alerta na tela se eu for fazer uma nova cotação para alguém que tem faturas vencidas, para que eu evite aumentar minha taxa de inadimplência no pátio." 
* "Como Operador, eu quero receber um alerta visual caso a internet do pátio caia enquanto consulto uma ficha, para que eu não perca as alterações recém digitadas aguardando a volta da conexão." 


## 11. Critérios de Aceitação

* [ ] O sistema permite criar orçamentos independentemente de um catálogo engessado, exigindo apenas um texto claro de item e valor.
* [ ] O sistema esconde o campo desconto aplicado da renderização e geração do PDF, caso o desconto seja zero ou nulo.
* [ ] O sistema acumula orçamentos concluídos na Conta Corrente do cliente para agrupamento manual via checkbox.
* [ ] O sistema não avança orçamentos na marra, as etapas (GERADO a PAGO) devem ser cumpridas e cancelamentos encerram o ciclo de cobrança do orçamento.
* [ ] O sistema impede a exclusão física definitiva no banco de dados.
* [ ] O Operador não enxerga menus de gerenciamento de permissão de equipes, somente seu perfil próprio.


## 12. Consultas, Relatórios e Indicadores

Na primeira versão, o painel de uso não necessita de métricas complexas de rentabilidade DRE. Focaremos em liquidez e saúde da gestão do serviço:

* **Dashboard Geral:** Flip Cards: Quantia total de serviços orçados aguardando aprovação/Expectativa de faturamento dos serviços aguardando aprovação; serviços na oficina (Em Execução)/Expectativa de faturamento dos serviços aprovados (Em Execução); Previsão de faturamento do mês/Previsão de despesas do mês/Previsão de resultado do mês; Orçamentos realizados/Orçamentos Aprovados/Orçamentos Em Execução/Orçamentos concluídos, no mês, Contas Vencidas/Vencendo hoje/Vencendo nos próximos 7 dias; Volume financeiro travado em serviços já concluídos aguardando emissão de NF (Conta corrente represada); Orçamentos vencidos/À vencer nos próximos 3 dias.

* **Relatório de Clientes e Margens:** Acesso a visualização do histórico do relacionamento (total já faturado com um cliente particular) e relatórios formatados em CSV e PDF para envio posterior à contabilidade terceirizada.


## 13. Permissões e Segurança Funcional

| Perfil | Pode fazer | Não pode fazer | Observações |
| --- | --- | --- | --- |
| **Administrador** | - Convidar, promover e rebaixar usuários <br> - Acessar todas as informações e relatórios <br> - Parametrizar Configurações Globais e Categorias Financeiras (Plano de Contas) <br> - Limpar logs de erro do sistema <br> - Aplicar Exclusão Lógica (Soft Delete) e Restaurar registros criados por **qualquer** usuário <br> - Executar todas as funções operacionais | - Auto-cadastrar contas abertas no painel público da web <br> - Apagar permanentemente dados consolidados do banco (Hard Delete) | Perfil concentrador da tecnologia e da governança das regras. |
| **Operador** | - Emitir, editar e aprovar Orçamentos <br> - Gerar Faturas (individuais ou agrupadas) e gerir Recebimentos <br> - Fazer upload de Notas Fiscais e comprovantes <br> - Lançar Contas a Pagar, Receitas Livres e Transferências Bancárias <br> - Criar, ler e atualizar Itens, Produtos, Campos Dinâmicos, Equipamentos, Clientes e Fornecedores <br> - Aplicar Exclusão Lógica (Soft Delete) **apenas** nos registros que ele mesmo criou | - Acessar menus de privilégios e equipe <br> - Mudar configurações globais (cor, tempo de sessão, retenção de logs) <br> - Criar, editar ou inativar Categorias Financeiras e Contas Bancárias <br> - Aplicar Exclusão Lógica em registros criados por outros usuários ou restaurá-los | Foco exclusivo em operar a rotina do pátio, faturamento e fluxo de caixa diário. |

## 14. Limitações da Primeira Versão

* Não haverá emissão integrada com a Receita Federal ou SEFAZ para Nota Fiscal Eletrônica. O serviço na V1 é estritamente informacional, os dados deverão ser emitidos em emissores externos e seu ID colado no sistema web.
* Não haverá automação de conciliação do Open Finance, a conferência com a conta corrente ocorrerá via leitura simplificada de arquivos de banco OFX/CSV.
* Operação com modo Offline passiva (PWA): Sem conexão, o Operador não salvará novos relatórios para não criar conflito em banco, ficando com um aviso preventivo visual da queda de rede em tela.


## 15. Pontos Pendentes Antes do FSD

"Não foram identificadas dúvidas funcionais pendentes para a criação do FSD." 

*Todas as dinâmicas de transposição de valores, hierarquias de equipe, mecânicas de agrupamento comercial e a relação direta entre fluxo operacional vs saldo de fluxo de caixa foram plenamente debatidas e confirmadas ao longo da consolidação.*

## 16. Resumo Final do PRD

O software que será construído (**EMC Soldas**) é uma plataforma web ERP responsiva destinada a simplificar e aglutinar todo o serviço burocrático e comercial da oficina. O sistema será utilizado única e exclusivamente pelo quadro de colaboradores da empresa (Operadores e Administração interna).

Ele resolve a dificuldade latente de cobrar serviços agrupados, modernizando todo o pátio operacional desde a orçamentação dinâmica, acompanhamento (Workflow) do que o cliente está precisando, até a geração da cobrança acumulada com acompanhamento de recebimentos parciais e boletos inadimplentes.

Ficarão, estrategicamente, de fora desta primeira versão todos os controles puramente complexos industriais de maquinário ou estoque unitário via biometria/apontamento celular, e não haverá dependências pesadas de APIs bancárias diretas, garantindo rapidez para lançamento no mercado interno da companhia.

O projeto encontra-se robusto, totalmente alinhado com a realidade da oficina, e plenamente apto para avançar rumo à modelagem técnica e arquitetura de software contida no Documento de Especificação Funcional (FSD).