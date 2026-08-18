# DOCUMENTO DE ESPECIFICAÇÃO FUNCIONAL (FSD)

## 1. Visão Geral

O sistema **EMC Soldas** é uma aplicação web ERP de gestão modular, projetada para otimizar as operações diárias e financeiras da oficina. O objetivo principal é organizar o fluxo de trabalho unindo orçamentos (operações no chão de fábrica) ao faturamento (financeiro), controlando custos e maximizando a lucratividade sem a necessidade de terminologia contábil complexa.

O sistema será utilizado exclusivamente pelo quadro interno de colaboradores (Administradores e Operadores) através de dispositivos variados (computadores, celulares e tablets). Por ser usado também no pátio da oficina, o sistema foi pensado como uma aplicação responsiva e resiliente. O funcionamento abrange desde a criação dinâmica de orçamentos, acompanhamento de execução, até o faturamento aglutinado da "conta corrente" do cliente, além da conciliação bancária de recebimentos.

## 2. Documentos do Projeto para Implementação

Os seguintes documentos deverão ser utilizados pela IA codificadora para a implementação do sistema:

- `docs/FSD.md`
- `docs/DESIGN.md`

Este FSD já consolida todas as decisões técnicas e funcionais necessárias para a implementação do sistema.

## 3. Stack Definida

A stack de tecnologia escolhida para a implementação é:

- **Linguagem de Programação:** Python
- **Framework de Backend:** Django (com Django REST Framework para criação da API)
- **Banco de Dados:** MySQL
- **Tecnologias de Interface (Frontend):** PWA client-side utilizando HTML, CSS, JavaScript Vanilla e Service Workers para resiliência.
- **Padrão Arquitetural:** Arquitetura desacoplada. O backend atuará estritamente como fornecedor de dados via API REST (JSON). Toda a regra de negócio e abstração do banco de dados ocorrerá no servidor sob forte Orientação a Objetos. A interface gráfica, o roteamento de telas e a resiliência offline serão tratados inteiramente de forma independente pelo frontend client-side.

## 4. Ambientes do Projeto

O sistema operará inicialmente através dos seguintes ambientes:

- **Desenvolvimento Local:** Utilizando XAMPP para hospedagem local do banco MySQL e o servidor nativo do Django para a aplicação de backend.
- **Produção:** Deploy em ambiente Cloud PaaS (exemplo: Render ou PythonAnywhere), preparado de forma que possa migrar para infraestrutura na nuvem (AWS) futuramente sem necessidade de grandes reestruturações de código.
- **Observações:** Na primeira versão, não haverá ambiente em nuvem exclusivo para testes/homologação. A validação e garantia de qualidade (QA) serão conduzidas primariamente no ambiente local antes da implantação em produção.

## 5. Arquitetura do Sistema

O sistema deverá respeitar uma arquitetura estritamente desacoplada entre Backend (Python) e Frontend (PWA). O projeto será centralizado no que chamamos de `[Diretório do Projeto - Repositório]`.

Não deverão ser utilizadas expressões de servidores legados como `public_html`, `public`, `htdocs` ou `www` para gerenciar a organização arquitetural da aplicação.

Dentro do `[Diretório do Projeto - Repositório]`, a estrutura organizacional dividirá claramente as responsabilidades:

- **Backend (Python):** Ficará em um conjunto de pastas internas que aglutina os arquivos da aplicação e do framework (ex: `app/`, `core/`, `api/`, `models/`, `services/`, `database/migrations/` e `logs/`). O arquivo de entrada para execução da API (ex: `manage.py` ou `app.py`) estará na raiz do Backend. As rotas, controllers e os Modelos/ORM ficarão contidos nessas pastas, operando exclusivamente as regras de domí­nio. O Backend comunicará via API REST e não enviará nenhum arquivo HTML renderizado.
- **Frontend (PWA):** Organizado em seu diretório próprio de arquivos client-side. Ficará isolado contendo arquivos HTML estáticos, Vanilla JS, CSS baseados no `docs/DESIGN.md`, o arquivo `manifest.json` e os Service Workers. O consumo do banco de dados deve ocorrer obrigatoriamente através de requisições AJAX/Fetch efetuadas na API.

**Proteção do Ambiente:**
As pastas do backend (como código-fonte `.py`, configuração, `migrations/` e `logs/`) nunca poderão ser servidas diretamente via web. A aplicação não deve depender de servidores Apache ou do uso de `.htaccess` para manter as pastas seguras. O isolamento deve ser tratado nativamente pelo framework backend (servidor WSGI/ASGI e middleware de proteção) e por uma exposição criteriosa onde a hospedagem aponta apenas para o tráfego da API e para a pasta isolada do Frontend PWA.

As credenciais e as configurações do ambiente devem utilizar a arquitetura desacoplada do Django (`config/settings.py` ou `core/config.py`). Em ambiente local de desenvolvimento, utiliza-se valores seguros padrão para agilidade de testes; em ambiente de produção na nuvem, as variáveis críticas e chaves-mestras (`SECRET_KEY`, `ENCRYPTION_KEY`, dados do banco) serão lidas dinamicamente da memória do sistema operacional (`os.environ`), configuradas no painel de segredos da plataforma PaaS (ex: Render/PythonAnywhere), impedindo que chaves reais fiquem expostas em arquivos no repositório Git ou em pastas web públicas.

## 6. Escopo Funcional da Primeira Versão

Abaixo as funcionalidades confirmadas, agrupadas por área:

**Cadastros Básicos**
- **Categorias Financeiras e Contas Bancárias:** Estruturação de contas do financeiro, abrangendo bancos, dinheiro, formas/regras de pagamento, etc.
- **Clientes e Fornecedores:** Formulários com suporte a Pessoas Físicas (PF) e Jurídicas (PJ). Inclui:
  - *Hierarquia Visual Top-Down:* O seletor de Tipo de Pessoa (PF/PJ) e o campo **CPF/CNPJ são posicionados obrigatoriamente no topo absoluto** do formulário/modal como o primeiro campo a ser preenchido, disparando validação matemática e checagem de duplicidade imediatamente na saída do campo (`onBlur`) para evitar retrabalho;
  - *Validação Matemática de CPF:* Algoritmo de validação de dígitos verificadores (módulo 11) com feedback visual imediato no frontend e validação estrita no backend;
  - *Motor de Busca e Autocomplete de CNPJ:* Integração com API pública (BrasilAPI / ReceitaWS) que preenche instantaneamente Razão Social, Nome Fantasia, CEP, Logradouro, Bairro, Cidade, UF, Telefone e E-mail ao digitar o CNPJ;
  - *Blindagem Anti-Duplicação:* Garantia de que nenhum CPF ou CNPJ seja cadastrado em duplicidade no sistema;
  - *Cadastro Rápido Ágil (Modal Flutuante):* Permite cadastrar novos clientes durante a elaboração do orçamento exigindo obrigatoriamente **apenas Nome/Razão Social e Telefone**, mantendo todos os outros campos como opcionais para não travar o fluxo comercial com clientes avulsos;
  - *Histórico de Preços no Fornecedor:* Histórico de compras para auditoria de aumento de custos.
- **Equipamentos e Veículos:** Cada equipamento/máquina será cadastrado e terá um "Log de Vínculo". Se um equipamento trocar de cliente na vida real, ele é reatribuído no sistema e manterá um histórico para que orçamentos antigos não mudem acidentalmente o proprietário retrospectivamente.
- **Catálogo (Motor de Custos BOM e Itens):** Dividido entre *itens/Matéria-Prima* (registram último preço de compra) e *Produtos Compostos/Receitas*. O Administrador mantém um **Dicionário Central (UOM)** contendo Unidades de Medida (ex: m², cm², Litro, Caixa) e atributos descritivos.
  - *Fator de Conversão:* Ao cadastrar um item, o Operador vincula a "Unidade de Compra" e a "Unidade de Consumo" a partir do Dicionário, informando a proporção matemática. O sistema passa a calcular custos fracionados instantaneamente.
  - *A Receita:* O Operador cria o Produto selecionando os itens e as Horas de Mão de Obra. O sistema gera automaticamente o `Preço de Custo Apurado`, simplificando a venda no Orçamento final e blindando a margem de erro.
- **Módulo de Compras (Notas Fiscais):** Tela para registro manual de Notas de Entrada. O arquivo físico (XML/PDF) atua apenas como anexo de arquivamento na V1. O Operador digita manualmente os itens comprados (suportando modal dinâmico para novos itens).
  - *Retroalimentação de Custos e Snapshots:* Salvar a nota atualiza o `Último Preço de Compra` dos itens no Catálogo, gerando um registro histórico contínuo (linha do tempo de custos).
  - *Isolamento Financeiro V1:* A nota de compra não gera automaticamente títulos no Contas a Pagar. Ela foca no motor de custos (BOM). O lançamento da despesa real deve ser feito manualmente no Módulo Financeiro.

**Operação Comercial e Orçamentos**
- **Elaboração Dinâmica:** Permite inserir itens em catálogo de Produtos, ou através da digitação de textos livres diretos. O Snapshot de valor guarda o custo exato do momento.
- **Validade, Renovações e Alertas de Inflação (Proteção de Margem):** Orçamentos não aprovados mantêm seus preços travados (Snapshot) durante a validade. Se o prazo expirar e o Operador for "Renovar" a data, o sistema compara o custo base gravado no orçamento com o custo atual do catálogo (alimentado pelas novas Notas de Compra). Havendo inflação, o sistema emite um **Alerta**, permitindo ao Operador escolher entre apenas renovar o prazo (assumindo a perda de margem) ou re-precificar os itens atualizando o orçamento.
- **Inadimplência Preventiva:** Aviso visual durante a tentativa de gerar cotação para cliente com título de fatura em atraso.
- **Geração PDF e Desconto Oculto:** O orçamento exporta para PDF profissional. O desconto global ou atrelado a condições de pagamento constará em tela, mas será suprimido completamente da versão final impressa do cliente caso seja zerado/nulo.
- **Cancelamento com Justificativa Obrigatória:** O cancelamento de orçamentos exige compulsoriamente a abertura de modal com preenchimento de justificativa textual (mínimo 10 caracteres), gravada no campo `motivo_cancelamento` da entidade, carimbando autoria/data e disparando evento estruturado no log de auditoria do servidor.

**Conta Corrente de Clientes (Faturamento Agregado)**
- **Workflow Duplo:** O status produtivo do serviço ('Gerado' ➔ 'Enviado' ➔ 'Aprovado' ➔ 'Em Execução' ➔ 'Concluído') caminha paralelo com seu status de caixa ('A Faturar' ➔ 'Faturado' ➔ 'Pago').
- **Cascata de Faturamento e Máquina de Estados:**
  - *Fase 1 (Pré-Fatura / Rascunho):* O Operador seleciona na conta corrente do cliente os orçamentos prontos ('Concluído' ou 'Em Execução') com status financeiro 'A Faturar'. O sistema cria a Fatura em status `RASCUNHO` (Pré-Fatura), consolida os valores individuais e o valor bruto total, e permite ao Operador selecionar as opções de pagamento que deseja oferecer ao cliente, podendo **personalizar os descontos** (sobrescrevendo o desconto padrão do cadastro). O sistema gera o **PDF Espelho da Pré-Fatura** para envio ao cliente. **Regra estrita:** A Pré-Fatura *não gera* títulos no Contas a Receber, permitindo alterar orçamentos e condições livremente.
  - *Fase 2 (Fatura Final / Faturada):* Após o cliente definir a forma de pagamento desejada, o Operador abre o rascunho, vincula a **Forma de Pagamento Definida** (com possibilidade de ajustar o desconto final), e confirma o fechamento. O status da Fatura muda para `FATURADA`, o status financeiro de todos os orçamentos contidos muda automaticamente para `FATURADO`, e o backend gera compulsoriamente as parcelas no **Contas a Receber** com as datas calculadas pela regra escolhida, atualizando o Regime de Competência e os Dashboards.
  - *Fase 3 (Quitação Total / Paga):* Os recebimentos parciais ou totais vão amortizando a dívida. Ao atingir **100% do valor da fatura**, o status da Fatura transita automaticamente para `PAGA`, e todos os orçamentos vinculados têm seu status financeiro transitado automaticamente para `PAGO`.
- **Cancelamento de Faturas e Desvinculação em Cascata:** O cancelamento de faturas (antes de haver recebimentos reais) exige modal de justificativa obrigatória (persistida em `motivo_cancelamento`). Ao cancelar a fatura, os Orçamentos contidos são automaticamente libertados e revertidos para o status financeiro `A FATURAR`, e as parcelas geradas no Contas a Receber são canceladas compulsoriamente.
- **Recebimento Parcial e Liquidação da Fatura:** O Operador pode lançar pagamentos parciais com valores totalmente avulsos (não engessados ao valor exato de um orçamento agrupado). 
- **Integração de Baixa com a Tesouraria:** Ao confirmar o recebimento (baixa) na fatura, a entrada no Caixa Real é **imediata**, impactando no mesmo instante o saldo da Conta Bancária vinculada (`conta_id`), seja o pagamento feito via Pix, Dinheiro, Boleto Liquidado ou TED. No caso de **Maquininha de Cartão**, o modal solicitará que o Operador digite o **Valor Líquido** recebido (ou a taxa cobrada); o sistema lançará a entrada do **Valor Bruto** na conta bancária (receita de venda) e gerará automaticamente uma linha de saída de despesa referente à **Taxa da Maquininha** (Valor Bruto - Valor Líquido), compondo o saldo líquido real na conta e mantendo o DRE perfeitamente auditável sem duplicação de taxas.
- **Cortesia:** Faturas podem ser quitadas em cortesia (desconto de 100%), gerando baixa de dívida comercial e registrando no histórico de cortesia do cliente, sem que a ação gere receita no painel do Fluxo de Caixa bancário real.

**Tesouraria Interna e Conciliação Bancária Inteligente (Split-Screen)**
O módulo atua estritamente separando o *Regime de Competência* (previsão) do *Regime de Caixa* (realidade).
- **Contas a Receber (Previsão de Entrada - Competência):** Tela focada nas parcelas e vencimentos gerados automaticamente pelas Faturas Finais dos clientes (ou lançamentos manuais a receber com vencimento futuro). Títulos em aberto possuem `status_pagamento = 'A Vencer'` e **não afetam o saldo bancário** até que ocorra a liquidação manual ou conciliação bancária.
- **Contas a Pagar (Previsão de Saída - Competência):** Tela focada nas despesas futuras (fornecedores, impostos, salários, contas fixas). Títulos a vencer **não afetam o saldo bancário** de imediato. É aqui também que a *Fatura do Cartão de Crédito Corporativo* se consolida: os gastos avulsos no cartão vão acumulando na fatura aberta e o fechamento da fatura gera um título a pagar a ser liquidado por uma conta bancária.
- **Extrato Real (Regime de Caixa):** Tela isolada mostrando **apenas o que foi efetivamente liquidado** (`status_pagamento = 'Pago'`). Qualquer lançamento feito diretamente no caixa ou qualquer liquidação de título afeta **imediatamente** o saldo da conta bancária (`conta_id`), independente do meio de pagamento. A **única exceção** são as despesas pagas com Cartão de Crédito Corporativo (`cartao_credito_id`), que afetam apenas o total da fatura aberta do cartão e não debitam o saldo bancário até a liquidação da fatura.
- **Modal Universal de Liquidação:** Sempre que o Operador for liquidar uma conta (receber ou pagar), um modal exige as amarrações do mundo real: 1. Qual o Meio Físico? (Dinheiro, PIX, Boleto, Cartão de Débito, TED). 2. De qual Conta Bancária oficial saiu/entrou? 3. É pagamento de conta parcelado no Cartão de Crédito da empresa? (Se sim, o sistema fragmenta e injeta as despesas ao longo das faturas futuras do cartão escolhido).
- **Regra de Bloqueio por Limite:** O sistema barra baixas que negativem a conta bancária real, *exceto* se a conta possuir o campo `Limite de Cheque Especial` configurado pelo Admin.
- **Transferência Inter-Contas:** Transferências exclusivas entre contas reais (`conta_id` para `conta_destino_id`) sem afetar DRE.
- **Conciliação Bancária Inteligente Split-Screen (OFX/CSV):** Tela dividida em duas colunas (Extrato Bancário vs Lançamentos do ERP) com 3 modalidades de matching:
  1. *Match Automático 1:1:* Sugestão de correspondência por proximidade de data (±3 dias) e valor exato.
  2. *Match Múltiplo:* Agrupamento de 1 lançamento bancário para N títulos do ERP (ou vice-versa).
  3. *Lançamento Rápido no Ato:* Criação instantânea de despesas não previstas (tarifas bancárias, rendimentos) diretamente a partir da linha do extrato para conciliação imediata.
  Ao confirmar a conciliação, o sistema grava compulsoriamente `is_conciliado = True`, `data_conciliacao = NOW()` e `conciliado_por_id = request.user.id` em cada lançamento.

**Administração e Configurações Globais**
- **Parâmetros da Empresa e Comerciais:** Personalização dos dados cadastrais da oficina (Razão Social, CNPJ, Telefone, Endereço, Logo), definição da Taxa de Mão de Obra por Hora e prazo padrão de Validade de Orçamentos (com blindagem de não-retroatividade para itens em andamento).
- **Gestão de Retenção de Logs e Expurgo:** Definição do tempo de vida útil (TTL) dos arquivos físicos de log via manifesto no banco de dados, com fluxo de confirmação para reduções retroativas de prazo.
- **Serviço Dinâmico de E-mails (SMTP):** Painel administrativo para configuração de servidor SMTP com presets rápidos (Gmail com Senha de App, Outlook, Personalizado), card didático de ajuda e botão de teste de disparo em tempo real. As credenciais sensíveis são protegidas no banco via criptografia simétrica AES-256/Fernet (sem retorno de senha em texto puro para a UI) e contam com fallback nativo para `console.EmailBackend` em testes locais.
- **Painel de Lixeira e Restauração (100% Soft Delete):** Interface dedicada exclusivamente para auditoria e recuperação de registros inativados logicamente:
  - *Visão do Administrador (Lixeira Global):* Painel unificado com filtros por entidade (Orçamentos, Faturas, Clientes, Itens, etc.), período e usuário autor. Permite ao Administrador auditar o histórico e executar o `[Restaurar]` (revertendo `deleted_at = NULL`) para qualquer registro do sistema.
  - *Visão do Operador (Minha Lixeira):* Interface restrita que lista exclusivamente os registros criados e inativados pelo próprio operador logado (`deleted_by_id = request.user.id`), permitindo reverter exclusões acidentais próprias com o botão `[Restaurar]`, sem acesso a dados de outros colaboradores.

**Gestão de Equipe, Usuários e Controle de Acesso (RBAC Dinâmico Total)**
- **Onboarding e Cadastro Hierárquico:** Sem auto-cadastro público. O Administrador Master pode cadastrar tanto novos **Administradores** (acesso pleno) quanto **Operadores** através do envio de link seguro por e-mail para definição da própria senha.
- **Matriz de Permissões com 10 Toggles Dinâmicos:** O painel permite ligar/desligar permissões de forma granular por colaborador em todos os 10 módulos do ERP:
  1. Acesso Comercial (Orçamentos, Faturas e Clientes);
  2. Acesso à Tesouraria (Caixa, Conciliação e Estornos);
  3. Acesso a Compras (Notas Fiscais de Entrada e Fornecedores);
  4. Gestão de Catálogo (Itens, Produtos, BOM e Preços);
  5. Visualização de Relatórios (Curvas ABC, Inadimplência e DRE);
  6. Cadastros Financeiros (Contas Bancárias, Regras de Pagamento e Categorias);
  7. Dicionário Central UOM (Unidades de Medida e Atributos);
  8. Configurações Globais (Parâmetros da Empresa, Tempos de Sessão/Ociosidade, SMTP e Retenção de Logs);
  9. Gestão de Equipe (Usuários, Permissões e Desbloqueio);
  10. Auditoria e Logs (Logs do Servidor, Expurgo e Lixeira Global).
- **Gestão de Bloqueios Anti-Bruteforce:** Painel administrativo para visualizar e forçar o desbloqueio manual de contas travadas por excesso de tentativas de login.

**Autenticação, Gestão de Sessão e Blindagem de Segurança**
- **Autenticação Segura (JWT via Cookie HttpOnly):** Sessão armazenada estritamente como Cookie de Sessão HttpOnly, garantindo "Morte Súbita" da sessão ao fechar o navegador, desligar o computador ou sofrer queda de energia.
- **Soft Lock por Ociosidade (30 minutos):** Trava automática da tela após 30 minutos sem interação, com destravamento ágil via Biometria (WebAuthn) ou PIN numérico de 6 dígitos.
- **Hard Lock (Expiração Mestre):** Expiração absoluta do token JWT após o prazo definido pelo Admin (ex: 15 dias), exigindo digitação completa de e-mail e senha.
- **Blindagem contra Invasões:** Defesa nativa contra CSRF (`X-CSRFToken` e `SameSite=Strict`), bloqueio a acessos não autorizados no backend, sanitização ORM (anti-SQLi), Rate Limiting global (100 req/min padrão e 5 req/min para relatórios pesados) e sanitização de uploads com bloqueio de execução de scripts (NoExec).

**Dashboards e Relatórios**
- **Dashboard de Flip Cards:** Tela inicial com 5 cartões interativos que giram ao clique no corpo e contam com botões de atalho independentes no rodapé (`Ver detalhes ➔`) para navegação direta sem ativar o giro, exibindo: 1. Operação (Orçamentos realizados/aprovados/finalizados); 2. Faturamento (Faturas geradas/pagas); 3. Receita (Faturamento Real vs Projetado); 4. Caixa (Saldo Real vs Projetado); 5. Alertas (Contas vencidas/vencendo hoje/próximos 7 dias).
- **Relatórios Gerenciais e Exportações (PDF/CSV):**
  - *Espelho de Orçamentos Agrupados (PDF):* Consolidação detalhada de múltiplos orçamentos para o cliente aprovar antes da Fatura.
  - *Gestão de Inadimplência:* Painel em tela de Faturas Vencidas para gestão interna de cobrança (focado no contato humano/telefônico).
  - *Dossiê do Cliente:* Histórico financeiro separando ativamente "Produtos" (Venda direta) de "Serviços" (Reformas).
  - *Relatórios Estratégicos:* Curva ABC de Clientes (maiores geradores de receita), Consumo de Itens (mais orçados/vendidos) e DRE Simplificado (Receitas x Despesas por Categoria).
  - *Relatório de Divergências de Conciliação:* Painel de auditoria que cruza e lista lançamentos manuais marcados como realizados no ERP que não encontraram correspondência (match) no extrato bancário importado (OFX/CSV).

## 7. Fora de Escopo

Na primeira versão (v1), as seguintes funcionalidades estão fora de escopo:
- Controle Fí­sico Avançado de Estoque (onde se dá baixa métrica/fí­sica nos materiais, adotou-se o modelo de custo de snapshot).
- Área e Portal Externo Logado destinado aos Clientes.
- Integração Bancária direta e sincronização automática (Open Finance).
- Comunicação direta com a Sefaz/Receita Federal para emissão de NFe via API automática.
- **Hard Delete (Deleção Física e Permanente de Dados no SQL):** A exclusão física de registros no banco de dados está **terminantemente fora de escopo e proibida** em toda a V1. Toda e qualquer exclusão opera via *Soft Delete* (`deleted_at` e `deleted_by_id`), preservando a integridade referencial perpétua de todas as cascatas de dados (Faturas, Orçamentos, Snapshots, Compras e Fichas Técnicas).
- **Auto-cadastro, OAuth2 e 2FA:** Auto-cadastro público na plataforma, autenticação via provedores externos (ex: Google OAuth2 / Social Login) e Autenticação em Dois Fatores (2FA via aplicativo TOTP) estão fora de escopo na V1 e ficam como arquitetura preparatória para a V2.
- **Gestão de Grupos/Cargos de Permissão Customizáveis (Templates de Perfis):** Na V1, as permissões são atribuídas de forma direta e individual na ficha de cada colaborador através dos 10 toggles dinâmicos (`Permissoes` 1:1 com `Usuario`). A criação de uma interface administrativa para cadastrar "Nomes de Cargos/Perfis" pré-moldados (onde múltiplos colaboradores herdam regras de um grupo) fica postergada como evolução para a V2, caso a expansão da equipe justifique a gestão de acessos em lote.

## 8. Perfis de Usuário e Permissões Dinâmicas (RBAC)

Na primeira versão (V1), a plataforma estrutura-se sobre dois perfis base de usuários (`role`), operando em conjunto com um sistema granular de **10 Toggles de Permissões Dinâmicas** gerenciáveis por colaborador:

- **Administrador:** Gestor do sistema. Possui direitos plenos por padrão sobre todos os 10 módulos, incluindo o convite e gestão de novos colaboradores, parametrização de configurações globais (dados da empresa, SMTP, tempos de sessão/ociosidade e manifesto de expurgo de logs) e governança da Lixeira Global para auditar e restaurar registros de qualquer colaborador.
- **Operador:** Profissional da operação diária. Inicia por padrão com foco nas rotinas operacionais (orçamentos, faturas, clientes, catálogo e tesouraria) e acesso restrito à sua "Minha Lixeira" para registros próprios. Contudo, seu acesso é **totalmente flexível e personalizável**: o Administrador pode ligar ou desligar individualmente qualquer um dos 10 toggles de permissão (Comercial, Tesouraria, Compras, Catálogo, Relatórios, Cadastros Financeiros, Dicionário UOM, Configurações Globais, Gestão de Equipe e Auditoria/Logs), concedendo maior ou menor autonomia a cada colaborador conforme a função desempenhada na oficina.

Essa modelagem relacional desacoplada através da entidade `Permissoes` confere governança sob medida na V1 e já deixa a arquitetura preparada para a introdução de novos perfis intermediários em versões futuras sem necessidade de refatorações no banco de dados.

## 8.1. Gestão de Sessão e Autenticação (JWT & WebAuthn)

A segurança PWA adota uma abordagem hí­brida de usabilidade e restrição severa:
- **Morte Súbita (Fechamento do Navegador):** Para garantir segurança máxima em caso de queda de luz ou fechamento brusco, o Token JWT será armazenado estritamente como um **Cookie de Sessão HttpOnly**. Isso tem duas vantagens: 1. O token é invisí­vel para injeções de scripts maliciosos (XSS) e não pode ser roubado pela inspeção do navegador. 2. Por ser um cookie de sessão, se o Operador fechar o navegador (ou app), desligar o PC, ou a energia cair, **o cookie e a sessão evaporam instantaneamente**. Ao reabrir, o sistema exigirá reautenticação imediata.
- **Soft Lock (Ociosidade):** Se a janela continuar aberta, mas o operador ficar 30 minutos sem mexer no mouse, a tela é travada. 
  - *Retomada Ágil:* Se o aparelho possuir **WebAuthn** (Biometria/Windows Hello), o Operador destrava a tela com a digital. Se for Desktop simples, usa-se um Fallback de **PIN de 6 dí­gitos**.
- **Hard Lock (Expiração Mestre):** O Token JWT tem vida útil cravada (ex: 15 dias). Quando estourar, a sessão morre, obrigando o retorno ao E-mail e Senha absolutos.
- **Logout Explí­cito:** O botão "Sair" destrói os tokens ativamente no servidor.

## 8.2. Blindagem Contra Invasões (Red Team Assessment)

Para garantir que a oficina suporte ataques comuns da internet, o código seguirá restrições militares:
- **CSRF (Falsificação de Requisição):** Como usamos cookies HttpOnly, um hacker poderia forçar o navegador a executar ações num site falso. **Defesa:** O Django exigirá obrigatoriamente um cabeçalho `X-CSRFToken` em todas as requisições de alteração (POST/PUT/DELETE) e o cookie terá a flag `SameSite=Strict`.
- **IDOR (Quebra de Ní­vel de Acesso):** Um Operador mal-intencionado descobre a URL da API de configurações e tenta acessá-la. **Defesa:** A API não dependerá da interface para bloquear. Toda rota do backend terá decoradores rí­gidos (`@require_admin`). Se a rota não for explicitamente permitida, ela retorna Erro 403.
- **SQL Injection:** Tentativa de injetar código SQL nas caixas de pesquisa (ex: Drop Tables). **Defesa:** Proibição do uso de queries cruas (`.raw()`). O Django ORM será o único canal de comunicação com o banco, sanitizando os dados automaticamente.
- **Rate Limiting & DoS:** Um bot tenta derrubar o servidor pedindo a geração de 1.000 relatórios em PDF por segundo. **Defesa:** Implementação de estrangulamento global (Throttle). Endpoints normais (100 req/min). Endpoints pesados como Geração de PDF e Relatórios (5 req/min por IP/Usuário).
- **Uploads Maliciosos (Cavalos de Troia e Código Oculto):** Alguém tenta subir um script executável fingindo ser texto, ou oculta um código malicioso dentro dos "Metadados" de uma imagem/PDF real (Esteganografia). **Defesa:** 1. Validação estrita por *MIME-Type* profundo. 2. Sanitização do arquivo (remoção de metadados invisí­veis EXIF de imagens). 3. Armazenamento em diretório sem permissão de execução de scripts (NoExec). 4. Na hora de baixar/ver o anexo, o servidor impõe cabeçalhos estritos (`Content-Disposition` e `Content-Type`) forçando o navegador a tratar o arquivo apenas como mí­dia passiva, sendo impossí­vel o código malicioso "acordar" no computador do Operador.

## 9. Recursos Estruturais do Sistema

- **Autenticação:** Baseado em e-mail e senha. As senhas devem ser armazenadas utilizando um modelo seguro de hash. A sessão será fornecida à PWA através de Token (ex: JWT) fornecido pela API.
- **Controle Baseado em Papéis (RBAC):** Os perfis garantem segurança nos fluxos tanto visualmente pelo frontend, escondendo abas proibidas, quanto sistemicamente pela API, validando permissões no backend.
- **Soft Delete:** A exclusão total está proibida. Qualquer registro deletado recebe uma flag e a data de deleção, desaparecendo das listas de criação e caixas de seleção. Relatórios passados garantem a quebra dessa regra para continuar apresentando os itens inativos sem gerar inconsistência visual financeira.
- **Auditoria:** Registro invisí­vel e perpétuo gravando obrigatoriamente a assinatura (`created_by`, `updated_by`, `deleted_by`) atrelado a carimbos de tempo em quase todas as entidades.
- **Snapshot de Valores:** Arquitetura de persistência de dados. A linha do orçamento armazena o valor do Custo do Material individual e da Venda, no formato de foto, impedindo que flutuações de preços nos itens do fornecedor afetem transações antigas e aprovadas.
- **Dicionário de Atributos:** Uma matriz global e cadastrável que ajuda o Operador a montar itens do catálogo sem repetir caracterí­sticas escritas à mão erroneamente.

## 10. Entidades do Sistema

As principais entidades funcionais que formam o núcleo de dados:
- **Usuários (`Usuario`):** Colaboradores, controle de perfil, senha hasheada, PIN de segurança de 6 dígitos e auditoria de atividade.
- **Clientes e Fornecedores (`ClienteFornecedor`):** Informações cadastrais completas, flags de inscrição estadual e histórico de cortesias/inadimplência (para clientes) e compras (para fornecedores).
- **Equipamentos (`Equipamento`):** Propriedades/veículos da oficina com placa/identificação e histórico relacional de transferência de donos (`ClienteEquipamento`).
- **Catálogo Base (`Item`, `Produto`, `FichaTecnica`):** Materiais e insumos vinculados a unidades de medida (`DicionarioUom`), atributos técnicos dinâmicos (`ItemAtributoValor`, `DicionarioAtributo`), além de peças/serviços compostos com tempo de mão de obra e composição BOM.
- **Orçamentos (`Orcamento`, `OrcamentoItem`, `OrcamentoPropostaPagamento`):** Core operacional com snapshot de custo/venda e acompanhamento duplo (Status Operacional vs Financeiro).
- **Faturas (`Fatura`, `FaturaPropostaPagamento`):** Título financeiro mestre aglutinador de orçamentos, comandando o faturamento agregado e o Contas a Receber. Centraliza os documentos fiscais de saída e cobrança através de campos estruturados para número da NF-e de venda, anexo da DANFE em PDF, boleto bancário, linha digitável e comprovantes de liquidação.
- **Lançamentos Financeiros (`LancamentoFinanceiro`):** Movimentações de Competência (Contas a Pagar/Receber) e Caixa Real (Extrato), cobrindo recebimentos parciais, despesas e transferências inter-contas.
- **Estruturas Financeiras (`ContaBancaria`, `CartaoCredito`, `FaturaCartao`, `CategoriaFinanceira`, `MeioPagamento`, `RegraPagamento`):** Gavetas bancárias (com cheque especial), cartões corporativos (com rollover), categorias DRE, instrumentos físicos e matriz de parcelamentos/descontos.
- **Documentos Fiscais de Entrada (`DocumentoFiscalCompra`, `NotaCompraItem`):** Notas de compra com itens associados para retroalimentação automática do motor de custos BOM.
- **Auditoria, Manifesto e Segurança (`LogEstorno`, `ConfiguracaoGlobal`, `ControleArquivoLog`, `AnexoGeralCliente`):** Rastro perpétuo de estornos, manifesto TTL de retenção de logs físicos e parâmetros globais do sistema.

## 11. Modelo de Dados Proposto

### Convenção Técnica Mandatória de Nomenclatura (Django ORM, MySQL e API REST)

Para garantir integridade de código, evitar falhas de encoding no Python/MySQL e padronizar o desenvolvimento de Models, Migrations, Serializers e Endpoints pela IA codificadora, aplicam-se compulsoriamente as seguintes regras de nomenclatura:

1. **Classes de Models (Django ORM):** Adotam estritamente **PascalCase (CamelCase) no singular em ASCII puro** (sem acentos, cedilhas ou caracteres especiais). Exemplo: `LancamentoFinanceiro`, `OrcamentoItem`, `CartaoCredito`.
2. **Nomes Físicos de Tabelas (`db_table`):** Adotam estritamente **snake_case no plural em ASCII puro**. Exemplo: `lancamentos_financeiros`, `orcamento_itens`, `cartoes_credito`.
3. **Nomes de Colunas e Atributos:** Adotam estritamente **snake_case minúsculo em ASCII puro**. Exemplo: `tipo_lancamento`, `data_pagamento`, `conciliado_por_id`.
4. **Chaves Primárias e Estrangeiras (PK/FK):**
   - *Chave Primária (PK):* Padronizada universalmente como `id` (`BigAutoField` auto-increment).
   - *Chave Estrangeira (FK):* Nomeada compulsoriamente no formato `{entidade_singular}_id` em snake_case (ex: `cliente_id`, `fatura_id`, `meio_pagamento_id`, `conta_destino_id`, `usuario_id`, `conciliado_por_id`).
5. **Campos Booleanos:** Nomeados com prefixos claros como `is_` ou verbos afirmativos no presente (ex: `is_ativo`, `is_conciliado`, `isento_ie`, `permite_taxa_maquininha`, `permite_limite_emergencial`, `is_2fa_enabled`).
6. **Datas e Carimbos de Tempo:**
   - *Datas Puras (`DateField`):* Prefixo `data_` (ex: `data_emissao`, `data_vencimento`, `data_compra`, `data_fechamento_real`).
   - *Timestamps (`DateTimeField`):* Sufixo `_at` para auditoria padrão (`created_at`, `updated_at`, `deleted_at`) e prefixo `data_` para eventos de negócio (`data_pagamento`, `data_conciliacao`, `data_vinculo`, `data_estorno`).
7. **Rotas da API REST:** Padronizadas em **kebab-case no plural** para recursos de domínio (ex: `/api/orcamentos/`, `/api/lancamentos-financeiros/`, `/api/contas-bancarias/`, `/api/meios-pagamento/`, `/api/regras-pagamento/`, `/api/auth/unlock-pin/`).

#### Matriz De-Para de Nomenclatura das 29 Entidades do Sistema

| # | Entidade Funcional | Classe Django ORM (`models.Model`) | Nome da Tabela (`db_table`) | Rota Base da API REST |
| :- | :--- | :--- | :--- | :--- |
| 1 | Usuários | `Usuario` | `usuarios` | `/api/usuarios/` |
| 2 | Permissões | `Permissao` | `permissoes` | `/api/permissoes/` |
| 3 | Clientes e Fornecedores | `ClienteFornecedor` | `clientes_fornecedores` | `/api/clientes-fornecedores/` |
| 4 | Equipamentos | `Equipamento` | `equipamentos` | `/api/equipamentos/` |
| 5 | Vínculo Cliente-Equipamento | `ClienteEquipamento` | `cliente_equipamento` | `/api/cliente-equipamentos/` |
| 6 | Dicionário UOM | `DicionarioUom` | `dicionario_uom` | `/api/dicionario-uom/` |
| 7 | Dicionário Atributos | `DicionarioAtributo` | `dicionario_atributos` | `/api/dicionario-atributos/` |
| 8 | Itens (Materiais/Insumos) | `Item` | `itens` | `/api/itens/` |
| 9 | Valores de Atributos do Item | `ItemAtributoValor` | `item_atributos_valores` | `/api/item-atributos-valores/` |
| 10 | Produtos (Receitas) | `Produto` | `produtos` | `/api/produtos/` |
| 11 | Ficha Técnica (BOM) | `FichaTecnica` | `ficha_tecnica` | `/api/fichas-tecnicas/` |
| 12 | Orçamentos | `Orcamento` | `orcamentos` | `/api/orcamentos/` |
| 13 | Itens do Orçamento | `OrcamentoItem` | `orcamento_itens` | `/api/orcamento-itens/` |
| 14 | Faturas | `Fatura` | `faturas` | `/api/faturas/` |
| 15 | Propostas de Pgto da Fatura | `FaturaPropostaPagamento` | `fatura_propostas_pagamento` | `/api/fatura-propostas-pagamento/` |
| 16 | Propostas de Pgto do Orçamento | `OrcamentoPropostaPagamento` | `orcamento_propostas_pagamento` | `/api/orcamento-propostas-pagamento/` |
| 17 | Lançamentos Financeiros | `LancamentoFinanceiro` | `lancamentos_financeiros` | `/api/lancamentos-financeiros/` |
| 18 | Contas Bancárias | `ContaBancaria` | `contas_bancarias` | `/api/contas-bancarias/` |
| 19 | Cartões de Crédito | `CartaoCredito` | `cartoes_credito` | `/api/cartoes-credito/` |
| 20 | Faturas de Cartão | `FaturaCartao` | `faturas_cartao` | `/api/faturas-cartao/` |
| 21 | Categorias Financeiras | `CategoriaFinanceira` | `categorias_financeiras` | `/api/categorias-financeiras/` |
| 22 | Meios de Pagamento | `MeioPagamento` | `meios_pagamento` | `/api/meios-pagamento/` |
| 23 | Regras de Pagamento | `RegraPagamento` | `regras_pagamento` | `/api/regras-pagamento/` |
| 24 | Documentos Fiscais de Compra | `DocumentoFiscalCompra` | `documentos_fiscais_compra` | `/api/documentos-fiscais-compra/` |
| 25 | Itens da Nota de Compra | `NotaCompraItem` | `nota_compra_itens` | `/api/nota-compra-itens/` |
| 26 | Anexos de Clientes | `AnexoGeralCliente` | `anexos_gerais_clientes` | `/api/anexos-gerais-clientes/` |
| 27 | Log de Estornos | `LogEstorno` | `log_estornos` | `/api/log-estornos/` |
| 28 | Configurações Globais | `ConfiguracaoGlobal` | `configuracoes_globais` | `/api/configuracoes-globais/` |
| 29 | Manifesto de Logs | `ControleArquivoLog` | `controle_arquivos_log` | `/api/controle-arquivos-log/` |

---

### Especificação Detalhada das Tabelas

O banco de dados (MySQL) contemplará a arquitetura de dados íntegra. Abaixo a modelagem formal das tabelas, colunas, tipos e relacionamentos:

- **Tabela Usuarios:** `id` (PK), `email`, `password_hash`, `role` (Admin/Operador), `pin_hash` (varchar, nullable - hash do PIN de 6 dígitos para destravamento ágil de Soft Lock), `tentativas_login_falhas` (int, default 0), `bloqueado_ate` (datetime, nullable para controle anti-bruteforce), `auth_provider` (string/enum para V2, default "LOCAL"), `is_2fa_enabled` (boolean para V2).
- **Tabela Permissoes:** `id` (PK), `usuario_id` (FK 1:1), `acesso_comercial` (boolean, default False), `acesso_tesouraria` (boolean, default False), `acesso_compras` (boolean, default False), `gestao_catalogo` (boolean, default False), `visao_relatorios` (boolean, default True), `cadastros_financeiros` (boolean, default False), `gestao_dicionario_uom` (boolean, default False), `configuracoes_globais` (boolean, default False), `gestao_equipe` (boolean, default False), `auditoria_logs_recovery` (boolean, default False).
- **Tabela Clientes_Fornecedores:** `id` (PK), `tipo` (Cliente, Fornecedor, Ambos), `tipo_pessoa` (PF, PJ), `nome_razao` (varchar, obrigatório), `nome_fantasia` (varchar, nullable), `cnpj_cpf` (varchar 20, nullable, unique quando preenchido), `inscricao_estadual` (varchar, nullable), `isento_ie` (boolean, default False), `email` (varchar, nullable), `telefone` (varchar 20, obrigatório), `cep` (varchar 10, nullable), `logradouro` (varchar 255, nullable), `numero` (varchar 20, nullable), `complemento` (varchar 100, nullable), `bairro` (varchar 100, nullable), `cidade` (varchar 100, nullable), `uf` (varchar 2, nullable). (Soft Delete e Auditoria).
- **Tabela Equipamentos:** `id` (PK), `placa` (varchar 10, nullable - máscara antiga/Mercosul), `identificacao` (varchar 100, nullable - frota/chassi/código interno em maiúsculas sem acento), `descricao` (varchar 255, obrigatório). (Soft Delete e Auditoria).
- **Tabela Relacional Cliente_Equipamento (Vínculos):** `id` (PK), `cliente_id` (FK), `equipamento_id` (FK), `data_vinculo`, `is_ativo` (controla transferências preservando o passado).
- **Tabela Dicionario_UOM (Unidades de Medida Oficiais):** `id` (PK), `sigla` (varchar 10, ex: "m²", "cm²", "L", "mL", "kg", "g", "m", "UN", "CX", "BARRA"), `descricao` (varchar 50, ex: "Metro Quadrado", "Litro", "Quilograma", "Unidade"). Povoada com seeders iniciais padrão Brasil e gerenciada via tela administrativa.
- **Tabela Dicionario_Atributos (Catálogo Central de Características):** `id` (PK), `nome_atributo` (varchar 50, ex: "Espessura", "Diâmetro", "Material / Liga", "Rosca", "Marca / Fabricante"). Povoada com seeders iniciais e gerenciada via tela administrativa.
- **Tabela Itens (Catálogo de Materiais e Insumos):** `id` (PK), `nome` (varchar), `unidade_compra_id` (FK apontando para `Dicionario_UOM`), `unidade_consumo_id` (FK apontando para `Dicionario_UOM` - opcional), `fator_conversao` (decimal, proporção matemática de compra para consumo), `ultimo_custo_compra` (decimal), `data_ultima_compra` (datetime, nullable), `tipo_uso` (varchar/enum: 'Insumo Produtivo', 'Material de Consumo', 'EPI', 'Ferramental'). (Soft Delete e Auditoria).
- **Tabela Item_Atributos_Valores (Especificação Técnica Dinâmica do Item):** `id` (PK), `item_id` (FK apontando para `Itens`), `atributo_id` (FK apontando para `Dicionario_Atributos`), `valor` (varchar 255, ex: "6.35 mm (1/4 pol)", "ASTM A36", "E7018"). *(Sub-grid integrado no formulário de cadastro/edição do Item).*
- **Tabela Produtos (O que fabricamos / Receitas de Serviço):** `id` (PK), `nome` (varchar), `descricao` (texto longo/varchar para especificações adicionais), `unidade_venda_id` (FK apontando para `Dicionario_UOM`, default "UN"), `tempo_estimado_execucao` (decimal em Horas de Mão de Obra). (Soft Delete e Auditoria).
- **Tabela Ficha_Tecnica (Motor BOM — 1:N):** `id` (PK), `produto_id` (FK apontando para `Produtos`), `item_id` (FK apontando para `Itens`), `quantidade_utilizada` (decimal na unidade de consumo do item). *(Sub-grid integrado na tela do Produto para cálculo do Preço de Custo Apurado em tempo real).*
- **Tabela Orcamentos:** `id` (PK), `cliente_id` (FK apontando para `Clientes_Fornecedores`), `equipamento_id` (FK apontando para `Equipamentos`), `fatura_id` (FK apontando para `Faturas`, nullable — nulo enquanto 'A Faturar' e preenchido quando vinculado a uma Pré-Fatura/Fatura), `data_geracao`, `data_validade`, `status_operacional` (Gerado, Enviado, Aprovado, Em Execução, Concluído, Cancelado), `status_financeiro` (A Faturar, Faturado, Pago, Cancelado), `valor_bruto`, `valor_desconto_aplicado`, `motivo_cancelamento` (varchar 500, nullable — preenchimento obrigatório ao cancelar). (Soft Delete e Auditoria).
- **Tabela Orcamento_Itens:** `id` (PK), `orcamento_id` (FK), `produto_id` (FK nula - Venda de Produto composto), `item_id` (FK nula - Venda avulsa e direta de um Item), `descricao_livre` (Texto para Lançamentos Manuais Livres, quando as chaves FKs forem Nulas), `quantidade`, `custo_snapshot`, `valor_venda_snapshot`.
- **Tabela Faturas:** `id` (PK), `cliente_id` (FK), `data_emissao`, `data_fechamento`, `status` (Rascunho [Pré-Fatura], Faturada [Fatura Final], Paga, Cancelada), `valor_bruto` (soma dos valores dos orçamentos agregados), `desconto_global` (desconto comercial negociado/aplicado), `valor_total_faturado` (valor líquido final a receber), `regra_pagamento_id` (FK apontando para `Regras_Pagamento`, nullable — nulo na Pré-Fatura e obrigatório na Fatura Final), `numero_nfe_venda` (varchar 50, nullable), `caminho_nfe_pdf` (varchar 500, nullable), `caminho_boleto_pdf` (varchar 500, nullable), `linha_digitavel_boleto` (varchar 100, nullable), `caminho_comprovante_pagamento` (varchar 500, nullable), `motivo_cancelamento` (varchar 500, nullable — preenchimento obrigatório ao cancelar fatura). Relacionamento um-para-muitos vinculando Orcamentos à Fatura. (Soft Delete e Auditoria).
- **Tabela Fatura_Propostas_Pagamento (Opções sugeridas no Espelho da Pré-Fatura):** `id` (PK), `fatura_id` (FK apontando para `Faturas`), `regra_pagamento_id` (FK apontando para `Regras_Pagamento`), `desconto_personalizado` (decimal, nullable — permite ao Operador sobrescrever o desconto padrão do cadastro para aquela simulação).
- **Tabela Orcamento_Propostas_Pagamento (Opções sugeridas no PDF do Orçamento):** `id` (PK), `orcamento_id` (FK apontando para `Orcamentos`), `regra_pagamento_id` (FK apontando para `Regras_Pagamento`), `desconto_personalizado` (decimal, nullable).
- **Tabela Lancamentos_Financeiros (Lançamentos e Recebimentos Parciais):** `id` (PK), `fatura_id` (FK apontando para `Faturas`, nullable — preenchido em parcelas e recebimentos de clientes), `conta_id` (FK apontando para `Contas_Bancarias`, nullable — obrigatório na liquidação real de caixa como conta de movimentação/origem), `conta_destino_id` (FK apontando para `Contas_Bancarias`, nullable — preenchido exclusivamente em transferências inter-contas), `meio_pagamento_id` (FK apontando para `Meios_Pagamento`, nullable — instrumento físico de pagamento/recebimento), `cartao_credito_id` (FK apontando para `Cartoes_Credito`, nullable — preenchido em despesas no cartão corporativo), `fatura_cartao_id` (FK apontando para `Faturas_Cartao`, nullable — fatura do cartão corporativo a qual a despesa pertence), `categoria_id` (FK apontando para `Categorias_Financeiras`), `tipo_lancamento` (Entrada, Saída, Transferência), `descricao` (varchar 255, nullable — histórico/detalhes do lançamento), `valor`, `data_vencimento`, `data_pagamento` (datetime, nullable se ainda pendente), `status_pagamento` (A Vencer, Vencido, Pago, Cancelado), `motivo_cancelamento` (varchar 500, nullable — preenchido no cancelamento de títulos a vencer), `is_conciliado` (boolean, default False — flag de conciliação bancária), `data_conciliacao` (datetime, nullable — data/hora em que a conciliação foi efetivada), `conciliado_por_id` (FK apontando para `Usuarios`, nullable — colaborador que realizou a conciliação). *(Regra de Saldo: registros com status 'A Vencer' ou 'Vencido' não alteram o saldo bancário; registros com status 'Pago' afetam imediatamente o saldo da `conta_id`; despesas com `cartao_credito_id` preenchido afetam exclusivamente a fatura do cartão sem debitar a conta bancária até a liquidação da fatura).* (Soft Delete e Auditoria).
- **Tabela Contas_Bancarias:** `id` (PK), `nome`, `saldo`, `limite_credito` (cheque especial que permite saldo negativo até este limite). (Soft Delete e Auditoria).
- **Tabela Cartoes_Credito:** `id` (PK), `nome`, `dia_vencimento` (int), `dia_fechamento_padrao` (int), `limite` (decimal), `permite_limite_emergencial` (boolean, default False), `conta_bancaria_id` (FK apontando para `Contas_Bancarias`, nullable — conta preferencial de débito da fatura). (Soft Delete e Auditoria).
- **Tabela Faturas_Cartao:** `id` (PK), `cartao_id` (FK apontando para `Cartoes_Credito`), `mes_referencia` (varchar/date, ex: '2026-08'), `data_fechamento_real` (date — calculada inicialmente pelo dia de fechamento padrão, permitindo ajuste manual pelo gestor caso haja feriados/antecipações no mês), `status` (Aberta, Fechada, Paga). (Soft Delete e Auditoria).
- **Tabela Categorias_Financeiras:** `id` (PK), `nome`, `tipo` (Receita, Despesa, Transferência - neutra pro DRE), `categoria_pai_id` (opcional para subcategorias). (Soft Delete e Auditoria).
- **Tabela Meios_Pagamento (Dicionário de Instrumentos Financeiros):** `id` (PK), `nome` (PIX, Dinheiro, Boleto Bancário, Cartão de Crédito, Cartão de Débito, Transferência TED/DOC, Depósito Bancário, Cheque), `permite_taxa_maquininha` (boolean, default False), `ativo` (boolean, default True). (Soft Delete e Auditoria). Povoada com seeders padrão.
- **Tabela Regras_Pagamento (Matriz de Prazos e Condições Comerciais):** `id` (PK), `nome` (varchar 100, ex: "Boleto 30/60/90 Dias", "Pix à Vista com 5%", "Boleto 28 Dias"), `meio_pagamento_id` (FK apontando para `Meios_Pagamento`), `tipo_cobranca` (Enum: `A_VISTA`, `A_PRAZO`, `PARCELADO`), `numero_parcelas` (int, default 1), `prazo_primeira_parcela_dias` (int, default 0 — prazo para a 1ª parcela/vencimento: 0 para imediato no ato, 10, 15, 28, 30...), `intervalo_parcelas_dias` (int, default 0 — intervalo em dias entre parcelas subsequentes: 0 para à vista e a prazo único, 15, 30...), `desconto_concedido_padrao` (decimal, default 0.00 — % de desconto sugerido), `ativo` (boolean, default True). (Soft Delete e Auditoria).
- **Tabela Documentos_Fiscais_Compra:** `id` (PK), `num_nota`, `chave_acesso` (varchar 44, nullable), `fornecedor_id` (FK), `data_compra`, `valor_total`, `caminho_arquivo_anexo` (varchar 500, nullable). (Soft Delete e Auditoria).
- **Tabela Nota_Compra_Itens (O elo 1:N):** `id` (PK), `documento_fiscal_id` (FK apontando para a Nota Pai), `item_id` (FK apontando estritamente para a Tabela Itens), `quantidade_comprada`, `valor_unitario`.
- **Tabela Anexos_Gerais_Clientes:** `id` (PK), `cliente_id` (FK), `nome_documento`, `caminho_arquivo`.
- **Tabela Log_Estornos (Auditoria de Caixa):** `id` (PK), `lancamento_id` (FK), `usuario_id` (FK), `justificativa` (texto longo), `data_estorno`. Assegura rastro perpétuo de pagamentos anulados.
- **Tabela Configuracoes_Globais (Parâmetros Universais):** `id` (PK único), `validade_orcamento_dias`, `taxa_mao_de_obra_hora`, `razao_social`, `cnpj`, `telefone_contato`, `endereco_oficina`, `logo_empresa_url`, `tempo_ociosidade_minutos`, `tempo_expiracao_sessao_dias`, `retencao_logs_dias`, `smtp_host`, `smtp_port`, `smtp_user`, `smtp_password_encrypted` (armazenada via criptografia simétrica AES-256/Fernet), `smtp_use_tls` (boolean), `smtp_use_ssl` (boolean), `email_remetente_nome`.
- **Tabela Controle_Arquivos_Log (Manifesto de Expurgo):** `id` (PK), `caminho_arquivo_fisico` (aponta para o .log rotativo no disco), `data_criacao`, `data_expurgo_planejada`. Desacopla o peso textual do BD, mantendo apenas a matemática de retenção (TTL).

**Atributos de Auditoria e Matriz de Soft Delete:**
O sistema implementa uma camada centralizada de persistência e rastreabilidade dividida em três categorias estritas:

1. **Entidades Principais (Auditoria Plena e Soft Delete):**
   Recebem compulsoriamente os 6 campos de autoria (`created_at`, `updated_at`, `deleted_at`, `created_by_id`, `updated_by_id`, `deleted_by_id`): `Usuarios`, `Clientes_Fornecedores`, `Equipamentos`, `Itens`, `Produtos`, `Orcamentos`, `Faturas`, `Documentos_Fiscais_Compra`, `Contas_Bancarias`, `Cartoes_Credito`, `Faturas_Cartao`, `Categorias_Financeiras`, `Meios_Pagamento`, `Regras_Pagamento`, `Dicionario_UOM`, `Dicionario_Atributos` e `Lancamentos_Financeiros`.

2. **Tabelas Relacionais e Sub-Itens (Cascade Lógico):**
   Itens dependentes (`Orcamento_Itens`, `Item_Atributos_Valores`, `Ficha_Tecnica`, `Nota_Compra_Itens`, `Fatura_Propostas_Pagamento`, `Orcamento_Propostas_Pagamento`, `Anexos_Gerais_Clientes` e `Permissoes`) acompanham compulsoriamente a exclusão/restauração lógica do seu respectivo registro pai. A tabela `Cliente_Equipamento` preserva a rastreabilidade histórica de transferências via flag `is_ativo` e timestamp `data_vinculo`.

3. **Tabelas Imutáveis e Especiais (Sem Soft Delete — Invioláveis):**
   - `Log_Estornos`: Tabela append-only imutável para auditoria perpétua de baixas financeiras canceladas. Lançamentos do Caixa Real **não podem** ser apagados por soft delete; sofrem estorno mediante preenchimento obrigatório de justificativa.
   - `Controle_Arquivos_Log`: Manifesto de arquivos de log do servidor no disco, gerenciado exclusivamente pela rotina de expurgo físico (TTL).
   - `Configuracoes_Globais`: Registro único do sistema (Singleton id=1), suportando apenas atualização de valores e auditoria (`updated_at`, `updated_by_id`).

**Regras de Negócio e Integridade em Exclusões:**
- **Exclusão de Faturas:** Só é permitida se não houver recebimentos (lançamentos reais na tesouraria) atrelados a ela. Ao sofrer soft delete, os Orçamentos contidos na fatura são libertados e voltam para o status `A Faturar`.
- **Exclusão de Orçamentos:** Barrada pelo sistema caso o orçamento já esteja `Aprovado`, `Em Execução`, `Concluído` ou vinculado a uma `Fatura`. Para excluí-lo (soft delete), o operador deve manter o orçamento em **`Gerado`** ou **`Cancelado`**.
- **Exclusão de Itens (Catálogo):** Bloqueada sumariamente caso o Item conste na Ficha Técnica (Receita) de algum Produto. O sistema obriga a remoção da dependência prévia ou a inativação do material.

**Matriz Estratégica de Índices (Banco de Dados):**
*(Nota Arquitetural: Todas as Chaves Primárias, Chaves Estrangeiras e campos com UniqueConstraint já recebem indexação B-Tree automática nativa pelo Django ORM e MySQL InnoDB. A lista abaixo define a indexação mandatória adicional sobre campos de negócio, filtros de status, datas e autocompletes).*
Devido ao uso de filtros *Inline* dinâmicos nas tabelas, a performance do banco será garantida através da indexação mandatória (B-Tree/Hash) dos seguintes campos crí­ticos:
- **Identificadores Únicos (Busca Exata):** `cnpj_cpf` (Clientes), `identificacao_placa` (Equipamentos), `num_nota` (Compras).
- **Autocompletes Textuais:** `nome_razao` (Clientes), `nome` (Tabelas de Itens e Produtos).
- **Datas (Dashboards e Históricos):** `data_geracao` (Orçamentos), `data_fechamento` (Faturas), `data_vencimento` (Contas a Pagar/Receber), `data_pagamento` (Extrato), `data_compra` (Notas Fiscais de Entrada).
- **Status (Filtros Cruzados):** `status_operacional` e `status_financeiro` (Orçamentos), `status` (Contas).

**Matriz de Restrições de Unicidade e Integridade (`UniqueConstraint` e Campos Únicos):**
Para garantir integridade física no MySQL e impedir duplicações relacionais, o Django ORM aplicará as seguintes constraints no `class Meta` das entidades:
1. **`Item_Atributos_Valores`:** `UniqueConstraint(fields=['item_id', 'atributo_id'], name='unique_item_atributo')` — Impede que o mesmo atributo técnico (ex: "Espessura") seja cadastrado em duplicidade para o mesmo item.
2. **`Ficha_Tecnica`:** `UniqueConstraint(fields=['produto_id', 'item_id'], name='unique_produto_item_ficha')` — Impede que o mesmo item de matéria-prima apareça duplicado na receita de um mesmo produto.
3. **`Nota_Compra_Itens`:** `UniqueConstraint(fields=['documento_fiscal_id', 'item_id'], name='unique_nota_item')` — Garante que cada item comprado apareça apenas uma vez por nota fiscal de entrada.
4. **`Faturas_Cartao`:** `UniqueConstraint(fields=['cartao_id', 'mes_referencia'], name='unique_cartao_mes_referencia')` — Impede a criação acidental de duas faturas para o mesmo mês no mesmo cartão corporativo.
5. **`Orcamento_Propostas_Pagamento`:** `UniqueConstraint(fields=['orcamento_id', 'regra_pagamento_id'], name='unique_orcamento_regra_pgto')` — Impede sugerir a mesma regra de pagamento repetida no mesmo orçamento.
6. **`Fatura_Propostas_Pagamento`:** `UniqueConstraint(fields=['fatura_id', 'regra_pagamento_id'], name='unique_fatura_regra_pgto')` — Impede sugerir a mesma regra de pagamento repetida na mesma pré-fatura.
7. **Unicidades Simples (`unique=True`):** `Usuarios.email`, `Permissoes.usuario_id` (1:1), `Clientes_Fornecedores.cnpj_cpf` (quando preenchido/não-nulo — impede clientes ou fornecedores duplicados com o mesmo CPF/CNPJ), `Dicionario_UOM.sigla`, `Dicionario_Atributos.nome_atributo` e `Controle_Arquivos_Log.caminho_arquivo_fisico`.

**Execução do Banco por Migrations:**
Toda essa modelagem, desde a criação estrutural de tabelas até colunas de auditoria e í­ndices numéricos, não deverá ser exigida manualmente do usuário. A aplicação utilizará a arquitetura de **Migrations** geradas pelo backend (ex: ferramenta nativa do Django).

As migrations armazenam scripts versionados seguros que definem: criação das tabelas, campos, chaves primárias, chaves estrangeiras, constraints, í­ndices e campos de auditoria e soft delete.

- **Mecanismo de controle:** Para evitar execução duplicada, a stack do backend deverá manter o rastreio intrí­nseco (o framework registra numa tabela auxiliar quais migrations já foram concluí­das na base SQL).
- **Proteção e segurança:** A pasta que abrigará os scripts (ex: `database/migrations/`) ficará restrita nas entranhas do `[Diretório do Projeto - Repositório]`. Nenhum script de migration terá acesso exposto a requisições URL pelo navegador.
- **Modo de execução:** As migrations ocorrerão unicamente por execução interna e segura, via linha de comando no ambiente virtual (`python manage.py migrate`).

## 12. Módulos e Telas

A estrutura visual e de navegação (UI/UX) guiada pelo PWA seguirá os seguintes padrões:

- **Layout Base (Menu Lateral):** A navegação principal ocorrerá por um Menu Lateral (Sidebar) com comportamento retrátil inteligente (expande no hover/clique, recolhe com clique no backdrop).
- **Tabelas de Dados como Relatórios Visuais (Filtros Dinâmicos e Inline Headers):** **Padrão de UX mandatória.** Além dos cabeçalhos com `textbox` para buscas em tempo real, as listagens principais (Orçamentos, Faturas, Contas a Pagar/Receber) possuirão painéis de **Filtros Combinados Avançados**. O objetivo é transformar as próprias telas de rotina em relatórios visuais gerenciais. Exemplo em Orçamentos: cruzar `Status Operacional = Concluí­do` com `Status Financeiro = Não Faturado` para auditar dinheiro parado na oficina.
- **Filtros Temporais Globais:** Módulos de visão geral (como o Dashboard) suportarão atalhos rápidos de tempo no topo ("Este Mês", "Mês Passado", "Este Ano").

**Regra Geral de Comportamento Visual (Abordagem Híbrida de Permissões):**
O PWA lidará com os bloqueios de autorização de forma inteligente:
- **Ocultação Total:** Menus laterais, abas inteiras e botões de ações críticas (ex: Lixeira) não são renderizados se o usuário não tiver permissão.
- **Bloqueio Visual:** Flip Cards de Dashboard e Atalhos Interligados continuam na tela para não quebrar o layout, mas ficam censurados (ex: `R$ ***,**`) e desabilitados com um ícone de cadeado `[🔒]` acompanhados de um *tooltip* de aviso.

**Mapeamento Detalhado dos Módulos (Telas):**

- **1. Acesso (Login):** Telas públicas de Autenticação, Recuperação de Senha (via código alfanumérico de 8 dígitos com validade de 30 min enviado por e-mail), Criação Inicial de Senha (via link de convite), Modal de Desbloqueio Rápido por PIN de 6 dígitos (após 30 min de Soft Lock) e Painel Informativo de Bloqueio por Rate Limit (Anti-Bruteforce).
- **2. Dashboard Principal (Visão Geral):** 
  - *Flip Cards Interativos:* 5 cartões que giram ao clique no corpo (Operação, Faturamento, Receita, Caixa, Alertas). Cada "face" do cartão possui um botão/link no rodapé (`Ver detalhes ➔`) com área de clique isolada que não ativa o giro, apenas redireciona para a página da lista correspondente.
  - *Atalhos Rápidos e Gráficos:* Botões de ações frequentes e Gráfico de Barras (Receitas x Despesas) acompanhado do Feed de Atividades Recentes.
- **3. Módulo Operacional (Orçamentos, Faturas e Clientes):** Telas de listagem com busca avançada por status. Perfil do Cliente com Dossiê Financeiro. Cadastro de Clientes e Fornecedores estruturado com **hierarquia visual top-down** (o seletor `[PF / PJ]` e o campo `[CPF / CNPJ]` posicionam-se compulsoriamente no topo absoluto, validando e buscando dados no `onBlur`), validação matemática de CPF (módulo 11), botão `[Buscar CNPJ na Receita]` para preenchimento cadastral automático em 1 clique, e **Modal Flutuante de Cadastro Rápido** durante o orçamento (exigindo apenas Nome e Telefone para clientes avulsos). Interface limpa de elaboração de Orçamentos e painel agregador para conversão de faturas (onde faturas geradas formam uma árvore ligando as dívidas parciais até que encerrem em "Pago"). Na conversão da Pré-Fatura em Fatura Final, a interface renderiza um seletor visual com as opções de pagamento previamente enviadas na simulação (lidas de `fatura_propostas_pagamento`) para seleção e preenchimento automático em 1 clique, suportando também ajustes finos de desconto ou escolha de novas condições comerciais. Botões de ação `[Cancelar Orçamento]` e `[Cancelar Fatura]` acionam compulsoriamente um **Modal de Cancelamento com Justificativa Obrigatória** (mínimo 10 caracteres); registros cancelados exibem tarja visual destacada no topo contendo autor, data/hora e o motivo da anulação.
- **4. Tesouraria (Caixa Real e Conciliação):** Visão da conta corrente corporativa, transferências inter-contas (com especificação de conta de origem e conta de destino), modal universal de liquidação (com impacto bancário imediato), cancelamento de títulos a vencer via modal de justificativa obrigatória, modal de estorno com justificativa obrigatória e gravação perpétua em `Log_Estornos` para baixas de caixa liquidado (`status = Pago`), e **Tela de Conciliação Bancária Split-Screen (OFX/CSV)**:
  - *Coluna Esquerda (Extrato Bancário):* Transações do arquivo OFX/CSV importado com data, histórico bancário e valor.
  - *Coluna Direita (Lançamentos do ERP):* Lançamentos financeiros com badges visuais de status (`[✅ Conciliado]`, `[🕒 Pendente]`, `[⚠️ Não Localizado no Extrato]`).
  - *Ações Rápidas em Linha:* Motor de match automático 1:1, agrupamento de match múltiplo (1:N), botão `[Lançamento Rápido no Ato]` (criação instantânea de despesas/tarifas para match imediato), botão `[Trocar Conta Bancária]` (corrige alocação do lançamento em 1 clique) e botão `[Estornar com Justificativa]` (anula baixas indevidas). Toda conciliação efetivada registra compulsoriamente `is_conciliado = True`, o carimbo de data/hora (`data_conciliacao = NOW()`) e o operador responsável (`conciliado_por_id = request.user.id`) em cada lançamento.
- **5. Cartões Corporativos (Sub-Módulo da Tesouraria):** Interface exclusiva para cartões com a linha do tempo horizontal de faturas (Abertas, Fechadas, Pagas). Permite visualizar as micro-despesas na fatura aberta (sem debitar o saldo bancário até o fechamento/liquidação) e o botão principal para liquidação e rollover financeiro (gerando a saída real da conta bancária de pagamento).
- **6. Módulo de Compras (Notas Fiscais de Entrada e Fornecedores):** Tela de listagem e cadastro completo de Fornecedores (com histórico de preços e compras), tela de listagem de notas fiscais com modal de vinculação de itens ao catálogo, input manual, modal de cadastro rápido de Fornecedor na própria tela da nota e área de anexo físico de XML/PDF para registrar a retroalimentação de custos.
- **7. Catálogo Base:** Interface de Veículos/Equipamentos (com log de troca de donos), cadastro de Materiais (Itens com atributos dinâmicos e fator de conversão) e Receitas de Produção (Produtos com tempo de mão de obra e Ficha Técnica BOM).
- **8. Relatórios Estratégicos (Central Analítica):** Acesso às telas focadas no cruzamento de dados como Curvas ABC, Painel de Inadimplência (gestão de faturas vencidas em tela), Dossiê Histórico, DRE Simplificado e o **Painel do Relatório de Divergências de Conciliação**:
  - *Estrutura em Duas Abas Analíticas:*
    - **Aba 1 (Sobras do Extrato Bancário):** Transações que constam no banco mas não no ERP (ações: `[Lançamento Rápido no Ato]` ou `[Ignorar]`).
    - **Aba 2 (Sobras do ERP / Não Localizados no Banco):** Lançamentos registrados no ERP que não constam no extrato (ações: `[Trocar Conta Bancária]`, `[Estornar com Justificativa]` ou `[Manter Pendente]`).
  - *Filtros e Exportação:* Filtros por Conta Bancária, Período e Tipo de Divergência, com exportação consolidada em **PDF** e **CSV**.
- **9. Cadastros Financeiros Estruturais:** Telas administrativas organizadas em abas dedicadas:
  - *Contas Bancárias:* Cadastro e parametrização de contas correntes, caixas físicos e definição do `Limite de Cheque Especial`.
  - *Meios de Pagamento (Dicionário de Instrumentos):* Gerenciamento dos instrumentos físicos de movimentação (Pix, Dinheiro, Boleto, Cartões, TED, Cheque), permitindo ativar/inativar instrumentos e configurar o toggle `permite_taxa_maquininha`.
  - *Regras de Pagamento (Condições Comerciais):* Parametrização da matriz de prazos e parcelamentos (à vista imediato no ato, a prazo em parcela única com vencimento futuro, ou parcelado em N vezes, com número de parcelas, prazo da 1ª parcela/vencimento, intervalo de dias e percentual de desconto sugerido).
  - *Categorias Financeiras:* Árvore hierárquica de categorias e subcategorias classificadas por tipo (Receita, Despesa e Transferência neutra para o DRE).
- **10. Central do Administrador (Configurações, Equipe e Logs):** Dicionário Central UOM e Atributos, Parâmetros Globais (dados da empresa, logo e SMTP com presets e teste em tempo real), **Gestão de Equipe** (10 Toggles Dinâmicos por usuário e desbloqueio manual de contas anti-bruteforce), **Log Viewer** nativo para erros do servidor e **Painel de Lixeira e Restauração (Soft Delete)**:
  - *Visão do Administrador (Lixeira Global):* Grid com filtros avançados por tipo de entidade, data de inativação e usuário autor, com ação exclusiva de `[Restaurar]` (reverte `deleted_at = NULL`). Não há ação de deleção física (hard delete) no banco de dados na V1.
  - *Visão do Operador (Minha Lixeira):* Exibe exclusivamente os registros criados e excluídos pelo próprio operador logado (respeitando permissões comerciais), com botão de `[Restaurar]`.

## 13. Fluxos Funcionais e a Cascata de Documentos

O sistema opera sob uma rí­gida "Cascata de Documentos" para garantir integridade financeira, dividida em três fases vitais:

**Fase 1: O Orçamento**
- O Operador inicia o Orçamento. Se o Cliente ou Veículo não existir, um **Modal Flutuante de Cadastro Rápido** permite o cadastramento ágil na mesma tela exigindo **apenas Nome e Telefone** (com suporte a busca automática de dados por CNPJ e validação de CPF), sem perder o progresso.
- **Inserção de Linhas no Orçamento:** O sistema permite a entrada de 3 tipos de registros na mesma listagem financeira (e suportados pelas chaves da tabela `Orçamento_Itens`):
  1. **Produtos:** Puxa do catálogo os itens compostos fabricados pela oficina (trazendo embutida a Ficha Técnica e Mão de Obra).
  2. **Itens Simples:** Venda direta avulsa de um material do catálogo sem ficha técnica (ex: Vender apenas uma "Dobradiça" que a oficina comprou, sem prestar um serviço em cima).
  3. **Lançamentos Manuais Livres:** Digitação de texto livre na hora (descrição_livre, qtd e valor individual), para serviços únicos ou materiais avulsos que não merecem ser cadastrados no Catálogo permanente.
- O resumo financeiro (Subtotal/Total) consolida esses 3 formatos e é responsivo (fixo na lateral em desktops, no rodapé em mobiles).
- O sistema apresenta um **Tooltip/Alerta descartável (X)** no topo se o cliente estiver inadimplente.
- **Flexibilidade Comercial na Aprovação:** A transição de status para "Aprovado" e a execução do serviço não são bloqueadas por ausência de dados fiscais completos (endereço, IE ou CPF/CNPJ), permitindo fluxo contínuo e ágil para clientes avulsos de balcão.
- O Operador pode inserir opcionalmente *Propostas de Pagamento* (com possibilidade de personalizar descontos) para o cliente escolher no PDF.
- Concluído o serviço na oficina, o orçamento fica com Status Operacional `CONCLUÍDO` e Status Financeiro `A FATURAR`, pronto na conta corrente do cliente.

**Fase 2: A Pré-Fatura (Espelho de Aglutinação)**
- O Operador seleciona na conta corrente do cliente os orçamentos prontos com status financeiro `A FATURAR`.
- O sistema gera o registro de Fatura em estado de **`RASCUNHO` (Pré-Fatura)**, somando os valores individuais e calculando o `valor_bruto` consolidado.
- O Operador seleciona as **Opções de Pagamento Sugeridas** no formulário, podendo **sobrescrever livremente as regras de desconto** em relação ao cadastro padrão (ex: conceder 7% no Pix em vez dos 5% padrão).
- O sistema gera o **PDF Espelho da Pré-Fatura** detalhando os serviços e apresentando as opções para envio ao cliente.
- **Regra de Ouro:** A Pré-Fatura *não gera* movimentações no Contas a Receber, permitindo adicionar/remover orçamentos livremente.

**Fase 3: A Fatura Final (O Gatilho Financeiro)**
- Com a definição da forma de pagamento pelo cliente, a Pré-Fatura é convertida em **`FATURADA` (Fatura Final)**.
- **Obrigatório:** O Operador vincula a **Regra de Pagamento Definitiva** (`regra_pagamento_id`), define o `desconto_global` final acordado e calcula o `valor_total_faturado` líquido.
- **Gatilho Automático:** Ao salvar, o sistema:
  1. Transita o status financeiro de todos os orçamentos agrupados para **`FATURADO`** (mantendo o status operacional intacto);
  2. Gera automaticamente as parcelas no **Contas a Receber** com `status_pagamento = 'A Vencer'` e as datas calculadas pela regra escolhida, atualizando o Regime de Competência e os Dashboards (sem impacto imediato no saldo bancário);
  3. Permite anexar a NF-e de venda emitida, o boleto gerado e transcrever a linha digitável.

**Fase 4: Liquidação e Quitação Total**
- Conforme os pagamentos vão sendo realizados e liquidados na Tesouraria (ou conciliados via extrato), cada baixa gera um lançamento financeiro `PAGO` que injeta o saldo real imediatamente na Conta Bancária e amortiza a dívida da fatura.
- Ao cobrir **100% do valor faturado**, a Fatura transita automaticamente para **`PAGA`**, e todos os orçamentos vinculados têm seu status financeiro transitado automaticamente para **`PAGO`**.

**Fase 5: Cancelamentos e Estornos com Justificativa Obrigatória**
- **Cancelamento de Orçamentos:** Transita o status para `CANCELADO`, grava a justificativa obrigatória (mínimo 10 caracteres) no campo `motivo_cancelamento`, registra autor/timestamp e dispara log de auditoria.
- **Cancelamento de Faturas:** Transita a fatura para `CANCELADA`, grava o `motivo_cancelamento`, reverte compulsoriamente os orçamentos agrupados para `A FATURAR` e anula as parcelas a vencer no Contas a Receber.
- **Cancelamento de Títulos a Vencer vs Estorno de Caixa Liquidado:** Cancelar uma previsão no Contas a Pagar/Receber grava `status_pagamento = 'Cancelado'` e o `motivo_cancelamento`. Cancelar uma baixa já liquidada (`status = 'Pago'`) aciona o fluxo de **Estorno**, revertendo o saldo da conta bancária e gravando a linha imutável com justificativa na tabela `Log_Estornos`.

## 14. Validações e Regras de Negócio

As operações garantirão a resiliência via backend:

- **Bloqueio Inviolável de Perfil:** Operadores não têm acesso às áreas restritas do painel de equipe de jeito nenhum.
- **Restrição de Ocultação Financeira:** Soft delete obrigatório em entidades de configuração financeira.
- **Política Rígida de Cancelamento com Justificativa Obrigatória e Rastreabilidade:** O cancelamento de Orçamentos, Faturas e Lançamentos Financeiros não pode ser efetuado de forma acidental ou sem justificativa. A ação exige compulsoriamente modal com preenchimento de justificativa textual (mínimo 10 caracteres), persistida no atributo `motivo_cancelamento`, com carimbo de autoria (`updated_by_id = request.user.id`, `updated_at = NOW()`), disparo de evento estruturado no log físico do servidor e desvinculação em cascata dos registros dependentes.
- **Mecânica de Retenção de Logs em Massa (Manifesto):** O texto de falhas/segurança reside em arquivos físicos rotativos diários (`logs/app-YYYY-MM-DD.log`). O BD (Tabela de Manifesto `Controle_Arquivos_Log`) controla apenas a data limite (`data_expurgo_planejada`), eliminando qualquer necessidade de renomear arquivos no disco.
  - *Aumento do prazo:* O BD roda um UPDATE imediato e silencioso empurrando a data de expurgo de todos os logs para o futuro.
  - *Redução do prazo:* O sistema exige aceite do Admin: aplicar a redução retroativamente (apagando logs velhos imediatamente) ou aplicar apenas aos novos salvamentos (mantendo os arquivos antigos com sua vida útil original do manifesto).
- **Regra de Blindagem Comercial (Não-Retroatividade):** Alterações na "Taxa de Mão de Obra" e na "Validade de Orçamentos" do Painel Global **jamais** retroagem para orçamentos em andamento. O `data_validade` gerado é inviolável.
- **Renovação de Orçamento com Alerta de Inflação:** Ao renovar um orçamento expirado, o sistema recalcula a validade (pela nova regra global) e *alerta* o operador caso a mão de obra ou o custo dos materiais tenham encarecido no período (quebra do Snapshot original). A decisão final de atualizar os preços ou manter o valor antigo por cortesia pertence exclusivamente ao usuário.
- **Liquidação 100%:** Faturas (e seus orçamentos vinculados) só alcançam status "PAGO" via verificação sistemática na API que confirme que todas as sub-linhas de parcelas e pagamentos cobriram todo o total emitido original em dí­vida.
- **Respeito Comercial - Independência de Fatura:** O desconto fornecido em caráter extraordinário na hora da agregação do Faturamento é aplicado ao Tí­tulo Mestre da Fatura, e os Orçamentos fechados na etapa anterior continuam exibindo o valor unitário fiel da negociação no momento em que ocorreram. A cortesia, por sua vez, injeta liquidez invisí­vel sem espelhar no banco real.
- **Condição Visual de Impressão:** Todo desconto gerado na tela do orçamento atua sobre o resultado final e é bloqueado de aparecer impresso no espelho do PDF gerado para envio ao cliente, caso o desconto seja zero ou nulo (em branco).
- **Rollover de Pagamento Parcial de Cartão de Crédito:** O sistema garantirá que, caso a fatura de um Cartão Corporativo seja paga de forma apenas parcial (ou passe batida sem pagamento), o saldo devedor remanescente componha compulsoriamente a fatura do cartão no mês seguinte atuando como um lançamento de "Saldo Anterior", preservando o histórico da dívida e o fluxo real da Tesouraria.
- **Regra de Impacto Bancário por Transição de Status (`Lancamentos_Financeiros`):**
  1. *Títulos Pendentes (`status_pagamento = 'A Vencer'` ou `'Vencido'`):* Permanecem visíveis e filtráveis nas telas de Contas a Pagar e Contas a Receber para controle de vencimentos futuros e auditoria de inadimplência, **sem alterar o saldo bancário** da empresa até a efetivação da baixa.
  2. *Títulos Liquidados (`status_pagamento = 'Pago'`):* Ao realizar a baixa (manual, recebimento de fatura ou conciliação), o título transita compulsoriamente para o status **`Pago`** (permanecendo 100% visível nas listagens de Contas Pagas e Recebidas) e **debita ou credita imediatamente o saldo real da conta bancária vinculada** (`saldo = saldo ± valor`), independente do meio de pagamento utilizado (Pix, Dinheiro, Boleto liquidado, TED).
  3. *Despesas em Cartão Corporativo (`cartao_credito_id` preenchido):* Não debitam a conta bancária de imediato; somam no total da fatura aberta do cartão (`faturas_cartao_id`), debitando o saldo bancário apenas no momento do pagamento/liquidação da fatura do cartão.
  4. *Rastreabilidade de Conciliação:* O ato de conciliar grava compulsoriamente `is_conciliado = True`, `data_conciliacao = NOW()` e `conciliado_por_id = request.user.id` em cada lançamento.
- **Contrato da Rota de Liquidação e Baixa com Taxa de Maquininha:**
  - **Endpoint:** `POST /api/lancamentos-financeiros/{id}/liquidar/` (ou recebimento direto em `POST /api/faturas/{id}/receber/`)
  - **Request Payload:**
    ```json
    {
      "conta_id": 1,
      "meio_pagamento_id": 4,
      "data_pagamento": "2026-08-16T12:00:00Z",
      "valor_pago": 1000.00,
      "valor_liquido_recebido": 970.00
    }
    ```
  - **Lógica de Processamento do Backend:**
    1. O backend verifica se o `MeioPagamento.permite_taxa_maquininha == True`;
    2. Se `valor_liquido_recebido` for informado e menor que `valor_pago`, o sistema calcula automaticamente a taxa (`taxa = valor_pago - valor_liquido_recebido`);
    3. Registra a baixa do título de receita no valor bruto (`R$ 1.000,00`) com `status = 'Pago'` na `conta_id`;
    4. Cria automaticamente um lançamento financeiro de despesa no valor da taxa (`R$ 30,00`), com `tipo_lancamento = 'Saída'`, `categoria = 'Tarifas e Maquininhas'`, `status = 'Pago'` e vinculado à mesma `conta_id`;
    5. O saldo da conta bancária recebe o impacto líquido imediato (`+ R$ 970,00`), garantindo conciliação perfeita e DRE transparente sem duplicar despesas.
- **Validação Algorítmica de CPF e Unicidade Cadastral (Anti-Duplicação e UX Preventiva):**
  - **Hierarquia Visual e Validação Antecipada (`onBlur`):** O seletor `[PF / PJ]` e o campo `[CPF / CNPJ]` posicionam-se compulsoriamente no topo de todos os formulários e modais como o primeiro dado a ser inserido. A validação matemática e a checagem de duplicidade no banco são disparadas imediatamente na saída do campo (`onBlur`), alertando o operador na hora para evitar preenchimento inútil de outros campos caso o documento seja inválido ou já exista no sistema.
  - O sistema aplica a validação algorítmica matemática dos 2 dígitos verificadores (módulo 11) para qualquer CPF informado, rejeitando CPFs inválidos ou sequências repetidas fictícias (`111.111.111-11`), com feedback de borda em tempo real no frontend e validação estrita no backend (`serializers.ValidationError`).
  - O campo `cnpj_cpf` possui unicidade mandatória no MySQL quando informado (`unique=True, null=True`). Cadastros rápidos sem documento permanecem nulos sem conflito; no entanto, havendo digitação de CPF ou CNPJ existente, o salvamento é sumariamente barrado com alerta visual indicando o cadastro pré-existente.
- **Motor de Busca e Autocomplete de CNPJ (Integração Pública com Fallback Gracioso):**
  - **Rota Utilitária Backend:** `GET /api/utilitarios/consulta-cnpj/{cnpj}/`
  - O backend atua como proxy seguro consultando serviços públicos (BrasilAPI / ReceitaWS) e entregando JSON padronizado com: `razao_social`, `nome_fantasia`, `cep`, `logradouro`, `numero`, `bairro`, `cidade`, `uf`, `telefone` e `email`.
  - No frontend, o botão `[Buscar CNPJ]` ou a saída do campo CNPJ preenche automaticamente todo o formulário/modal em 1 segundo.
  - *Resiliência e Fallback:* Caso a API externa esteja fora do ar ou o CNPJ não seja localizado, o sistema exibe toast informativo amigável (*"Consulta pública indisponível. Preencha os dados manualmente"*) e permite a digitação livre sem travar o operador.

## 15. Autenticação e Segurança de Sessão (Login)

- **Arquitetura Base:** A autenticação na V1 será via e-mail e senha usando JSON Web Token (JWT). Contudo, a estrutura do banco de dados será projetada para o futuro (V2), aceitando senhas nulas apenas a ní­vel de tabelas fí­sicas para comportar provedores externos e incluindo colunas preparatórias como `auth_provider` e `is_2fa_enabled`. O backend garantirá uma trava lógica absoluta: é proibido salvar usuários sem senha quando o provedor for "LOCAL".
- **Onboarding e Recuperação:** 
  - Não há auto-cadastro. O Administrador cadastra apenas nome e e-mail. O usuário recebe um e-mail com link único para configurar sua própria senha, garantindo que o gestor nunca conheça a credencial da equipe.
  - O fluxo de "Esqueci minha senha" enviará um código alfanumérico de 8 dígitos ao e-mail com validade estrita de 30 minutos.
  - O disparo de e-mails utiliza o serviço dinâmico de SMTP configurado pelo Administrador na Central do Admin. Durante o desenvolvimento e testes locais (ou se o SMTP não estiver configurado), o sistema utiliza automaticamente o `console.EmailBackend` do Django como fallback seguro para não travar o fluxo operacional.
- **Mecânica de Soft Lock e Destravamento Ágil por PIN (6 Dígitos):**
  - Quando a aplicação detecta inatividade local do usuário (tempo padrão de 30 minutos, parametrizável em `Configuracoes_Globais.tempo_ociosidade_minutos`), a interface entra no estado `is_soft_locked = true`, escurece a tela e renderiza o modal de **Soft Lock** com input de 6 dígitos numéricos.
  - **Endpoint de Destravamento:** `POST /api/auth/unlock-pin/`
    - *Request Header:* Requer Cookie HttpOnly com sessão/token ativo.
    - *Request Payload:* `{ "pin": "123456" }`
    - *Resposta de Sucesso (200 OK):* `{ "status": "success", "message": "Sessão destravada com sucesso." }`. O frontend fecha o modal e restaura o acesso às telas imediatamente.
    - *Resposta de Falha (400 Bad Request):* `{ "status": "error", "message": "PIN incorreto. Tentativa X de 3." }`.
  - **Mecânica de Hard Lock:** Se o usuário errar o PIN por **3 vezes consecutivas**, o backend invalida o Refresh Token, limpa o Cookie HttpOnly e retorna `401 Unauthorized` (`{ "status": "hard_lock", "message": "Tentativas excedidas. Faça login novamente." }`), forçando o redirecionamento imediato para a tela de Login tradicional com e-mail e senha.
  - **Cadastro e Alteração do PIN:** `POST /api/auth/set-pin/` (Payload: `{ "pin": "123456", "pin_confirmacao": "123456" }`). O usuário define seu PIN de 6 dígitos no primeiro acesso ou no menu "Meu Perfil / Segurança". O valor é persistido com hash criptográfico PBKDF2/Argon2 em `Usuarios.pin_hash`.
- **Proteção Anti-Brute-Force (Rate Limiting) e Desbloqueio pelo Admin:** 
  - A API blinda tentativas de invasão e robôs no login principal. Se um IP ou e-mail registrar 5 tentativas falhas de login (senha incorreta) no intervalo de 15 minutos, a conta é bloqueada temporariamente por 1 hora (`bloqueado_ate = NOW() + 1 hora` e `tentativas_login_falhas = 5`), rejeitando novas tentativas com código `429 Too Many Requests`.
  - **Endpoint de Desbloqueio pelo Administrador:** `POST /api/usuarios/{id}/desbloquear/`. Exclusivo para usuários com permissão administrativa (`role = Admin` ou toggle `gestao_equipe = True`). Zera `tentativas_login_falhas = 0` e limpa `bloqueado_ate = NULL`, reabilitando o login do operador imediatamente.
- A configuração global (ditada pelo gestor) determina o tempo de expiração (`exp`) do JWT emitido nas novas sessões.

## 16. Controle de Acesso

- As validações de autorização (Controle RBAC) atuam obrigatoriamente tanto na filtragem das interfaces do PWA visualmente quanto nas rotas do Backend, de forma impenetrável.
- **Gestão Dinâmica de Permissões (10 Módulos):** O sistema terá uma interface onde o Administrador pode ligar/desligar permissões operacionais e administrativas específicas em tempo real para cada usuário nos 10 módulos do sistema.
- Usuários cadastrados com o perfil **Administrador** possuem todos os 10 módulos liberados por padrão e têm direitos plenos de governança.
- Usuários cadastrados com o perfil **Operador** iniciam com os módulos operacionais ativados por padrão e módulos estruturais desativados, mas o Administrador pode personalizar granularmente qualquer um dos 10 toggles para cada colaborador.
- Operadores que tentarem acessar rotas sem autorização recebem erro "Proibido" (403/Forbidden) emitido diretamente pelo backend.

**Matriz de Permissões Configurável e Níveis de Acesso Padrão:**

| Módulo / Funcionalidade | Administrador (Padrão) | Operador (Padrão Inicial) | Tipo de Toggle na UI |
| :--- | :--- | :--- | :--- |
| **1. Orçamentos, Faturas e Clientes** | Acesso Total | **Acesso Total** (restaura exclusões próprias) | *Dinâmico (ON/OFF)* |
| **2. Tesouraria (Caixa, Conciliação, Estornos)** | Acesso Total | **Acesso Total** | *Dinâmico (ON/OFF)* |
| **3. Compras (Entrada de Notas e Fornecedores)** | Acesso Total | **Acesso Total** | *Dinâmico (ON/OFF)* |
| **4. Catálogo Base (Itens, Produtos e Preços)**| Acesso Total | **Acesso Total** | *Dinâmico (ON/OFF)* |
| **5. Relatórios, Dashboards e DRE** | Acesso Total | **Acesso de Leitura** | *Dinâmico (ON/OFF)* |
| **6. Cadastros Financeiros (Contas e Regras)** | Acesso Total | **Acesso Negado** (Usa em dropdowns, mas não edita) | *Dinâmico (ON/OFF)* |
| **7. Dicionário Central (UOM e Atributos)** | Acesso Total | **Acesso Negado** (Apenas usa unidades cadastradas) | *Dinâmico (ON/OFF)* |
| **8. Configurações Globais e Parâmetros** | Acesso Total | **Acesso Negado** | *Dinâmico (ON/OFF)* |
| **9. Gestão de Equipe, Permissões e Senhas** | Acesso Total | **Acesso Negado** (Apenas altera a própria senha) | *Dinâmico (ON/OFF)* |
| **10. Auditoria, Logs e Lixeira Global** | Acesso Total | **Acesso Negado** (Acesso restrito à Minha Lixeira) | *Dinâmico (ON/OFF)* |

**Os 10 Toggles de Permissões Dinâmicas (Interface do Administrador):**
No painel Administrativo (e na tabela `Permissoes` do banco de dados), a gestão de acesso opera com 10 interruptores por usuário:
- `[ ON/OFF ]` **`acesso_comercial`:** Gerenciar Orçamentos, Faturas e cadastrar Clientes e Veículos.
- `[ ON/OFF ]` **`acesso_tesouraria`:** Dar baixa em recebimentos, executar conciliação bancária split-screen e justificar estornos.
- `[ ON/OFF ]` **`acesso_compras`:** Cadastrar Fornecedores, registrar Notas Fiscais de Entrada e alimentar histórico de custos.
- `[ ON/OFF ]` **`gestao_catalogo`:** Criar novas receitas de produtos (BOM) e adicionar materiais e itens operacionais.
- `[ ON/OFF ]` **`visao_relatorios`:** Acesso de leitura a Curvas ABC, Painel de Inadimplência e DRE Simplificado.
- `[ ON/OFF ]` **`cadastros_financeiros`:** Criar e parametrizar Contas Bancárias, Regras de Pagamento e Categorias Financeiras.
- `[ ON/OFF ]` **`gestao_dicionario_uom`:** Gerenciar o catálogo mestre de Unidades de Medida (UOM) e Atributos Descritivos.
- `[ ON/OFF ]` **`configuracoes_globais`:** Configurar dados da empresa, taxa de mão de obra hora, validade de orçamentos e SMTP.
- `[ ON/OFF ]` **`gestao_equipe`:** Convidar novos colaboradores (Admins/Operadores), ajustar os 10 toggles e desbloquear contas travadas por brute-force.
- `[ ON/OFF ]` **`auditoria_logs_recovery`:** Visualizar Log Viewer do servidor, auditar manifesto de expurgo e acessar a Lixeira Global para restaurar registros de qualquer usuário.

## 17. Auditoria e Histórico

- O núcleo gravador da plataforma carimbará o ID do usuário da sessão acompanhando as ações com Data/Hora em instantes da execução principal de tabelas.
- O histórico garantirá uma clareza em visualizações pontuais, informando nas fichas (e acessí­vel pela gestão) "quem criou/inativou" transações polêmicas (Faturas com erros, canceladas, orçamentos antigos, e transições).
- **Log Estruturado de Cancelamentos e Estornos:** Toda anulação de Orçamento, Fatura ou Título Financeiro gera compulsoriamente um registro no log do servidor com formato estruturado: `[AUDIT] [CANCELAMENTO] Usuário: email (ID) | Entidade: Nome #ID | Motivo: "..." | Data/Hora | IP`.
- Lançamentos não conciliados com o banco na Tesouraria formarão um log vivo (Relatório de Divergências) permitindo rastreio a quem cometeu fraude ou errou valores ao não conciliar o extrato manual de forma correta.

## 18. Soft Delete e Exclusões

- **Proibição Absoluta de Hard Delete:** A deleção física permanente de registros está totalmente desabilitada e proibida na V1. Nenhuma rota de API ou tela do sistema executa comandos `DELETE` diretos nas tabelas de negócio do MySQL, garantindo a preservação eterna das cascatas de dados, integridade de Fichas Técnicas BOM e trilhas de auditoria.
- **Mecânica de Exclusão Lógica:** Toda exclusão aplica compulsoriamente os carimbos de autoria (`deleted_at = NOW()` e `deleted_by_id = request.user.id`), ocultando o registro das listagens ativas e enviando-o para o Painel de Lixeira.
- **Regra de Restauração do Operador (Minha Lixeira):** O Operador tem acesso restrito para restaurar unicamente aqueles registros que foram criados e inativados pelo seu próprio login (`deleted_by_id = request.user.id`).
- **Regra de Governança do Administrador (Lixeira Global):** O Administrador possui visão panorâmica para auditar e restaurar qualquer registro inativado por qualquer colaborador no sistema.
- **Preservação Histórica Financeira:** Ao inativar cadastros estruturais (como Contas Bancárias ou Categorias), a regra de ocultação se aplica apenas a novos cadastros; relatórios e extratos passados continuam exibindo os nomes históricos normalmente sem quebra visual.

## 19. Logs

### Rotação Diária e Arquitetura de Arquivos Físicos

Os logs do sistema são organizados em **arquivos físicos diários e rotativos** (ex: `logs/app-YYYY-MM-DD.log`), desacoplados da base MySQL para não onerar o banco de dados. Os nomes dos arquivos são imutáveis e baseados estritamente na data de criação. Toda a matemática de expurgo é gerenciada centralizadamente pela tabela de manifesto `Controle_Arquivos_Log.data_expurgo_planejada`, **sem necessidade de renomear arquivos no disco** caso o Administrador altere a política de retenção global.

### Log de erros

Os logs de falhas graves originárias no servidor backend não podem corromper e poluir a base MySQL.
Erros provenientes do sistema interno (ex: falhas de processamento, exceções, e indisponibilidade do banco de dados) atuarão sempre em formato de **arquivo fí­sico de log** armazenado no servidor backend (dentro do `[Diretório do Projeto - Repositório]`, longe de acesso direto e pastas públicas).

Essa contingência confere estabilidade garantida: mesmo se o banco parar de interagir, o log fí­sico salva o erro em arquivo texto, permitindo auditoria pontual pelo Administrador que determina seu perí­odo de retenção programado. O usuário verá mensagens de erro seguras pela interface PWA.

### Log de segurança e auditoria

Os logs associados ao risco à infraestrutura registrarão todos os episódios de tentativa de fraude local e manipulação intencional: IPs anômalos em múltiplas falhas de login da conta dos Operadores, quebras contrárias nas áreas de autorizações, ações suspeitas, cancelamentos/estornos justificados e suspensão em bloqueios restritivos de sessão.

## 20. Configurações Globais

- A interface apresentará ao Gestor campos de personalização universal da ferramenta (parâmetros de duração da sessão, validade de orçamento, expurgo de logs e configuração do serviço SMTP de e-mails com armazenamento criptografado de senha) que aplicam fallback padronizado caso os campos sofram reset forçado.
- Estratégia de Configuração Técnica Protegida e Blindagem de Segredos: Variáveis centrais e sensí­veis (dados de conexão com o banco de dados, chaves-mestras de criptografia `SECRET_KEY` e `ENCRYPTION_KEY`) serão lidas de forma desacoplada através do módulo `os.environ` no arquivo `config/settings.py`. O sistema não exporá arquivos de senhas em pastas públicas. Em ambiente local, haverá chaves padrão de fallback para agilidade nos testes; em produção na nuvem, essas chaves serão alimentadas exclusivamente pelo painel de variáveis de ambiente da hospedagem PaaS (injetadas diretamente na memória RAM do processo Python).
- O backend fica estritamente isolado em pasta interna dentro do `[Diretório do Projeto - Repositório]`. O servidor WSGI/ASGI e as rotas da aplicação garantem que apenas a API REST e os arquivos estáticos do PWA sejam servidos, sendo impossível o acesso web direto a arquivos `.py` ou configurações do servidor.

## 21. Uploads, Anexos e Arquivos

- O upload suportará XML ou PDF quando o assunto for documentos fiscais de faturas ou aquisição de notas de itens de fornecedor.
- O sistema exigirá o processamento e upload momentâneo de arquivos gerados pelo caixa financeiro da oficina via formato de extrato CSV ou OFX para cruzamento e matching (Conciliação Bancária).
- Estes arquivos de leitura seguirão o limitador local de tamanho. Os arquivos armazenados logicamente devem ter seu Mime Type real validado, assegurando a não inserção oculta de scripts renomeados como PDF. A proteção de acesso contra URL indevida será feita validando os downloads pela própria API.

## 22. Relatórios, Consultas e Exportações

- O sistema gerará relatórios tanto em formato PDF (documentos formais de envio) quanto em CSV (planilhas de conferência gerencial).
- **PDFs Transacionais:** Geração de Orçamentos Individuais, Espelho de Orçamentos Agrupados (detalhados com sumário) e Faturas Finais.
- **Relatórios Gerenciais (Tela/CSV/PDF):** 
  - Painel de Inadimplência (auditoria de faturas vencidas x falta de baixa manual).
  - Dossiê do Cliente (histórico de funil de orçamentos e separação do que foi material vs reforma).
  - Curva ABC de Clientes e Curva ABC de Itens (consumo).
  - DRE Simplificado (agrupando por Categoria Financeira).
- Os modelos de dados exigirão a criação de **Índices** no banco para evitar lentidão, priorizando os filtros de datas e de `status` utilizados ativamente nas listagens de painel de conta corrente e relatórios financeiros.

## 23. APIs e Integrações Externas

- **Integração Externa com API Pública de Consulta de CNPJ (BrasilAPI / ReceitaWS):**
  - O sistema integra-se com serviços públicos abertos (BrasilAPI com fallback para ReceitaWS) através da rota proxy interna do backend `GET /api/utilitarios/consulta-cnpj/{cnpj}/`. O objetivo exclusivo desta integração é acelerar o cadastramento de clientes e fornecedores via autopreenchimento de dados cadastrais (Razão Social, Nome Fantasia, Endereço e Contato).
  - *Resiliência e Fallback Gracioso:* Se o serviço externo estiver fora do ar ou sofrer lentidão, o sistema libera a digitação manual normal sem travar as rotinas do usuário.
- **Isolamento de Outras Integrações Externas na V1 (Fora de Escopo):**
  - A plataforma não possui integração automatizada de Open Finance bancário (a conciliação ocorre via importação de arquivos OFX/CSV), nem integração direta com Web Services de autorização de NF-e da SEFAZ (o faturamento ocorre via emissão externa e anexo de PDF/XML no ERP) ou gateways de emissão de boletos.
- **Consumo de APIs do Ecossistema Interno:**
  - Excetuando a rota proxy de consulta de CNPJ, o consumo de APIs existirá unicamente dentro do ecossistema interno, onde o frontend PWA consumirá a API REST provida pelo próprio backend Django do projeto.

## 24. Segurança Funcional

- Proteção das rotas API validando os tokens (ex: JWT) e autorizações por perfil diretamente no backend, impedindo elevação de privilégio.
- Validação de Mime Type para bloqueio de uploads perigosos.
- Cuidado com mensagens de erro, garantindo que o Traceback original não "vaze" nas respostas em JSON do frontend. Erros crí­ticos irão apenas para a contingência do log de erros.
- Proteção de exportações seguindo as mesmas restrições de permissão e filtros da tela.
- **Criptografia Simétrica de Credenciais (AES-256 / Fernet):** A senha do serviço SMTP configurada na interface administrativa é gravada no banco de dados obrigatoriamente criptografada via AES-256 (utilizando a chave-mestra `ENCRYPTION_KEY` lida da memória do servidor via `os.environ`). A API nunca devolve a senha real nas respostas JSON do frontend, exibindo apenas o status mascarado na UI.

## 25. Organização Sugerida da Implementação

A codificação em etapas lógicas deverá ser seguida pela IA focando em validação ambiente local:

1. Preparação da raiz da aplicação baseada no `[Diretório do Projeto - Repositório]`.
2. Criação da estrutura inicial de pastas desacoplada (backend Django e frontend/PWA).
3. Configuração inicial do ambiente virtual Python e instalação de dependências.
4. Criação do arquivo de configuração em código Python (ex: `config/settings.py`), sem uso de `.env`.
5. Isolamento do backend e configuração das rotas públicas exclusivas para a API e PWA.
6. Definição da estrutura arquitetural base no backend (modelos, serviços, rotas).
7. Configuração da conexão com o banco de dados.
8. Criação da estrutura de migrations via ORM.
9. Criação das migrations iniciais de tabelas, campos, í­ndices, constraints, auditoria e soft delete.
10. Definição do mecanismo de controle e execução segura de migrations (linha de comando).
11. Autenticação e segurança da API (emissão e validação de tokens, serviço de onboarding e recuperação de senhas com fallback de envio para `console.EmailBackend` e integração dinâmica ao modelo de SMTP criptografado).
12. Controle de acesso e permissões (RBAC).
13. Desenvolvimento dos endpoints dos Cadastros Básicos (Clientes, Dicionário, Itens).
14. Desenvolvimento da lógica de Orçamentos, Snapshots e Faturamento Agregado.
15. Estruturação do Frontend client-side (PWA, Service Workers, cache offline Vanilla JS).
16. Integração dos fluxos funcionais entre Frontend e API REST.
17. Relatórios, conciliação e consultas (backend gerando dados higienizados, frontend exibindo).
18. Uploads de PDF/XML/CSV/OFX.
19. Exportações em CSV e PDF.
20. Configuração de logs de erros e segurança (com contingência em arquivo).
21. Revisão de segurança e performance da API (í­ndices confirmados).
22. Revisão de qualidade do código e testes locais.
23. Preparação da entrega e deploy para ambiente Cloud (PaaS) com Assistência Interativa da IA: A IA codificadora fornecerá um script gerador de chaves aleatórias seguras de 64 caracteres para `SECRET_KEY` e `ENCRYPTION_KEY` e apresentará um guia passo a passo ao usuário ensinando como cadastrar essas variáveis no painel da plataforma de nuvem escolhida (Render, PythonAnywhere, etc.), garantindo um deploy 100% assistido e seguro.

## 26. Plano de Testes, Validação Contínua com o Usuário e Bateria de Segurança (Pentest)

### 1. Protocolo de Desenvolvimento Iterativo e Checkpoints com o Usuário
A IA codificadora não executará o projeto em formato de "caixa preta". A cada término de bloco funcional da Seção 25, a IA deve compulsoriamente:
1. Executar seus testes automatizados locais de backend e frontend;
2. Subir o servidor local de desenvolvimento e fornecer a URL de acesso;
3. **Apresentar um Roteiro de Teste Interativo para o Usuário**, contendo:
   - Credenciais de teste preparadas (ex: Admin e Operador);
   - Passo a passo de cliques e fluxos para testar a funcionalidade na prática;
   - Checklist de validação visual de layout (Desktop e Mobile) conforme `docs/DESIGN.md`;
4. **Pausar e solicitar a aprovação formal do usuário** antes de iniciar a codificação do bloco seguinte.

### 2. Bateria de Testes Automatizados da IA (Backend & Lógica)
- **Testes Unitários de Models e Constraints:** Unicidade de CPF/CNPJ (`unique=True, null=True`), regras de integridade BOM (Ficha Técnica), soft delete e imutabilidade de snapshots de custo/venda;
- **Testes de Integração de Endpoints REST:** Cobertura de status codes (200, 201, 400, 403, 404), validação estrita de payloads JSON e autorização JWT;
- **Testes de Máquinas de Estados e Cascatas Financeiras:** Ciclo de vida completo: Orçamentos ➔ Pré-Fatura ➔ Fatura Final ➔ Baixa com Taxa de Maquininha ➔ Quitação 100% ➔ Cancelamentos/Estornos com justificativa.

### 3. Checklist de Validação de Layout, UX e Responsividade pelo Usuário
- **Identidade Visual *Industrial Integrity*:** Aderência a tokens HSL, cantos retos (0px border-radius), tipografia técnica (IBM Plex Sans / Inter / JetBrains Mono) e ausência de clichês visuais;
- **Responsividade Multi-Dispositivo:** Comportamento fluido em Desktop (Grid 12 colunas com Sidebar retrátil e Resumo Lateral Fixo) e Mobile (Grid 4 colunas com cards empilhados, Split-Screen adaptada e Bottom Sheet);
- **Ergonomia Operacional:** Teste dos Flip Cards do Dashboard, filtros inline em tempo real, modais rápidos (cadastro ágil de cliente com busca de CNPJ) e seletores de proposta de pagamento em 1 clique.

### 4. Bateria de Testes de Segurança e Teste de Invasão (Pentest de Conclusão)
Ao finalizar a codificação da V1, a IA codificadora executará uma bateria mandatória de testes de invasão e *hardening*:

1. **Teste 1 - Controle de Acesso e Quebra de Permissões (IDOR / BOLA / RBAC):**
   - Simular requisições via API com token de Operador sem privilégios tentando acessar ou modificar rotas exclusivas do Admin (ex: `/api/usuarios/`, `/api/logs/`, `/api/configuracoes-globais/`). O sistema deve retornar compulsoriamente `403 Forbidden`.
2. **Teste 2 - Anti-Brute Force e Rate Limiting:**
   - Disparar 6 tentativas consecutivas de login com senha incorreta e verificar se a conta/IP é sumariamente bloqueada por 15 minutos com status `429 Too Many Requests`;
   - Disparar requisições em rajada nos endpoints de relatórios e exportações para validar o estrangulamento preventivo do `ScopedRateThrottle ('heavy_reports')`.
3. **Teste 3 - Injeção SQL (SQLi) e Cross-Site Scripting (XSS):**
   - Injetar payloads maliciosos (`' OR '1'='1`, `<script>alert('XSS')</script>`, etc.) em campos de busca textual, autocompletes, justificativas de estorno/cancelamento e descrições livres, garantindo a sanitização e escape nativo do Django ORM e frontend Vanilla JS.
4. **Teste 4 - Segurança de Uploads e Bypass de Extensão:**
   - Tentar fazer upload de scripts executáveis (.php, .exe, .sh, .py, .js) renomeados com extensão `.pdf`, `.xml` ou `.ofx`, verificando se a validação de *Mime Type real* e cabeçalho de bytes barra o arquivo com erro seguro.
5. **Teste 5 - Sessão, Soft Lock e Cookie HttpOnly:**
   - Verificar se o Token JWT armazenado em Cookie HttpOnly está inacessível via `document.cookie` no console do navegador (impossibilitando roubo de sessão por XSS);
   - Validar se requisições após 30 minutos de ociosidade são bloqueadas pelo Soft Lock até a digitação correta do PIN de 6 dígitos.
6. **Teste 6 - Criptografia de Segredos e Não-Vazamento de Tracebacks:**
   - Verificar no banco MySQL se a senha do SMTP está indecifrável (criptografada via AES-256/Fernet);
   - Forçar erros 500 no backend e certificar-se de que a API retorna apenas JSONs amigáveis sem expor o Traceback do Python, gravando os detalhes técnicos exclusivamente no arquivo físico `.log` do servidor.

## 27. Critérios de Aceitação Técnica e Funcional

O FSD atingirá as premissas propostas quando:
- Todas as funcionalidades principais e fluxos de Orçamento estiverem definidos para implementação.
- A arquitetura definida (Backend API REST em Python + Frontend PWA client-side) for plenamente respeitada, separando interface e regras de negócios.
- Permissões de RBAC fechadas e validadas primariamente no Backend.
- Soft delete, auditoria e restrições modeladas e asseguradas.
- O banco contém os í­ndices criados para consultas crí­ticas e filtros de status/data.
- Logs funcionando, e log de contingência em arquivo de texto funcional ativado para cobrir indisponibilidade de banco.
- Telas baseadas estritamente na experiência exigida do `docs/DESIGN.md`.
- Erros tratados visualmente e sem exposição indevida do Traceback.
- Estrutura baseada puramente em `[Diretório do Projeto - Repositório]`, rejeitando dependências a pastas `public_html`, `public`, `htdocs` ou `www`.
- Arquivo de configuração em código nativo criado e protegido (ex: `config/settings.py`), com leitura de variáveis sensíveis via `os.environ` e sem exposição de segredos no repositório. Pastas internas protegidas contra acesso web por URL direta.
- Migrations criadas para a estrutura do banco contemplando tudo que for necessário. O mecanismo de execução das migrations não é acessí­vel diretamente via navegador e não roda de forma duplicada.

## 28. Pontos Pendentes e Decisões Futuras

Não foram identificadas pendências para iniciar a codificação com base neste FSD. Todas as restrições arquitetônicas e comerciais já se encontram consolidadas nesta estrutura.

## 29. Conclusão

O FSD está consolidado, completo e pronto para orientar de forma autossuficiente uma IA codificadora.

Os seguintes documentos deverão ser entregues para a IA codificadora, juntamente com o desenvolvimento baseado neste projeto:
- `docs/FSD.md`
- `docs/DESIGN.md`