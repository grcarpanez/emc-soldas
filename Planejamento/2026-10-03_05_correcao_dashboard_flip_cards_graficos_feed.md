# Plano de Implementação - Correção Integral do Dashboard (Flip Cards, Gráfico SARGable e Feed)

**Data:** 2026-10-03  
**Autor:** Antigravity  
**Status:** Concluído  
**Registro de Aprovação (Proceed):** Aprovado pelo usuário em 2026-10-03 11:10:20 com a mensagem: *"Proceed"*  

---

## 1. Contexto e Objetivos

O usuário relatou que o Dashboard Principal (`#/dashboard`) não estava funcionando e estava com todas as informações zeradas.
A investigação identificou 4 causas raízes principais:
1. Incompatibilidade estrutural e de nomenclatura de chaves no payload dos 5 Flip Cards (`/api/dashboard/flip-cards/`), onde o frontend tentava acessar `res.cards` inexistente e propriedades que divergiam do backend;
2. Falha silenciosa no Gráfico de Receitas x Despesas no MySQL: a utilização de `data_pagamento__year` e `data_pagamento__month` em campos `DateTimeField` dispara a função `CONVERT_TZ` do MySQL, que retorna `NULL` quando a tabela de fusos horários do MySQL não está carregada (comum em Windows/XAMPP), fazendo com que todos os meses retornassem R$ 0,00; além de o frontend esperar `res.historico` enquanto o backend retornava `res.meses`;
3. Incompatibilidade no Feed de Atividades Recentes (`/api/dashboard/feed/`): backend retornava uma lista direta (`[...]`) e o frontend esperava `res.atividades`, além de chave `data_hora` vs `timestamp`;
4. Inoperância dos botões de filtro de período ("HOJE", "MÊS ATUAL", "ANO"), cujos parâmetros não eram interpretados pelo serializer nem pela view do backend.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Backend: Unificação e Enriquecimento do Contrato de Dados dos Flip Cards
- Em `backend/apps/relatorios/services.py` (`DashboardService.obter_flip_cards`):
  - Retornar tanto o formato direto (`operacao`, `faturamento`, `receita`, `caixa`, `alertas`) quanto a chave de espelho `cards: { ... }`, garantindo retrocompatibilidade com qualquer consumidor da API;
  - Entregar os nomes de propriedades esperados pelo frontend sem remover os nomes legados:
    - **Operação:** `aprovados`, `em_execucao`, `concluidos`, `cancelados`, `orcamentos_aprovados`, `orcamentos_concluidos`, `orcamentos_gerados`, `total_orcamentos`, `taxa_aprovacao_percentual`, `valor_total_orcado`, `valor_total_aprovado`;
    - **Faturamento:** `rascunhos`, `faturadas`, `pagas`, `canceladas`, `faturas_rascunho`, `faturas_faturadas`, `faturas_pagas`, `total_faturas`, `valor_bruto_faturado`, `desconto_total_concedido`, `valor_liquido_faturado`;
    - **Receita:** `faturamento_real` (alias de `receita_real`), `faturamento_projetado` (alias de `receita_projetada`), `a_receber_pendente` (contas a receber com vencimento no período não quitadas), `taxa_realizacao_percentual`, `diferenca_projetado_real`;
    - **Caixa:** `saldo_bancario_real` (alias de `saldo_real_consolidado`), `contas_a_pagar_pendente` (alias de `previsao_saidas`), `contas_a_receber_pendente` (alias de `previsao_entradas`), `saldo_projetado`;
    - **Alertas:** `vencidas` (soma de contas a pagar e a receber vencidas em atraso), `vencendo_hoje` (alias de `vencendo_hoje_qtd`), `vencendo_hoje_valor`, `proximos_7_dias` (alias de `proximos_7_dias_qtd`), `proximos_7_dias_valor`.

### 2.2 Backend: Gráfico Mensal Portável e SARGable (Bypass no `CONVERT_TZ` do MySQL)
- Em `backend/apps/relatorios/services.py` (`DashboardService.obter_graficos_receitas_despesas`):
  - Determinação inteligente de ano: se `ano` não for fornecido, verificar se há dados no ano corrente; caso não haja e existam lançamentos no banco (ex: 2025), adotar automaticamente o ano do lançamento mais recente para que o histórico importado seja visualizado de imediato;
  - Substituir o filtro dependente de `CONVERT_TZ` (`data_pagamento__year` e `data_pagamento__month`) por intervalos SARGable com timezone-aware datetimes:
    `data_pagamento__gte=dt_ini_mes, data_pagamento__lt=dt_fim_mes`;
  - Retornar em cada mês: `mes`, `mes_nome`, `mes_sigla`, `receitas`, `despesas`, `resultado_liquido`;
  - Retornar no payload tanto `meses` quanto `historico` (`res.historico = res.meses`).

### 2.3 Backend: Suporte ao Parâmetro `periodo` (Hoje, Mês Atual, Ano)
- Em `backend/apps/relatorios/serializers.py`:
  - Adicionar o campo `periodo = serializers.CharField(required=False)` no `FiltroPeriodoSerializer`;
  - Adicionar campos opcionais de espelho nos serializers de resposta (`cards`, `historico`, `data_hora`).
- Em `backend/apps/relatorios/views.py` (`DashboardFlipCardsView`):
  - Capturar `periodo = request.query_params.get('periodo', '').lower()`;
  - Se `data_inicio` e `data_fim` não forem passadas explicitamente:
    - `'hoje'`: `data_inicio = hoje`, `data_fim = hoje`;
    - `'mes'`: `data_inicio = primeiro dia do mês`, `data_fim = hoje`;
    - `'ano'`: `data_inicio = 01/01 do ano`, `data_fim = 31/12 do ano`.

### 2.4 Backend: Enriquecimento do Feed de Atividades
- Em `backend/apps/relatorios/services.py` (`DashboardService.obter_feed_atividades`):
  - Incluir tanto `timestamp` quanto `data_hora` nos itens do feed;
  - Em `views.py`, manter retorno de lista direta `[...]` para preservar 100% de compatibilidade com os testes unitários.

### 2.5 Frontend: Ajuste Defensivo e Exibição do Ano no Gráfico (`dashboard-view.js`)
- Em `frontend/assets/js/views/dashboard-view.js`:
  - `carregarFlipCards`: adotar extração resiliente `const cards = res.cards || res || {};`;
  - `carregarGrafico`: adotar `const meses = res.historico || res.meses || [];`, e atualizar dinamicamente o título do card para refletir o ano consultado (`RECEITAS X DESPESAS (${res.ano || 'ANO ATUAL'})`);
  - `carregarFeed`: adotar `const items = Array.isArray(res) ? res : (res.atividades || []);` e leitura `item.data_hora || item.timestamp`.

### 2.6 Governança de Cache PWA e Versionamento Sincronizado
- Incrementar `CACHE_NAME` para `emc-soldas-v4.36` em `frontend/sw.js`;
- Atualizar sufixos `?v=4.36` no `frontend/index.html`.

---

## 3. Arquivos Modificados

1. `backend/apps/relatorios/services.py` - Lógica de agregação dos Flip Cards com aliases, ranges SARGable do Gráfico, determinação inteligente de ano e Feed com `data_hora`.
2. `backend/apps/relatorios/views.py` - Interpretação dos filtros `hoje`, `mes` e `ano` em `DashboardFlipCardsView`.
3. `backend/apps/relatorios/serializers.py` - Inclusão de `periodo` e campos de compatibilidade nos serializers.
4. `backend/apps/relatorios/tests.py` - Suíte de testes enriquecida com validação de períodos, espelho de cards, histórico no gráfico e data_hora no feed.
5. `frontend/assets/js/views/dashboard-view.js` - Resiliência na leitura de cards, meses do gráfico, ano no cabeçalho e feed.
6. `frontend/sw.js` - Atualização da versão do cache para `emc-soldas-v4.36`.
7. `frontend/index.html` - Atualização dos sufixos de cache-busting `?v=4.36`.
8. `docs/STATUS.md` - Registro da conclusão da melhoria e histórico vivo.
9. `docs/ERROS.md` - Registro do incidente e prevenção técnica contra o uso de `__year`/`__month` em MySQL.

---

## 4. Plano de Verificação e Testes

1. **Testes Automatizados do Django:**
   - Executados 14 testes de `apps.relatorios` com 100% de sucesso.
   - Executada a suíte completa de testes (193 testes) com 100% de sucesso.
2. **Teste de Integração no MySQL via Shell:**
   - Confirmado que os Flip Cards retornam o saldo real consolidado (R$ 1.285,77) e os alertas de atraso reais.
   - Confirmado que o gráfico carrega as movimentações reais de 2025 (Março a Julho/2025 com receitas de até R$ 10.898,20 e despesas de R$ 9.864,10).
   - Confirmado que o feed lista as 20 atividades cronológicas mais recentes com `data_hora`.

---

## 5. Relatório de Execução (Pós-conclusão)

- **Resultado Geral:** Implementação concluída com 100% de conformidade arquitetural e técnica.
- **Evidências de Homologação:**
  - `apps.relatorios`: 14 testes aprovados em 5.1s.
  - Suíte Global: 193 testes aprovados em 79.4s (`OK`).
  - MySQL Shell: Saldo de contas real em R$ 1.285,77, 1 conta vencida em atraso, 5 meses de movimentações no gráfico de receitas x despesas e feed cronológico ativo.
- **Cache PWA:** Sincronizado para `emc-soldas-v4.36`.
