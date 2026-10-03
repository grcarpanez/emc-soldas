# Plano de Implementação - Tooltips com Segregação por Categoria no Gráfico do Dashboard

**ID da Tarefa:** `2026-10-03_08_tooltips_grafico_categorias`  
**Data:** 03/10/2026  
**Status:** `Concluído`  
**Autor:** Antigravity AI  
**Registro do Proceed:** Aprovado pelo usuário em 03/10/2026 às 15:17 ("Proceed")  

---

## 1. Contexto e Motivação
Atualmente, as barras mensais de **Receitas Líquidas** (verdes) e **Despesas Pagas** (vermelhas) no gráfico comparativo anual do Dashboard exibem apenas um atributo HTML simples com o total geral. O usuário solicitou que, ao passar o mouse sobre cada barra (hover), seja exibido um tooltip interativo e detalhado com as receitas ou despesas daquele mês segregadas por categoria financeira (`CategoriaFinanceira`), exibindo o valor monetário e o percentual correspondente.

---

## 2. Decisões Arquiteturais e Técnicas

### 2.1 Backend (`backend/apps/relatorios/services.py` & `serializers.py`)
1. **Agregação SARGable por Categoria:**
   - Na rotina `DashboardService.obter_graficos_receitas_despesas(ano)`:
   - Para cada um dos 12 meses do ano selecionado, em vez de realizar apenas a soma total de valores, faremos a consulta agrupada por categoria com timezone-aware datetime range:
     ```python
     # Receitas por Categoria
     rec_qs = LancamentoFinanceiro.objects.filter(
         deleted_at__isnull=True,
         tipo_lancamento='ENTRADA',
         status_pagamento='PAGO',
         data_pagamento__gte=dt_ini_mes,
         data_pagamento__lt=dt_fim_mes
     ).values('categoria__nome').annotate(total=Sum('valor')).order_by('-total')
     ```
     E de forma idêntica para as saídas/despesas (`tipo_lancamento='SAIDA'`).
   - A soma total do mês será calculada diretamente pela soma das categorias retornadas na memória (`sum(c['valor'] for c in categorias)`), mantendo o número exato de consultas idêntico ao atual (2 queries por mês = 24 queries ultra-rápidas executadas em ~0.06s).
   - O payload de cada mês incluirá:
     - `receitas`: valor decimal total.
     - `receitas_categorias`: lista ordenada de `[{ "categoria": "NOME DA CATEGORIA", "valor": 1234.56 }, ...]`.
     - `despesas`: valor decimal total.
     - `despesas_categorias`: lista ordenada de `[{ "categoria": "NOME DA CATEGORIA", "valor": 1234.56 }, ...]`.
2. **Atualização dos Serializers:**
   - Em `backend/apps/relatorios/serializers.py`, criar `CategoriaValorSerializer` e atualizar `GraficosReceitasDespesasSerializer` documentando as listas de categorias em cada mês.

### 2.2 Frontend (`frontend/assets/js/views/dashboard-view.js` & `frontend/assets/css/industrial-integrity.css`)
1. **Design System Industrial Integrity (0px border-radius):**
   - Criação da classe `.chart-tooltip` em `industrial-integrity.css`:
     - Fundo escuro industrial (`#141414` / `var(--color-surface-container-high)`).
     - Borda técnica reta `1px solid var(--color-steel-gray)` (`#71797E`).
     - Cantos estritamente retos (`border-radius: 0px`).
     - Tipografia técnica: `Inter` para rótulos/categorias e `JetBrains Mono` (`var(--font-mono)`) para valores monetários e percentuais.
     - Sombra suave profunda (`box-shadow: 0 8px 24px rgba(0, 0, 0, 0.85)`).
     - Cabeçalho com indicador colorido (verde para receitas, vermelho para despesas), mês/ano de referência e valor total destacado.
     - Lista com as categorias, seus respectivos valores formatados em Real (`R$`) e o percentual de representatividade relativo ao total do mês (`X.X%`).
2. **Posicionamento Inteligente Flutuante:**
   - Criação de um elemento tooltip flutuante exclusivo dentro do container do gráfico (`#dashboard-chart-container`).
   - Cálculo dinâmico de coordenadas relativas com base no `getBoundingClientRect()` da barra em foco:
     - Centralizado horizontalmente em relação à barra.
     - Clamp automático nas extremidades esquerda e direita para nunca vazar os limites do card do gráfico.
     - Posicionado logo acima da barra (ou invertido para baixo caso a barra ocupe quase a altura total do card).
   - Suporte a Desktop (hover com mouse) e Mobile/Tablet (toque/tap na barra).

### 2.3 Versionamento de Assets PWA
- Elevação mandatória da versão do Service Worker em `frontend/sw.js` para `CACHE_NAME = 'emc-soldas-v4.39'`.
- Atualização dos parâmetros de cache-busting em `frontend/index.html` para `?v=4.39`.

---

## 3. Arquivos Afetados

| Arquivo | Responsabilidade / Modificação |
|---|---|
| `Planejamento/2026-10-03_08_tooltips_grafico_categorias.md` | Registro formal do plano de implementação e aprovação (`Proceed`). |
| `backend/apps/relatorios/services.py` | Agrupamento por `categoria__nome` no método `obter_graficos_receitas_despesas`. |
| `backend/apps/relatorios/serializers.py` | Definição de `CategoriaValorSerializer` e tipagem no `GraficosReceitasDespesasSerializer`. |
| `backend/apps/relatorios/tests.py` | Testes unitários para validar a segregação por categoria nas receitas e despesas. |
| `frontend/assets/css/industrial-integrity.css` | Estilos visuais do componente `.chart-tooltip` (0px border-radius, tipografia mono). |
| `frontend/assets/js/views/dashboard-view.js` | Renderização do gráfico, listeners de hover/touch e exibição do tooltip inteligente. |
| `frontend/sw.js` | Incremento da versão do cache para `emc-soldas-v4.39`. |
| `frontend/index.html` | Atualização do cache-busting para `?v=4.39`. |
| `docs/STATUS.md` | Atualização do checklist e histórico de versão. |

---

## 4. Plano de Testes e Validação

1. **Testes Automatizados de Backend:**
   - Executar `python backend/manage.py test backend/apps/relatorios/` para verificar os novos campos no serializer e resposta do serviço.
   - Executar a suíte completa de testes (`python backend/manage.py test backend/`) garantindo 100% de sucesso sem regressões.
2. **Testes de Integração e Frontend:**
   - Testar o endpoint `/api/dashboard/graficos/?ano=2025` e verificar a listagem de `receitas_categorias` e `despesas_categorias`.
   - Passar o mouse sobre barras de despesas com múltiplas categorias (ex: Maio/2025 que possui combustível, peças, pró-labore, etc.) e conferir se o tooltip abre suavemente, alinhado à barra, com os nomes das categorias e percentuais corretos.
   - Passar o mouse sobre barras de receitas (100% prestação de serviços) e verificar o cálculo de percentual e formatação monetária.
   - Testar barras com valor `R$ 0,00` exibindo "Nenhum lançamento no período".
   - Testar responsividade em viewport reduzida e extremidades (Janeiro e Dezembro) conferindo que o tooltip não transborda a tela.
3. **Commit Semântico:**
   - Executar commit formal: `feat(dashboard): implementar tooltips com segregacao por categoria no grafico`.

---

## 5. Relatório de Execução e Homologação

- **Backend Implementado:**
  - `obter_graficos_receitas_despesas` em `apps/relatorios/services.py`: Agrupamento de `LancamentoFinanceiro` por `categoria__nome` via SARGable range queries. Cada mês retorna `receitas_categorias` e `despesas_categorias` ordenadas de forma decrescente por valor.
  - Serializers em `apps/relatorios/serializers.py`: Criação de `CategoriaItemSerializer` e `MesGraficoSerializer` garantindo validação e integridade tipada.
- **Frontend PWA e Design System:**
  - `frontend/assets/css/industrial-integrity.css`: Definição de `.chart-tooltip` com 0px border-radius, tipografia técnica (`Inter` para títulos/categorias e `JetBrains Mono` para valores/percentuais), sombra profunda e contraste escuro.
  - `frontend/assets/js/views/dashboard-view.js`: Barras com classe `.chart-bar-interactive`, cálculo dinâmico de percentual de cada categoria, clamps laterais para não vazar a tela e suporte a hover e toque mobile.
- **Versionamento PWA:**
  - `frontend/sw.js` atualizado para `CACHE_NAME = 'emc-soldas-v4.39'`.
  - `frontend/index.html` atualizado com sufixos `?v=4.39`.
- **Suíte de Testes Automatizados:**
  - 14 testes específicos de `apps.relatorios` executados e 100% aprovados.
  - 197 testes da suíte global executados com sucesso total (77.8s) sem nenhuma falha ou regressão.

