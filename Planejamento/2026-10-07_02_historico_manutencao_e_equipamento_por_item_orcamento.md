# Implementation Plan - Histórico de Manutenção de Equipamentos e Vinculação por Item de Orçamento

- **Data:** 2026-10-07
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Concluído
- **Registro do Proceed:** Aprovado explicitamente pelo usuário em 2026-10-07 12:08:09 via "Proceed".
- **Arquivo de Registro:** `Planejamento/2026-10-07_02_historico_manutencao_e_equipamento_por_item_orcamento.md`

---

## 1. Contexto e Motivação

### 1.1 Diagnóstico Apresentado pelo Usuário
1. **Erro Estrutural na Modelagem Atual:**
   - O modelo `Orcamento` atualmente possui uma ForeignKey direta com `Equipamento` (`orcamentos.equipamento_id`).
   - Essa modelagem 1:1 entre Orçamento e Equipamento impede que um cliente traga mais de um veículo ou equipamento no mesmo atendimento (ex: um caminhão e uma carreta, ou duas máquinas industriais), forçando a criação de orçamentos apartados e dificultando a negociação comercial, o faturamento unificado e a consolidação de pré-faturas.
2. **Necessidade de Vinculação no Item do Orçamento (`OrcamentoItem`):**
   - O vínculo com `Equipamento` deve residir no **item do orçamento**, permitindo que um único orçamento contenha linhas de serviço/peças para $N$ equipamentos diferentes, ou até itens gerais da oficina não vinculados a um equipamento específico.
3. **Controle e Prontuário de Manutenção por Equipamento:**
   - O sistema já possui um histórico de titularidade/movimentação (transferências de proprietários).
   - É necessário um **Controle de Manutenção de Equipamentos e Veículos** com botão dedicado na listagem de equipamentos e no dossiê de frotas, permitindo acompanhar cronologicamente **tudo o que já foi feito em cada equipamento/veículo**: serviços executados, peças e insumos aplicados, datas de execução, valores e os orçamentos de origem.

---

## 2. Decisões Arquiteturais e de Engenharia

### 2.1 Modelagem de Dados (`backend/apps/orcamentos/models.py`)
1. **Nova ForeignKey em `OrcamentoItem`:**
   ```python
   equipamento = models.ForeignKey(
       'cadastros.Equipamento',
       on_delete=models.SET_NULL,
       null=True,
       blank=True,
       related_name='itens_orcamento',
       db_column='equipamento_id',
       verbose_name="Equipamento / Veículo"
   )
   ```
   - `on_delete=models.SET_NULL`: Protege o histórico caso o equipamento seja manipulado ou transferido.
   - Índice em `equipamento_id` na classe `Meta` para acelerar consultas do prontuário de manutenção.
2. **Manutenção de Compatibilidade em `Orcamento.equipamento`:**
   - Mantido como campo opcional (`null=True, blank=True, on_delete=models.SET_NULL`).
   - Atuará como "Equipamento Padrão / Sugerido" no cabeçalho: se preenchido na criação do orçamento, preenche automaticamente os novos itens inseridos como sugestão padrão, agilizando orçamentos com equipamento único.
3. **Data Migration (Migração de Preservação Histórica):**
   - Criação de migração Django que copia `orcamento.equipamento_id` para `item.equipamento_id` em todos os `OrcamentoItem` já existentes no banco de dados. Nenhum histórico existente será perdido.

### 2.2 Serializers e Lógica de Negócio (`backend/apps/orcamentos/serializers.py`)
1. **`OrcamentoItemSerializer`:**
   - Campo `equipamento` (PrimaryKeyRelatedField, allow_null=True, required=False).
   - Campos de leitura: `equipamento_placa`, `equipamento_identificacao`, `equipamento_descricao`, `equipamento_display`.
   - `to_internal_value`: mapeamento flexível de `equipamento_id` e normalização de `null`.
2. **`OrcamentoSerializer`:**
   - No `create` e `update`: repassar `equipamento_id` ao salvar cada `OrcamentoItem`. Fallback: se o item não tiver equipamento mas o cabeçalho tiver, herdar o do cabeçalho.
   - Campo `equipamentos_envolvidos`: lista agregada com os equipamentos únicos envolvidos nas linhas daquele orçamento.

### 2.3 Endpoint de Histórico de Manutenção (`backend/apps/cadastros/views.py`)
1. Adicionar action `@action(detail=True, methods=['get'], url_path='historico-manutencao')` em `EquipamentoViewSet`:
   - Busca todos os `OrcamentoItem` onde `equipamento_id = equipamento.id` (e suporte fallback a `orcamento.equipamento_id == equipamento.id`) com `orcamento.deleted_at__isnull=True`.
   - Suporta filtros na query string:
     - `search`: busca por termo em produto, insumo, descrição livre ou ID do orçamento.
     - `status_operacional`: filtrar por status (ex: `CONCLUIDO` ou múltiplos).
     - `data_inicio` e `data_fim`: intervalo de datas do serviço.
   - Resumo consolidado com métricas:
     - `total_intervencoes`: quantidade de orçamentos distintos.
     - `total_itens_aplicados`: quantidade de linhas de serviços/peças.
     - `valor_total_acumulado`: total financeiro das intervenções.
     - `data_ultima_intervencao`: data do último serviço registrado.
   - Lista detalhada de manutenções com orçamento, data, status operacional/financeiro, cliente na época, item/serviço, quantidade, valor unitário e subtotal.

### 2.4 Atualizações Complementares no Backend
1. **`EquipamentoSerializer` (`backend/apps/cadastros/serializers.py`):**
   - Ajustar `get_em_patio` e `get_orcamento_em_execucao` para verificar tanto `obj.orcamentos` quanto `obj.itens_orcamento`.
2. **Filtro de Pátio (`backend/apps/cadastros/views.py`):**
   - Atualizar filtro `no_patio` para verificar equipamentos presentes em orçamentos em execução através dos itens.
3. **Filtro e Busca de Orçamentos (`backend/apps/orcamentos/views.py`):**
   - Atualizar filtro `equipamento_id` para: `Q(equipamento_id=equipamento_id) | Q(itens_orcamento__equipamento_id=equipamento_id)`.
   - Atualizar `search_fields` e prefetch.
4. **Geração de PDF (`backend/apps/orcamentos/pdf_service.py`):**
   - No cabeçalho: se houver 1 equipamento, exibe seus dados; se houver múltiplos, exibe lista dos equipamentos atendidos.
   - Na grade de itens: incluir a identificação do equipamento vinculado ao item (ex: `[PLACA]`).

### 2.5 Frontend - Interface e Experiência do Usuário (UI/UX)
1. **Tela de Clientes & Equipamentos (`cadastros-view.js`):**
   - Na tabela de equipamentos:
     - Botão **`MANUTENÇÃO`** (abre o prontuário de manutenção).
     - Renomear o botão antigo de `HISTÓRICO` para **`TITULARIDADE`** (para segregar claramente histórico de donos x histórico de manutenção).
     - Botões `EDITAR` e `EXCLUIR`.
   - No modal de frota de clientes: adicionar botão **`MANUTENÇÃO`** ao lado de `TITULARIDADE`.
2. **Modal de Prontuário de Manutenção (`abrirModalHistoricoManutencao(equipId)`):**
   - Padrão *Industrial Integrity*:
     - Título: `PRONTUÁRIO DE MANUTENÇÃO - #{id} {DESCRICAO} [{PLACA}]`
     - 4 flip/metric cards no topo: Intervenções, Peças/Serviços, Investimento Total (R$) e Última Intervenção.
     - Barra de filtro por busca e status operacional.
     - Tabela detalhada de itens aplicados com chips de status, data, cliente, item/peça, qtd, valor e botão `VER ORÇAMENTO` que abre o modal de detalhes do orçamento diretamente.
3. **Tela de Orçamentos (`orcamentos-view.js`):**
   - No modal de criação de orçamento:
     - Cabeçalho: Cliente, Equipamento Sugerido/Padrão (opcional), Validade.
     - Montador de itens: adicionar seletor de "Equipamento / Veículo" para cada item (filtrado pelos veículos do cliente selecionado).
     - Grade de itens temporários: nova coluna "EQUIPAMENTO / VEÍCULO".
     - Payload: envio de `equipamento_id` em cada item.
   - No modal de detalhes: exibir o equipamento de cada item na tabela.
   - Na lista principal de orçamentos: exibir equipamentos envolvidos no orçamento.
4. **PWA e Cache:**
   - Incrementar versão no `frontend/sw.js` para `v4.59`.
   - Atualizar tags com `?v=4.59` no `frontend/index.html`.

---

## 3. Arquivos a Criar e Modificar

| Arquivo | Ação | Descrição |
|---|---|---|
| `backend/apps/orcamentos/models.py` | Modificar | Adicionar `equipamento` e índice em `OrcamentoItem`; ajustar `Orcamento.equipamento` |
| `backend/apps/orcamentos/migrations/0002_add_equipamento_to_orcamento_item.py` | Criar | Migração de schema e data migration para preencher itens legados |
| `backend/apps/orcamentos/serializers.py` | Modificar | Adicionar campo de equipamento por item e serialização completa |
| `backend/apps/orcamentos/views.py` | Modificar | Suporte a busca e filtro por equipamento nos itens do orçamento |
| `backend/apps/orcamentos/pdf_service.py` | Modificar | Suporte a identificação de equipamentos por item e múltiplos equipamentos no PDF |
| `backend/apps/cadastros/views.py` | Modificar | Criar action `historico_manutencao` em `EquipamentoViewSet` e ajustar filtro `no_patio` |
| `backend/apps/cadastros/serializers.py` | Modificar | Ajustar detecção de `em_patio` e `orcamento_em_execucao` considerando itens |
| `backend/apps/orcamentos/tests.py` | Modificar | Adicionar testes para orçamentos multi-equipamento |
| `backend/apps/cadastros/tests.py` | Modificar | Adicionar testes para o endpoint de histórico de manutenção |
| `frontend/assets/js/views/cadastros-view.js` | Modificar | Adicionar botão `MANUTENÇÃO`, renomear `TITULARIDADE` e criar modal de histórico de manutenção |
| `frontend/assets/js/views/orcamentos-view.js` | Modificar | Adicionar seletor de equipamento por item, coluna na grade e exibição em detalhes |
| `frontend/sw.js` | Modificar | Atualizar `CACHE_NAME` para `emc-soldas-v4.59` |
| `frontend/index.html` | Modificar | Atualizar sufixos `?v=4.59` |
| `docs/STATUS.md` | Modificar | Registrar nova funcionalidade e evolução da modelagem |

---

## 4. Plano de Verificação e Testes

1. **Testes Unitários e Automatizados:**
   - Executar `.\venv\Scripts\python.exe backend\manage.py test apps/` e garantir 100% de aprovação (todos os testes anteriores + novos testes).
   - Validar testes específicos de criação de orçamento com itens associados a equipamentos distintos.
   - Validar retorno do endpoint `/api/equipamentos/{id}/historico-manutencao/`.
2. **Testes Manuais de Fluxo:**
   - Criar um orçamento para um cliente com 2 equipamentos cadastrados (ex: Item 1 para Equipamento A, Item 2 para Equipamento B).
   - Abrir o modal de detalhes do orçamento e confirmar que cada item exibe seu respectivo veículo.
   - Ir na tela de Equipamentos e clicar no botão `MANUTENÇÃO` do Equipamento A: verificar se apenas o Item 1 aparece no seu prontuário com métricas corretas.
   - Clicar no botão `MANUTENÇÃO` do Equipamento B: verificar se o Item 2 aparece no seu prontuário.
   - Clicar em `VER ORÇAMENTO` dentro do modal de manutenção e checar a abertura fluida dos detalhes.
   - Clicar no botão `TITULARIDADE` e verificar que o histórico de transferências de proprietários continua intacto.
   - Gerar o PDF do orçamento e conferir a apresentação limpa e legível dos equipamentos atendidos.

---

## 5. Relatório de Execução Pós-Conclusão

- **Data de Conclusão:** 2026-10-07
- **Resultado:** Concluído com 100% de sucesso e zero regressões.
- **Entregas Realizadas:**
  1. **Modelagem de Dados e Migrações:**
     - Adicionado campo `OrcamentoItem.equipamento` como FK para `cadastros.Equipamento` com `on_delete=SET_NULL`, `db_column='equipamento_id'` e índices de busca `idx_orc_item_orcamento` e `idx_orc_item_equipamento`.
     - Migração gerada e executada: `0005_orcamentoitem_equipamento_and_more.py`, com operação de `RunPython` preservando retroativamente todos os equipamentos associados aos itens passados.
  2. **Endpoint e Lógica de Prontuário:**
     - Implementado endpoint `@action(detail=True, methods=['get'], url_path='historico-manutencao')` em `EquipamentoViewSet`.
     - Agregação de intervenções técnicas, métricas consolidadas (total de ordens, total de itens, investimento acumulado, datas de primeira e última intervenção) e filtros flexíveis.
  3. **Interface PWA (*Industrial Integrity*):**
     - Botão `TITULARIDADE` dedicado para histórico de transferências de donos.
     - Botão `MANUTENÇÃO` abrindo modal de prontuário com cards KPI, filtro de status em tempo real, barra de busca e tabela técnica com atalho `VER ORÇAMENTO`.
     - No módulo de Orçamentos: seletor de equipamento por item com autocomplete e sincronização com cabeçalho, grid de itens com coluna de veículo e modal de detalhes com identificação precisa.
     - PDF técnico atualizado para orçamentos multi-veículo.
  4. **Validação e Testes Automatizados:**
     - Criado teste `test_15_criacao_orcamento_com_multiplos_equipamentos_por_item` em `apps/orcamentos/tests.py`.
     - Criado teste `test_historico_manutencao_equipamento` em `apps/cadastros/tests.py`.
     - Suíte completa de testes executada: **195 testes passando com 100% de sucesso**.
  5. **Versionamento e Governança:**
     - Service worker incrementado para `emc-soldas-v4.59`.
     - Cache-busting atualizado para `?v=4.59` no `index.html`.
     - Documentos vivos `docs/STATUS.md` e `docs/ERROS.md` atualizados.

