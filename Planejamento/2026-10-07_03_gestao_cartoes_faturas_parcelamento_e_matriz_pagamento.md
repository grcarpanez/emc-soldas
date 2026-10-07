# Implementation Plan - Gestão Completa de Cartões de Crédito Corporativos, Faturas, Parcelamento em N Vezes e Matriz de Pagamentos Multi-Meio

- **Data:** 2026-10-07
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Concluído
- **Registro do Proceed:** Aprovado explicitamente pelo usuário em 2026-10-07 16:16:04 via "Proceed".
- **Arquivo de Registro:** `Planejamento/2026-10-07_03_gestao_cartoes_faturas_parcelamento_e_matriz_pagamento.md`

---

## 1. Contexto e Motivação

### 1.1 Diagnóstico Apresentado pelo Usuário
1. **Ausência de Interface e Ciclo de Vida Visual de Cartões Corporativos:**
   - Embora as entidades `CartaoCredito` e `FaturaCartao` existam no banco de dados MySQL, não há uma tela de gestão visual dedicada na Tesouraria (`#/tesouraria`).
   - É necessário acompanhar os limites de crédito, as faturas abertas, fechadas e pagas de cada cartão da empresa.
2. **Ciclo Completo de Faturas e Recálculo Automático de Fechamento:**
   - As faturas de cartão precisam de rotinas claras de transição de status (`ABERTA` ➔ `FECHADA` ➔ `PAGA`).
   - Ao alterar as datas de fechamento ou vencimento de uma fatura, o sistema deve recalcular e redistribuir automaticamente as compras vinculadas (compras feitas após o novo corte são migradas para a fatura seguinte; compras que ficaram dentro do corte são puxadas para a fatura corrente).
   - Liquidação flexível de faturas: pagamento total (quitando todas as compras contidas) ou pagamento parcial com crédito rotativo (*rollover* do saldo restante para a fatura do mês seguinte).
3. **Gestão de Compras Parceladas em N Faturas ($N \ge 2$):**
   - Compras feitas com cartão corporativo podem ser à vista (1x) ou parceladas em $N$ vezes.
   - O sistema deve criar/obter as $N$ faturas futuras consecutivas, gerar os lançamentos correspondentes (com identificação de parcela ex: `1/3`, `2/3`, `3/3`) e comprometer o limite total do cartão, recompondo o limite gradualmente conforme cada fatura mensal for paga.
4. **Matriz de Pagamento Multi-Meio ("Caixa de Mercado" / Split Payment):**
   - Uma mesma compra/despesa pode ser paga com múltiplos instrumentos financeiros (ex: parte em Dinheiro no Caixa Físico, parte no PIX da Conta Bancária Principal e parte parcelada no Cartão Corporativo).
   - O sistema deve aceitar uma matriz de pagamento que totalize o valor da compra, gerando os lançamentos específicos de cada meio/conta com rastreabilidade mestre unificada (`grupo_pagamento_id`), garantindo exatidão contábil e de saldo real.
5. **Anexo Único com Reutilização na Conciliação Bancária:**
   - Comprovantes ou NFs anexados no momento do lançamento da compra/despesa devem ser vinculados diretamente a todos os lançamentos gerados.
   - Quando o extrato bancário (OFX/CSV) for importado na conciliação, o match automático com a linha do ERP herdará o anexo sem exigir novo upload.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Modelagem de Dados (`backend/apps/financeiro/models.py`)
1. **Campos Auxiliares em `LancamentoFinanceiro`:**
   - `grupo_pagamento_id = models.UUIDField(null=True, blank=True, db_index=True)`: Chave de correlação para despesas pagas com matriz multi-meio.
   - `numero_parcela = models.IntegerField(default=1)`: Identificador ordinal da parcela (ex: 1).
   - `total_parcelas = models.IntegerField(default=1)`: Quantidade total de parcelas da transação (ex: 3).
2. **Geração e Aplicação de Migração Django:**
   - Criação da migração `financeiro.0006_lancamentofinanceiro_grupo_pagamento_id_and_more.py`.

### 2.2 Serviços de Negócio (`backend/apps/financeiro/services_cartao.py` e `services.py`)
1. **Parcelamento em N Vezes (`lancar_despesa_cartao`):**
   - Validação de limite global: se $N \times \text{parcela}$ ultrapassar o limite disponível (e sem limite emergencial), bloqueia a operação.
   - Divisão exata com tratamento de centavos: $\text{resto} = \text{valor\_total} - (\text{parcela\_base} \times N)$, alocando o centavo excedente na 1ª parcela.
   - Criação/obtenção das $N$ faturas consecutivas no cartão.
   - Criação dos $N$ lançamentos com `numero_parcela=i`, `total_parcelas=N` e vínculo com a fatura correspondente.
2. **Recálculo Automático por Mudança de Fechamento (`ajustar_fechamento_fatura`):**
   - Ao alterar `data_fechamento_real` da fatura $F$:
     - Se o fechamento for antecipado: despesas com data superior à nova data de corte são remanejadas para a fatura subsequente $F+1$.
     - Se o fechamento for adiado: despesas da fatura $F+1$ com data anterior ou igual à nova data de corte são puxadas de volta para $F$.
     - Bloqueio de segurança: se a fatura subsequente já estiver `FECHADA` ou `PAGA`, a migração de compras é impedida.
     - Recálculo sincronizado de `data_vencimento` de todos os lançamentos abertos da fatura.
3. **Liquidação e Fechamento de Faturas:**
   - Fechamento (`fechar_fatura_cartao`): consolida compras, calcula vencimento e gera/atualiza o título no Contas a Pagar.
   - Liquidação (`liquidar_fatura_cartao`): debita a conta bancária escolhida, quita a fatura e, em caso de pagamento parcial, transfere o saldo residual para a próxima fatura como despesa de *rollover*.
4. **Matriz de Pagamentos Multi-Meio (`registrar_compra_multi_meio`):**
   - Transação atômica (`@transaction.atomic`).
   - Valida que $\sum \text{valores da matriz} == \text{valor total da compra}$.
   - Gera um `UUID` único para `grupo_pagamento_id`.
   - Processa cada linha:
     - Linhas à vista (Dinheiro, PIX, Débito): geram lançamento com `status_pagamento='PAGO'` debitando a conta imediatamente.
     - Linhas a prazo/boleto: geram lançamento com `status_pagamento='A_VENCER'`.
     - Linhas no Cartão: acionam `lancar_despesa_cartao` com o número de parcelas especificado.
   - Replica o arquivo de comprovante para todos os lançamentos criados.

### 2.3 Endpoints e Serializers (`backend/apps/financeiro/views.py` e `serializers.py`)
1. **`CartaoCreditoViewSet`:**
   - Action `@action(detail=True, methods=['get'], url_path='resumo-limite')`: retorna limite total, comprometido e disponível.
   - Action `@action(detail=True, methods=['get'], url_path='faturas')`: retorna a linha do tempo de faturas do cartão com totais.
2. **`FaturaCartaoViewSet`:**
   - Action `@action(detail=True, methods=['get'], url_path='itens')`: lista compras detalhadas da fatura com parcelas e comprovantes.
   - Action `@action(detail=True, methods=['post'], url_path='ajustar-fechamento')`: ajusta data e dispara redistribuição automática.
   - Action `@action(detail=True, methods=['post'], url_path='fechar')`: consolida e fecha fatura.
   - Action `@action(detail=True, methods=['post'], url_path='liquidar')`: efetua pagamento total ou parcial com rollover.
3. **`LancamentoFinanceiroViewSet`:**
   - Action `@action(detail=False, methods=['post'], url_path='lancar-multi-meio')`: processa a matriz de pagamento.

### 2.4 Interface PWA (*Industrial Integrity* em `frontend/assets/js/views/financeiro-view.js` e CSS)
1. **Aba "CARTÕES CORPORATIVOS" na Tesouraria:**
   - **Flip/KPI Cards:** Limite Total, Comprometido, Disponível e Faturas em Aberto.
   - **Barra de Ferramentas:** Botão `+ NOVO CARTÃO CORPORATIVO`, seletor pesquisável de cartão ativo.
   - **Card da Fatura do Cartão:**
     - Barra de navegação cronológica de faturas (anteriores, atual `[ABERTA]`, futuras `[PARCELADAS]`).
     - Badges com status da fatura, total acumulado, limite disponível e datas de fechamento e vencimento.
     - Botões de ação contextuais: `[AJUSTAR FECHAMENTO]`, `[FECHAR FATURA]`, `[PAGAR FATURA]`.
     - Tabela densa de compras da fatura: Data, Descrição, Categoria DRE, Parcela (ex: `1/3`), Valor, Comprovante e Ação `[REMANEJAR]`.
2. **Modais Especializados de Cartão:**
   - Modal de Cadastro/Edição de Cartão de Crédito.
   - Modal de Ajuste de Fechamento com preview de redistribuição de itens.
   - Modal de Liquidação de Fatura com seleção de conta bancária e suporte a pagamento parcial.
3. **Matriz de Pagamentos Multi-Meio no Modal de Despesa:**
   - Switch / Aba: `[FORMA ÚNICA]` vs `[MÚLTIPLAS FORMAS (MATRIZ)]`.
   - Grid dinâmico com botão `+ ADICIONAR FORMA DE PAGAMENTO`:
     - Colunas: Meio de Pagamento, Conta/Cartão, Parcelas (1x a 24x se cartão), Valor.
   - Contador reativo de conferência:
     - `Valor Total: R$ X,XX | Soma das Formas: R$ Y,YY | Diferença: R$ Z,ZZ (Alerta verde/vermelho)`.
     - Cálculo automático de Troco caso pagamento em dinheiro seja superior.
   - Upload de Comprovante único propagado para todas as linhas da matriz.
4. **Conciliação Bancária com Reuso de Anexo:**
   - No `conciliacao-view.js`, os cards da mesa de triagem que derem match com lançamentos do ERP herdam visualmente o comprovante pré-existente (`[📎 NF_123.pdf]`), sem exigir upload redundante.

---

## 3. Arquivos a Modificar / Criar

| Arquivo | Ação | Descrição |
| :--- | :---: | :--- |
| `backend/apps/financeiro/models.py` | Modificar | Adicionar `grupo_pagamento_id`, `numero_parcela` e `total_parcelas` em `LancamentoFinanceiro`. |
| `backend/apps/financeiro/migrations/0006_...py` | Criar | Migração Django gerada para os novos campos. |
| `backend/apps/financeiro/services_cartao.py` | Modificar | Implementar parcelamento em $N$ faturas, recálculo por corte de fechamento e liquidação. |
| `backend/apps/financeiro/services.py` | Modificar | Implementar o serviço de registro de compra multi-meio (`registrar_compra_multi_meio`). |
| `backend/apps/financeiro/serializers.py` | Modificar | Serializers para matriz multi-meio, itens de fatura e campos computados de cartão. |
| `backend/apps/financeiro/views.py` | Modificar | Actions REST para cartões, faturas, itens, ajuste de fechamento e lançamento multi-meio. |
| `backend/apps/financeiro/tests.py` | Modificar | Testes automatizados unitários para parcelamento, recálculo, liquidação e matriz multi-meio. |
| `frontend/assets/js/views/financeiro-view.js` | Modificar | Implementar aba Cartões Corporativos, faturas, modais e componente de matriz de pagamento. |
| `frontend/assets/js/views/conciliacao-view.js` | Modificar | Herança e exibição direta de comprovantes pré-existentes na conciliação bancária. |
| `frontend/assets/css/industrial-integrity.css` | Modificar | Estilos para a tabela de faturas, sub-tabela da matriz de pagamento e status chips de cartão. |
| `frontend/sw.js` | Modificar | Atualizar `CACHE_NAME` para `emc-soldas-v4.60` (Regra Mandatória 12 do AGENTS.md). |
| `frontend/index.html` | Modificar | Atualizar sufixos de cache-busting `?v=4.60` nas tags de script e css. |

---

## 4. Plano de Verificação e Testes

### 4.1 Testes Automatizados no Backend (`python manage.py test apps.financeiro`)
1. **Teste de Limite de Cartão:** Criação de cartão, acúmulo de despesas e bloqueio quando excede limite sem emergencial.
2. **Teste de Parcelamento em N Faturas:** Lançamento de compra em 3x; verificar criação de 3 faturas futuras, divisão com centavo de arredondamento e cálculo de limite comprometido.
3. **Teste de Ajuste de Fechamento com Redistribuição:** Antecipação e adiamento da data de corte; verificar migração automática das compras para a fatura correta.
4. **Teste de Fechamento e Liquidação (Total e com Rollover):** Fechamento de fatura e liquidação parcial; verificar débito na conta e geração de saldo anterior na fatura seguinte.
5. **Teste de Matriz de Pagamentos Multi-Meio:** Lançamento de compra com Dinheiro + PIX + Cartão; verificar impacto simultâneo nos caixas reais, criação de despesas no cartão e compartilhamento do anexo.

### 4.2 Verificação Visual e Operacional no Frontend
1. Acessar a nova aba `CARTÕES CORPORATIVOS` e verificar cards de KPI e tabela de faturas.
2. Criar uma compra com matriz multi-meio dividida entre Caixa da Oficina e Cartão de Crédito.
3. Conferir na aba Extrato o débito imediato no Caixa e na aba Cartões a fatura com o lançamento pendente.
4. Anexar um arquivo e validar a persistência em ambos os lançamentos e na Conciliação Bancária.
5. Testar responsividade em viewport de smartphone (<= 768px).

---

## 5. Registro de Aprovação (Proceed)
- **Status do Plano:** Aprovado e Concluído.
- **Data e Hora de Apresentação:** 2026-10-07 16:00
- **Aprovação do Usuário:** Aprovado explicitamente pelo usuário em 2026-10-07 16:16:04 via comando "Proceed".

---

## 6. Relatório de Execução (Pós-conclusão)

### 6.1 Resumo das Entregas Técnicas
1. **Modelagem de Dados e Migrações:**
   - Adicionados campos `grupo_pagamento_id` (UUID), `numero_parcela`, `total_parcelas` e `data_competencia` em `LancamentoFinanceiro`.
   - Migrações `0007_lancamentofinanceiro_grupo_pagamento_id_and_more.py` e `0008_lancamentofinanceiro_data_competencia.py` geradas e aplicadas no banco de dados.
2. **Serviços de Negócio:**
   - `services_cartao.py`: Suporte a compras parceladas em $N$ faturas futuras com centavo na 1ª parcela, recálculo dinâmico e redistribuição automática de itens por corte de fechamento (antecipação e adiamento), consolidação e fechamento de faturas, e liquidação com débito em conta bancária, validação de limite de cheque especial e rollover.
   - `services.py`: Função `registrar_compra_multi_meio` implementando transação atômica (`@transaction.atomic`), validação de soma de matriz, geração de `grupo_pagamento_id` e réplica do anexo/comprovante.
3. **Serializers e Views REST:**
   - `ItemMatrizPagamentoSerializer` e `LancamentoMultiMeioSerializer` criados e integrados.
   - Novas actions: `/api/lancamentos-financeiros/lancar-multi-meio/`, `/api/faturas-cartao/{id}/itens/`, `/api/faturas-cartao/{id}/fechar/`, `/api/faturas-cartao/{id}/liquidar/`, `/api/faturas-cartao/{id}/ajustar-fechamento/`, `/api/cartoes-credito/{id}/faturas/`.
4. **Interface Frontend (PWA Industrial Integrity):**
   - Aba completa `CARTÕES CORPORATIVOS` com seletor de cartão ativo, 4 flip cards de KPI (Contratual, Comprometido, Disponível, Fatura Vigente), timeline de navegação de faturas, detalhe de fechamento e tabela de compras com status de parcelas (`1/3`) e visualização de comprovantes.
   - Modais: Cadastro/Edição de Cartão, Ajustar Fechamento com preview explicativo, Fechar Fatura, Liquidar Fatura com suporte a rollover e débito bancário com cheque especial.
   - Componente de Matriz de Pagamentos Multi-Meio (Caixa de Mercado) no modal de novo lançamento, com balanço matemático em tempo real e lançamento atômico com anexo único.
   - Reuso e exibição direta de comprovantes pré-existentes na Conciliação Bancária (`conciliacao-view.js`).
5. **Governança de Assets e PWA:**
   - Incremento da versão do Service Worker (`frontend/sw.js`) para `emc-soldas-v4.60`.
   - Atualização universal de cache-busting `?v=4.60` em todas as tags de CSS e JS no `frontend/index.html`.

### 6.2 Evidências de Validação Automatizada
- Bateria de testes `CartaoParcelamentoMatrizPagamentoTestCase` criada e aprovada (4 testes com 100% de sucesso).
- Suíte completa do módulo `apps.financeiro` executada com 34 testes aprovados (0 erros, 0 falhas).
- Suíte global de regressão de todo o sistema executada com 209 testes aprovados (0 erros, 0 falhas).

