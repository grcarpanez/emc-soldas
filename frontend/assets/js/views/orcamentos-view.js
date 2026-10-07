/**
 * EMC Soldas - View de Orçamentos Comerciais
 * Elaboração dinâmica, Snapshots, Validade, Renovação com Alerta de Inflação e Geração PDF.
 */

window.OrcamentosView = {
  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">ORÇAMENTOS COMERCIAIS</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">ELABORAÇÃO, SNAPSHOTS DE CUSTO, VALIDADE E GERAÇÃO DE PROPOSTAS</p>
        </div>
      </div>

      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-orc-busca" class="form-control" placeholder="BUSCAR POR CLIENTE, EQUIPAMENTO OU ID..." style="flex: 1; min-width: 220px;">
          <div style="width: 230px; min-width: 190px; flex-shrink: 0;" id="wrapper-orc-status">
            <select id="filtro-orc-status" class="form-control">
              <option value="">TODOS OS STATUS OPERACIONAIS</option>
              <option value="GERADO">GERADO</option>
              <option value="ENVIADO">ENVIADO</option>
              <option value="APROVADO">APROVADO</option>
              <option value="EM_EXECUCAO">EM EXECUÇÃO</option>
              <option value="CONCLUIDO">CONCLUÍDO</option>
              <option value="CANCELADO">CANCELADO</option>
            </select>
          </div>
          <select id="filtro-orc-status-fin" class="form-control" style="width: 215px; min-width: 195px; flex-shrink: 0;">
            <option value="">FINANCEIRO: TODOS</option>
            <option value="A_FATURAR">A FATURAR</option>
            <option value="FATURADO">FATURADO</option>
            <option value="PAGO">PAGO</option>
            <option value="CANCELADO">CANCELADO</option>
          </select>
          <span id="total-orc-badge" class="status-chip secondary mono-text" style="padding: 7px 12px; flex-shrink: 0;">0 ORÇAMENTOS</span>
          <button class="btn btn-primary" id="btn-novo-orcamento" style="white-space: nowrap; flex-shrink: 0;">+ NOVO ORÇAMENTO</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>CLIENTE</th>
              <th>EQUIPAMENTO</th>
              <th>GERAÇÃO / VALIDADE</th>
              <th>STATUS OPERACIONAL</th>
              <th>STATUS FINANCEIRO</th>
              <th>VALOR TOTAL</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-orc-tbody">
            <tr><td colspan="8" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    const selStatusOp = document.getElementById('filtro-orc-status');
    if (selStatusOp) {
      window.EMCUtils.initMultiSelectCombobox(selStatusOp, {
        placeholder: 'OPERACIONAL: TODOS',
        prefix: 'OPERACIONAL',
        onChange: () => this.carregarListaOrcamentos()
      });
    }

    document.getElementById('btn-novo-orcamento')?.addEventListener('click', () => this.abrirModalNovoOrcamento());
    document.getElementById('filtro-orc-busca')?.addEventListener('input', () => this.carregarListaOrcamentos());
    document.getElementById('filtro-orc-status-fin')?.addEventListener('change', () => this.carregarListaOrcamentos());

    this.carregarListaOrcamentos();
  },

  async carregarListaOrcamentos() {
    const tbody = document.getElementById('lista-orc-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-orc-busca')?.value.trim() || '';
    const selStatus = document.getElementById('filtro-orc-status');
    const statusOp = selStatus?._emcMultiSelect ? selStatus._emcMultiSelect.getValues().join(',') : (selStatus?.value || '');
    const statusFin = document.getElementById('filtro-orc-status-fin')?.value || '';

    try {
      const query = new URLSearchParams();
      if (busca) query.append('search', busca);
      if (statusOp) query.append('status_operacional', statusOp);
      if (statusFin) query.append('status_financeiro', statusFin);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.ORCAMENTOS.LISTA}?${query.toString()}`);
      const lista = res.results || res || [];

      const badge = document.getElementById('total-orc-badge');
      if (badge) {
        const count = lista.length;
        badge.textContent = `${count} ${count === 1 ? 'ORÇAMENTO' : 'ORÇAMENTOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum orçamento encontrado.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((orc) => {
        const badgeOp = {
          GERADO: 'info',
          ENVIADO: 'info',
          APROVADO: 'success',
          EM_EXECUCAO: 'warning',
          CONCLUIDO: 'success',
          CANCELADO: 'danger'
        }[orc.status_operacional] || 'info';

        const badgeFin = {
          A_FATURAR: 'warning',
          FATURADO: 'info',
          PAGO: 'success',
          CANCELADO: 'danger'
        }[orc.status_financeiro] || 'info';

        const statusOpTexto = orc.status_operacional_display || window.EMCUtils.formatarStatus(orc.status_operacional);
        const statusFinTexto = orc.status_financeiro_display || window.EMCUtils.formatarStatus(orc.status_financeiro);

        html += `
          <tr>
            <td class="mono-text"><strong>#${orc.id}</strong></td>
            <td><strong>${window.EMCUtils.escapeHtml(orc.cliente_nome || 'Cliente')}</strong></td>
            <td class="mono-text" style="font-size: 12px;">
              ${window.EMCUtils.escapeHtml(
                (orc.equipamentos_envolvidos && orc.equipamentos_envolvidos.length > 1)
                  ? `MÚLTIPLOS VEÍCULOS (${orc.equipamentos_envolvidos.length})`
                  : (orc.equipamentos_envolvidos?.[0]?.display || orc.equipamento_descricao || 'Geral / Oficina')
              )}
            </td>
            <td class="mono-text" style="font-size: 12px;">
              ${window.EMCUtils.formatarDataPtBr(orc.data_geracao)} ➔ ${window.EMCUtils.formatarDataPtBr(orc.data_validade)}
            </td>
            <td><span class="status-chip ${badgeOp}">${window.EMCUtils.escapeHtml(statusOpTexto)}</span></td>
            <td><span class="status-chip ${badgeFin}">${window.EMCUtils.escapeHtml(statusFinTexto)}</span></td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange); font-size: 15px;">
              ${window.EMCUtils.formatarMoeda(orc.valor_total || orc.valor_bruto)}
            </td>
            <td style="text-align: right; white-space: nowrap;">
              ${(orc.status_operacional === 'GERADO' || orc.status_operacional === 'ENVIADO') ? `
                <button class="btn btn-sm" style="background-color: #2e7d32; color: #fff; margin-right: 4px;" onclick="window.OrcamentosView.transitarStatus(${orc.id}, 'aprovar', 'Aprovado')" title="Aprovar Orçamento">APROVAR</button>
              ` : ''}
              <button class="btn btn-primary btn-sm" onclick="window.OrcamentosView.baixarPdf(${orc.id})">PDF</button>
              <button class="btn btn-secondary btn-sm" onclick="window.OrcamentosView.verDetalhes(${orc.id})">DETALHES</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalNovoOrcamento() {
    // Carrega clientes, equipamentos, produtos e itens para a montagem
    const [clientes, equipamentos, produtos, itens] = await Promise.all([
      window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?page_size=1000`),
      window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}?page_size=1000`),
      window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS}?page_size=1000`),
      window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.ITENS}?page_size=1000`)
    ]);

    let todosClientes = clientes.results || clientes || [];
    // Filtra apenas clientes (exclui fornecedores puros)
    let listaClientes = todosClientes.filter(c => (c.tipo || '').toUpperCase() !== 'FORNECEDOR');
    let listaEquip = equipamentos.results || equipamentos || [];
    let listaProd = produtos.results || produtos || [];
    let listaItens = itens.results || itens || [];

    let optionsCli = '<option value="">SELECIONE O CLIENTE...</option>';
    listaClientes.forEach((c) => {
      const doc = c.cnpj_cpf ? ` (${window.EMCUtils.formatarCpfCnpjDinamico(c.cnpj_cpf)})` : '';
      optionsCli += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome_razao)}${doc}</option>`;
    });

    const montarOptionsEquip = (clienteIdFiltro = null) => {
      let opts = '<option value="">SEM EQUIPAMENTO ESPECÍFICO (OFICINA GERAL)</option>';
      let equipsFiltrados = listaEquip;

      if (clienteIdFiltro) {
        equipsFiltrados = listaEquip.filter(e => e.cliente_atual?.id == Number(clienteIdFiltro));
      }

      if (equipsFiltrados.length === 0 && clienteIdFiltro) {
        opts += '<option value="" disabled>-- NENHUM VEÍCULO VINCULADO A ESTE CLIENTE --</option>';
      } else {
        equipsFiltrados.forEach((e) => {
          const placa = (e.placa && e.placa !== 'null' && e.placa !== 'None') ? ` [${window.EMCUtils.formatarPlacaVeiculo(e.placa)}]` : '';
          const ident = (e.identificacao && e.identificacao !== 'null' && e.identificacao !== 'None') ? ` - ${e.identificacao}` : '';
          const dono = (!clienteIdFiltro && e.cliente_atual?.nome_razao) ? ` (Proprietário: ${e.cliente_atual.nome_razao})` : '';
          opts += `<option value="${e.id}">${window.EMCUtils.escapeHtml(e.descricao)}${placa}${ident}${dono}</option>`;
        });
      }
      return opts;
    };

    let optionsProd = '<option value="">SELECIONE UM PRODUTO BOM...</option>';
    listaProd.forEach((p) => {
      optionsProd += `<option value="${p.id}" data-preco="${p.preco_custo_apurado}">${window.EMCUtils.escapeHtml(p.nome)} (${window.EMCUtils.formatarMoeda(p.preco_custo_apurado)})</option>`;
    });

    let optionsItens = '<option value="">SELECIONE UM INSUMO DIRETO...</option>';
    listaItens.forEach((it) => {
      optionsItens += `<option value="${it.id}" data-preco="${it.ultimo_custo_compra}">${window.EMCUtils.escapeHtml(it.nome)}</option>`;
    });

    this.orcItensTemp = [];

    window.EMCUtils.openModal({
      title: 'ELABORAÇÃO ÁGIL DE ORÇAMENTO',
      size: 'xl',
      confirmText: 'GERAR ORÇAMENTO',
      content: `
        <form id="form-novo-orcamento">
          <!-- Cabeçalho do Orçamento -->
          <div style="display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) 140px; gap: 12px; margin-bottom: 16px;">
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; justify-content: space-between; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="orc-cliente" style="margin-bottom: 0;">Cliente *</label>
              </div>
              <select id="orc-cliente" class="form-control" required>${optionsCli}</select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; justify-content: space-between; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="orc-equipamento" style="margin-bottom: 0;">Equipamento Padrão / Sugerido (Opcional)</label>
              </div>
              <select id="orc-equipamento" class="form-control">${montarOptionsEquip()}</select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; justify-content: space-between; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="orc-validade-dias" style="margin-bottom: 0;">Validade (Dias)</label>
              </div>
              <input type="number" id="orc-validade-dias" class="form-control mono-text" value="15" required>
            </div>
          </div>

          <div id="inadimplencia-alerta-box" class="alert-banner alert-danger" style="display: none;"></div>

          <!-- Montador de Itens do Orçamento (3 Tipos) -->
          <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <h4 style="font-size: 14px;">INSERIR LINHA DE ORÇAMENTO (PRODUTO BOM / INSUMO / TEXTO LIVRE)</h4>
              <div style="display: flex; gap: 8px;">
                <label style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                  <input type="radio" name="tipo_item_radio" value="PRODUTO" checked> Produto BOM
                </label>
                <label style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                  <input type="radio" name="tipo_item_radio" value="ITEM"> Insumo Direto
                </label>
                <label style="font-size: 12px; display: flex; align-items: center; gap: 4px; cursor: pointer;">
                  <input type="radio" name="tipo_item_radio" value="LIVRE"> Lançamento Livre
                </label>
              </div>
            </div>

            <!-- Seletor do Equipamento do Item -->
            <div style="display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 12px; align-items: flex-end; margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px dashed var(--color-outline-variant);">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" for="sel-item-equip-id" style="margin-bottom: 4px; font-weight: 600;">
                  Equipamento / Veículo deste Item (Opcional):
                </label>
                <select id="sel-item-equip-id" class="form-control">${montarOptionsEquip()}</select>
              </div>
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); padding-bottom: 6px;">
                * Permite vincular veículos diferentes para cada serviço/peça deste orçamento.
              </div>
            </div>

            <!-- Seletor dinâmico baseado no tipo -->
            <div id="seletor-produto-container" style="display: grid; grid-template-columns: minmax(0, 2fr) 100px 140px 140px auto; gap: 8px; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Produto Composto</label>
                <select id="sel-produto-id" class="form-control">${optionsProd}</select>
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Qtd</label>
                <input type="number" step="0.01" id="sel-prod-qtd" class="form-control mono-text" value="1.00">
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Custo Base (Snapshot)</label>
                <input type="text" id="sel-prod-custo" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00" readonly>
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Valor de Venda</label>
                <input type="text" id="sel-prod-venda" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
              </div>
              <button type="button" class="btn btn-secondary" id="btn-add-orc-item" style="height: 42px;">+ INSERIR</button>
            </div>

            <div id="seletor-item-container" style="display: none; grid-template-columns: minmax(0, 2fr) 100px 140px 140px auto; gap: 8px; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Insumo / Material</label>
                <select id="sel-item-id" class="form-control">${optionsItens}</select>
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Qtd</label>
                <input type="number" step="0.01" id="sel-item-qtd" class="form-control mono-text" value="1.00">
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Custo Base (Snapshot)</label>
                <input type="text" id="sel-item-custo" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00" readonly>
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Valor de Venda</label>
                <input type="text" id="sel-item-venda" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
              </div>
              <button type="button" class="btn btn-secondary" id="btn-add-orc-insumo" style="height: 42px;">+ INSERIR</button>
            </div>

            <div id="seletor-livre-container" style="display: none; grid-template-columns: minmax(0, 2fr) 100px 140px 140px auto; gap: 8px; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Descrição do Serviço / Peça</label>
                <input type="text" id="sel-livre-desc" class="form-control" placeholder="EX: SOLDA ESPECIAL TIG EM EIXO">
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Qtd</label>
                <input type="number" step="0.01" id="sel-livre-qtd" class="form-control mono-text" value="1.00">
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Custo Estimado</label>
                <input type="text" id="sel-livre-custo" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Valor de Venda</label>
                <input type="text" id="sel-livre-venda" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
              </div>
              <button type="button" class="btn btn-secondary" id="btn-add-orc-livre" style="height: 42px;">+ INSERIR</button>
            </div>
          </div>

          <!-- Tabela de Itens Inseridos -->
          <div class="table-container mb-16">
            <table class="table">
              <thead>
                <tr>
                  <th>TIPO</th>
                  <th>VEÍCULO / EQUIPAMENTO</th>
                  <th>DESCRIÇÃO / ESPECIFICAÇÃO</th>
                  <th>QUANTIDADE</th>
                  <th>CUSTO BASE (SNAP)</th>
                  <th>VALOR VENDA</th>
                  <th>SUBTOTAL</th>
                  <th style="text-align: right;">AÇÃO</th>
                </tr>
              </thead>
              <tbody id="orc-itens-grid-tbody">
                <tr><td colspan="8" class="text-center mono-text" style="padding: 16px;">Nenhum item inserido no orçamento.</td></tr>
              </tbody>
            </table>
          </div>

          <!-- Rodapé do Orçamento -->
          <div style="display: flex; justify-content: space-between; align-items: center; background-color: var(--color-surface-container-low); padding: 16px; border: 1px solid var(--color-steel-gray);">
            <div style="display: flex; gap: 16px; align-items: center;">
              <div>
                <span class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">DESCONTO COMERCIAL (R$):</span>
                <input type="text" id="orc-desconto-input" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00" style="width: 140px; height: 36px; margin-top: 4px;">
              </div>
              <div>
                <span class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">MARGEM DE LUCRO:</span>
                <div class="mono-text" id="orc-margem-display" style="font-size: 14px; font-weight: 700; color: var(--color-success); margin-top: 8px;">0.00 %</div>
              </div>
            </div>

            <div style="text-align: right;">
              <span class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">VALOR TOTAL FINAL:</span>
              <div class="mono-text" id="orc-total-final-display" style="font-size: 24px; font-weight: 700; color: var(--color-rust-orange);">R$ 0,00</div>
            </div>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const clienteVal = document.getElementById('orc-cliente')?.value;
        const cliente_id = clienteVal ? parseInt(clienteVal, 10) : null;
        const equipVal = document.getElementById('orc-equipamento')?.value;
        const equipamento_id = equipVal ? parseInt(equipVal, 10) : null;
        const validade_dias = parseInt(document.getElementById('orc-validade-dias')?.value, 10) || 15;
        const valor_desconto_aplicado = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('orc-desconto-input')?.value);

        if (!cliente_id) {
          window.EMCUtils.showToast('Selecione um cliente para o orçamento.', 'error');
          return false;
        }

        if (!this.orcItensTemp.length) {
          window.EMCUtils.showToast('Insira ao menos um item no orçamento.', 'warning');
          return false;
        }

        // Calcula a data de validade (hoje + validade_dias) no formato YYYY-MM-DD
        const dataValidadeObj = new Date();
        dataValidadeObj.setDate(dataValidadeObj.getDate() + validade_dias);
        const data_validade = dataValidadeObj.toISOString().split('T')[0];

        try {
          const payload = {
            cliente: cliente_id,
            cliente_id: cliente_id,
            equipamento: equipamento_id,
            equipamento_id: equipamento_id,
            validade_dias: validade_dias,
            data_validade: data_validade,
            valor_desconto_aplicado: valor_desconto_aplicado,
            itens: this.orcItensTemp.map(it => {
              const pId = it.produto_id ? parseInt(it.produto_id, 10) : null;
              const iId = it.item_id ? parseInt(it.item_id, 10) : null;
              const eqId = it.equipamento_id ? parseInt(it.equipamento_id, 10) : null;
              return {
                equipamento: eqId,
                equipamento_id: eqId,
                produto: pId,
                produto_id: pId,
                item: iId,
                item_id: iId,
                descricao_livre: it.descricao_livre || null,
                quantidade: parseFloat(it.quantidade),
                custo_snapshot: parseFloat(it.custo_snapshot || 0),
                valor_venda_snapshot: parseFloat(it.valor_venda_snapshot || 0)
              };
            })
          };

          const res = await window.api.post(window.CONFIG.ENDPOINTS.ORCAMENTOS.LISTA, payload);
          window.EMCUtils.showToast(`Orçamento #${res.id} gerado com sucesso!`, 'success');
          this.carregarListaOrcamentos();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao gerar orçamento.', 'error');
          return false;
        }
      }
    });

    // Inicializa Comboboxes com Autocomplete Pesquisável
    setTimeout(() => {
      const selCli = document.getElementById('orc-cliente');
      const selEq = document.getElementById('orc-equipamento');
      const selEqItem = document.getElementById('sel-item-equip-id');
      const selProd = document.getElementById('sel-produto-id');
      const selItem = document.getElementById('sel-item-id');

      const dispararCadastroNovoEquipamento = () => {
        const clienteAtualId = selCli?.value ? parseInt(selCli.value, 10) : null;
        window.CadastrosView.abrirModalEquipamento(null, clienteAtualId, {
          onSuccess: async (novoEquip) => {
            if (!novoEquip || !novoEquip.id) return;
            try {
              // Recarrega a lista de equipamentos do servidor
              const resEq = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}?page_size=1000`);
              listaEquip = resEq.results || resEq || [];

              // Se o orçamento estava sem cliente selecionado e o equipamento foi vinculado a um cliente, seleciona o cliente também
              const clienteVinculadoId = novoEquip.cliente_atual?.id || (typeof novoEquip.cliente_atual === 'number' ? novoEquip.cliente_atual : null) || novoEquip.cliente_id;
              if (selCli && !selCli.value && clienteVinculadoId) {
                if (selCli._emcCombobox) {
                  selCli._emcCombobox.setValue(clienteVinculadoId);
                } else {
                  selCli.value = clienteVinculadoId;
                  selCli.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }

              // Re-monta as options de equipamentos para o cliente ativo
              const clienteIdAtual = selCli?.value || null;
              const novasOptions = montarOptionsEquip(clienteIdAtual);

              if (selEq) {
                if (selEq._emcCombobox) {
                  selEq._emcCombobox.updateOptions(novasOptions, novoEquip.id);
                } else {
                  selEq.innerHTML = novasOptions;
                  selEq.value = String(novoEquip.id);
                }
              }

              if (selEqItem) {
                if (selEqItem._emcCombobox) {
                  selEqItem._emcCombobox.updateOptions(novasOptions, novoEquip.id);
                } else {
                  selEqItem.innerHTML = novasOptions;
                  selEqItem.value = String(novoEquip.id);
                }
              }

              window.EMCUtils.showToast(`Equipamento "${novoEquip.descricao}" cadastrado e selecionado com sucesso!`, 'success');
            } catch (err) {
              console.error('Erro ao atualizar equipamentos no orçamento:', err);
            }
          }
        });
      };

      const dispararCadastroNovoCliente = () => {
        window.CadastrosView.abrirModalCadastroRapido({
          tipoPredefinido: 'CLIENTE',
          onSuccess: async (novoCli) => {
            try {
              const resClientes = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?limit=1000`);
              const listaClientesAtualizada = resClientes.results || resClientes || [];
              todosClientes = listaClientesAtualizada;
              listaClientes = todosClientes.filter(c => (c.tipo || '').toUpperCase() !== 'FORNECEDOR');
              listaClientes.sort((a, b) => (a.nome_razao || '').localeCompare(b.nome_razao || ''));

              let novasOptionsCli = '<option value="">SELECIONE UM CLIENTE...</option>';
              listaClientes.forEach((c) => {
                const doc = c.cnpj_cpf ? ` (${window.EMCUtils.formatarCpfCnpjDinamico(c.cnpj_cpf)})` : '';
                novasOptionsCli += `<option value="${c.id}" ${c.id === novoCli.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(c.nome_razao)}${doc}</option>`;
              });

              if (selCli) {
                if (selCli._emcCombobox) {
                  selCli._emcCombobox.updateOptions(novasOptionsCli, novoCli.id);
                } else {
                  selCli.innerHTML = novasOptionsCli;
                  selCli.value = novoCli.id;
                  selCli.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
              window.EMCUtils.showToast(`Cliente "${novoCli.nome_razao}" cadastrado e selecionado!`, 'success');
            } catch (errCli) {
              console.error('Erro ao atualizar clientes no orçamento:', errCli);
            }
          }
        });
      };

      const dispararCadastroNovoProduto = () => {
        window.CatalogoView.abrirModalProduto(null, {
          onSuccess: async (novoProd) => {
            try {
              const resProd = await window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS);
              const listaProdAtualizada = resProd.results || resProd || [];
              listaProd = listaProdAtualizada;
              listaProd.sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));

              let novasOptionsProd = '<option value="">SELECIONE UM PRODUTO BOM...</option>';
              listaProd.forEach((p) => {
                novasOptionsProd += `<option value="${p.id}" data-preco="${p.preco_custo_apurado}" ${p.id === novoProd.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(p.nome)} (${window.EMCUtils.formatarMoeda(p.preco_custo_apurado)})</option>`;
              });

              if (selProd) {
                if (selProd._emcCombobox) {
                  selProd._emcCombobox.updateOptions(novasOptionsProd, novoProd.id);
                } else {
                  selProd.innerHTML = novasOptionsProd;
                  selProd.value = novoProd.id;
                  selProd.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
              window.EMCUtils.showToast(`Produto "${novoProd.nome}" cadastrado e selecionado!`, 'success');
            } catch (errProd) {
              console.error('Erro ao atualizar produtos no orçamento:', errProd);
            }
          }
        });
      };

      const dispararCadastroNovoInsumo = () => {
        window.CatalogoView.abrirModalItem(null, {
          onSuccess: async (novoItem) => {
            try {
              const resItens = await window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.ITENS);
              const listaItensAtualizada = resItens.results || resItens || [];
              listaItens = listaItensAtualizada;
              listaItens.sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));

              let novasOptionsItens = '<option value="">SELECIONE UM INSUMO DIRETO...</option>';
              listaItens.forEach((it) => {
                novasOptionsItens += `<option value="${it.id}" data-preco="${it.ultimo_custo_compra}" ${it.id === novoItem.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(it.nome)}</option>`;
              });

              if (selItem) {
                if (selItem._emcCombobox) {
                  selItem._emcCombobox.updateOptions(novasOptionsItens, novoItem.id);
                } else {
                  selItem.innerHTML = novasOptionsItens;
                  selItem.value = novoItem.id;
                  selItem.dispatchEvent(new Event('change', { bubbles: true }));
                }
              }
              window.EMCUtils.showToast(`Insumo "${novoItem.nome}" cadastrado e selecionado!`, 'success');
            } catch (errIt) {
              console.error('Erro ao atualizar insumos no orçamento:', errIt);
            }
          }
        });
      };

      if (selCli) {
        window.EMCUtils.initSearchableSelect(selCli, { 
          placeholder: 'SELECIONE OU BUSQUE O CLIENTE...',
          action: {
            label: '+ CADASTRAR NOVO CLIENTE',
            permission: 'acesso_comercial',
            onClick: () => dispararCadastroNovoCliente()
          }
        });
      }

      if (selEq) {
        window.EMCUtils.initSearchableSelect(selEq, { 
          placeholder: 'TODOS OU PESQUISE O VEÍCULO...',
          action: {
            label: '+ CADASTRAR NOVO EQUIPAMENTO',
            permission: 'acesso_comercial',
            onClick: () => dispararCadastroNovoEquipamento()
          }
        });
      }

      if (selEqItem) {
        window.EMCUtils.initSearchableSelect(selEqItem, { 
          placeholder: 'HERDAR DO ORÇAMENTO OU SELECIONAR VEÍCULO...',
          action: {
            label: '+ CADASTRAR NOVO EQUIPAMENTO',
            permission: 'acesso_comercial',
            onClick: () => dispararCadastroNovoEquipamento()
          }
        });
      }

      if (selProd) {
        window.EMCUtils.initSearchableSelect(selProd, { 
          placeholder: 'PESQUISE UM PRODUTO BOM...',
          action: {
            label: '+ CADASTRAR NOVO PRODUTO BOM',
            permission: 'gestao_catalogo',
            onClick: () => dispararCadastroNovoProduto()
          }
        });
      }

      if (selItem) {
        window.EMCUtils.initSearchableSelect(selItem, { 
          placeholder: 'PESQUISE UM INSUMO...',
          action: {
            label: '+ CADASTRAR NOVO INSUMO',
            permission: 'gestao_catalogo',
            onClick: () => dispararCadastroNovoInsumo()
          }
        });
      }

      // Ao trocar de cliente, re-filtra dinamicamente a combobox de equipamentos
      selCli?.addEventListener('change', async (e) => {
        const clienteId = e.target.value;
        const novasOpts = montarOptionsEquip(clienteId || null);
        if (selEq) {
          if (selEq._emcCombobox) {
            selEq._emcCombobox.updateOptions(novasOpts);
          } else {
            selEq.innerHTML = novasOpts;
            selEq.value = '';
          }
        }
        if (selEqItem) {
          if (selEqItem._emcCombobox) {
            selEqItem._emcCombobox.updateOptions(novasOpts);
          } else {
            selEqItem.innerHTML = novasOpts;
            selEqItem.value = '';
          }
        }

        // Checagem de inadimplência preventiva
        if (clienteId) {
          try {
            const analise = await window.api.get(`${window.CONFIG.ENDPOINTS.RELATORIOS.INADIMPLENCIA}?cliente_id=${clienteId}`);
            const alertaBox = document.getElementById('inadimplencia-alerta-box');
            if (analise && analise.tem_pendencias && alertaBox) {
              alertaBox.style.display = 'block';
              alertaBox.innerHTML = `<strong>[ALERTA DE RISCO]</strong> Este cliente possui títulos vencidos no total de ${window.EMCUtils.formatarMoeda(analise.valor_total_vencido)}.`;
            } else if (alertaBox) {
              alertaBox.style.display = 'none';
            }
          } catch (err) {
            // Silencioso
          }
        }
      });

      // Sincroniza equipamento do cabeçalho com o do item (se item ainda estiver vazio ou seguir o padrão)
      selEq?.addEventListener('change', (e) => {
        const eqId = e.target.value;
        if (selEqItem) {
          if (selEqItem._emcCombobox) {
            selEqItem._emcCombobox.setValue(eqId);
          } else {
            selEqItem.value = eqId;
          }
        }
      });
    }, 50);

    // Controle dos radio buttons de seleção de tipo
    document.querySelectorAll('input[name="tipo_item_radio"]').forEach((r) => {
      r.addEventListener('change', (e) => {
        const val = e.target.value;
        document.getElementById('seletor-produto-container').style.display = val === 'PRODUTO' ? 'grid' : 'none';
        document.getElementById('seletor-item-container').style.display = val === 'ITEM' ? 'grid' : 'none';
        document.getElementById('seletor-livre-container').style.display = val === 'LIVRE' ? 'grid' : 'none';
      });
    });

    // Auto-preenchimento de custos ao selecionar produto ou item
    document.getElementById('sel-produto-id')?.addEventListener('change', (e) => {
      const opt = e.target.selectedOptions[0];
      const preco = parseFloat(opt?.dataset.preco) || 0;
      document.getElementById('sel-prod-custo').value = window.EMCUtils.formatarMoeda(preco);
      document.getElementById('sel-prod-venda').value = window.EMCUtils.formatarMoeda(preco * 1.4); // sugestão 40% margem
    });

    document.getElementById('sel-item-id')?.addEventListener('change', (e) => {
      const opt = e.target.selectedOptions[0];
      const preco = parseFloat(opt?.dataset.preco) || 0;
      document.getElementById('sel-item-custo').value = window.EMCUtils.formatarMoeda(preco);
      document.getElementById('sel-item-venda').value = window.EMCUtils.formatarMoeda(preco * 1.5);
    });

    // Helper para capturar o equipamento selecionado para a linha
    const obterEquipItemAtual = () => {
      const selEqItem = document.getElementById('sel-item-equip-id');
      const selEqCabecalho = document.getElementById('orc-equipamento');
      let equipId = selEqItem?.value ? parseInt(selEqItem.value, 10) : null;
      let equipDisplay = '';

      if (!equipId && selEqCabecalho?.value) {
        equipId = parseInt(selEqCabecalho.value, 10);
      }

      if (equipId) {
        const found = (listaEquip || []).find(e => e.id === equipId);
        if (found) {
          equipDisplay = `${found.placa ? `[${found.placa}] ` : ''}${found.descricao}`;
        } else {
          equipDisplay = `Equipamento #${equipId}`;
        }
      } else {
        equipDisplay = '-';
      }

      return { equipId, equipDisplay };
    };

    // Botões de inserção
    document.getElementById('btn-add-orc-item')?.addEventListener('click', () => {
      const sel = document.getElementById('sel-produto-id');
      const produto_id = sel.value;
      const nome = sel.options[sel.selectedIndex]?.text || 'Produto';
      const quantidade = parseFloat(document.getElementById('sel-prod-qtd').value) || 1;
      const custo_snapshot = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sel-prod-custo').value);
      const valor_venda_snapshot = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sel-prod-venda').value);

      if (!produto_id || valor_venda_snapshot <= 0) {
        window.EMCUtils.showToast('Selecione um produto e defina o valor de venda.', 'warning');
        return;
      }

      const { equipId, equipDisplay } = obterEquipItemAtual();

      this.orcItensTemp.push({
        tipo: 'PRODUTO',
        equipamento_id: equipId,
        equipamento_display: equipDisplay,
        produto_id,
        descricao: nome,
        quantidade,
        custo_snapshot,
        valor_venda_snapshot
      });

      this.atualizarGridOrcItens();
    });

    document.getElementById('btn-add-orc-insumo')?.addEventListener('click', () => {
      const sel = document.getElementById('sel-item-id');
      const item_id = sel.value;
      const nome = sel.options[sel.selectedIndex]?.text || 'Insumo';
      const quantidade = parseFloat(document.getElementById('sel-item-qtd').value) || 1;
      const custo_snapshot = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sel-item-custo').value);
      const valor_venda_snapshot = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sel-item-venda').value);

      if (!item_id || valor_venda_snapshot <= 0) {
        window.EMCUtils.showToast('Selecione um insumo e defina o valor de venda.', 'warning');
        return;
      }

      const { equipId, equipDisplay } = obterEquipItemAtual();

      this.orcItensTemp.push({
        tipo: 'ITEM',
        equipamento_id: equipId,
        equipamento_display: equipDisplay,
        item_id,
        descricao: nome,
        quantidade,
        custo_snapshot,
        valor_venda_snapshot
      });

      this.atualizarGridOrcItens();
    });

    document.getElementById('btn-add-orc-livre')?.addEventListener('click', () => {
      const descricao_livre = document.getElementById('sel-livre-desc').value.trim();
      const quantidade = parseFloat(document.getElementById('sel-livre-qtd').value) || 1;
      const custo_snapshot = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sel-livre-custo').value);
      const valor_venda_snapshot = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sel-livre-venda').value);

      if (!descricao_livre || valor_venda_snapshot <= 0) {
        window.EMCUtils.showToast('Digite a descrição e defina o valor de venda.', 'warning');
        return;
      }

      const { equipId, equipDisplay } = obterEquipItemAtual();

      this.orcItensTemp.push({
        tipo: 'LIVRE',
        equipamento_id: equipId,
        equipamento_display: equipDisplay,
        descricao_livre,
        descricao: descricao_livre,
        quantidade,
        custo_snapshot,
        valor_venda_snapshot
      });

      this.atualizarGridOrcItens();
      document.getElementById('sel-livre-desc').value = '';
    });

    document.getElementById('orc-desconto-input')?.addEventListener('input', () => this.atualizarGridOrcItens());
  },

  atualizarGridOrcItens() {
    const tbody = document.getElementById('orc-itens-grid-tbody');
    const totalFinalEl = document.getElementById('orc-total-final-display');
    const margemEl = document.getElementById('orc-margem-display');
    if (!tbody) return;

    if (!this.orcItensTemp.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="text-center mono-text" style="padding: 16px;">Nenhum item inserido no orçamento.</td></tr>';
      if (totalFinalEl) totalFinalEl.textContent = 'R$ 0,00';
      if (margemEl) margemEl.textContent = '0.00 %';
      return;
    }

    let totalVenda = 0;
    let totalCusto = 0;
    let html = '';

    this.orcItensTemp.forEach((it, idx) => {
      const sub = it.quantidade * it.valor_venda_snapshot;
      const subCusto = it.quantidade * it.custo_snapshot;
      totalVenda += sub;
      totalCusto += subCusto;

      const badgeTipo = it.tipo === 'PRODUTO' ? 'info' : (it.tipo === 'ITEM' ? 'warning' : 'success');
      const eqTexto = it.equipamento_display && it.equipamento_display !== '-'
        ? `<span class="mono-text" style="font-weight: 600; font-size: 11px; color: var(--color-on-surface);"><i class="ph-bold ph-truck" style="color: var(--color-rust-orange);"></i> ${window.EMCUtils.escapeHtml(it.equipamento_display)}</span>`
        : `<span class="mono-text" style="color: var(--color-on-surface-variant); font-size: 11px;">[PADRÃO]</span>`;

      html += `
        <tr>
          <td><span class="status-chip ${badgeTipo}">${it.tipo}</span></td>
          <td>${eqTexto}</td>
          <td><strong>${window.EMCUtils.escapeHtml(it.descricao)}</strong></td>
          <td class="mono-text">${it.quantidade.toFixed(2)}</td>
          <td class="mono-text">${window.EMCUtils.formatarMoeda(it.custo_snapshot)}</td>
          <td class="mono-text">${window.EMCUtils.formatarMoeda(it.valor_venda_snapshot)}</td>
          <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(sub)}</td>
          <td style="text-align: right;">
            <button type="button" class="btn btn-danger btn-sm" onclick="window.OrcamentosView.removerOrcItemTemp(${idx})">X</button>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;

    const desconto = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('orc-desconto-input')?.value || '0');
    const valorLiquido = Math.max(0, totalVenda - desconto);
    const lucro = valorLiquido - totalCusto;
    const margem = valorLiquido > 0 ? ((lucro / valorLiquido) * 100) : 0;

    if (totalFinalEl) totalFinalEl.textContent = window.EMCUtils.formatarMoeda(valorLiquido);
    if (margemEl) {
      margemEl.textContent = `${margem.toFixed(2)} %`;
      margemEl.style.color = margem >= 30 ? 'var(--color-success)' : (margem > 0 ? 'var(--color-warning)' : 'var(--color-error)');
    }
  },

  removerOrcItemTemp(index) {
    if (this.orcItensTemp && this.orcItensTemp[index]) {
      this.orcItensTemp.splice(index, 1);
      this.atualizarGridOrcItens();
    }
  },

  async verDetalhes(orcId) {
    try {
      const orc = await window.api.get(`${window.CONFIG.ENDPOINTS.ORCAMENTOS.LISTA}${orcId}/`);
      const itens = orc.itens || [];

      let rows = '';
      itens.forEach((it) => {
        const sub = (parseFloat(it.quantidade) || 0) * (parseFloat(it.valor_venda_snapshot) || 0);
        const tipoBadge = it.tipo_item === 'PRODUTO' ? 'info' : (it.tipo_item === 'ITEM' ? 'warning' : 'success');
        const eqBadge = it.equipamento_display
          ? `<span class="mono-text" style="font-weight: 600; font-size: 11px;"><i class="ph-bold ph-truck" style="color: var(--color-rust-orange);"></i> ${window.EMCUtils.escapeHtml(it.equipamento_display)}</span>`
          : `<span class="mono-text" style="color: var(--color-on-surface-variant); font-size: 11px;">${window.EMCUtils.escapeHtml(orc.equipamento_descricao || '-')}</span>`;

        rows += `
          <tr>
            <td><span class="status-chip ${tipoBadge}">${it.tipo_item || 'ITEM'}</span></td>
            <td>${eqBadge}</td>
            <td><strong>${window.EMCUtils.escapeHtml(it.produto_nome || it.item_nome || it.descricao_livre || 'Item')}</strong></td>
            <td class="mono-text">${parseFloat(it.quantidade).toFixed(2)}</td>
            <td class="mono-text">${window.EMCUtils.formatarMoeda(it.custo_snapshot)}</td>
            <td class="mono-text">${window.EMCUtils.formatarMoeda(it.valor_venda_snapshot)}</td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(sub)}</td>
          </tr>
        `;
      });

      const badgeOpModal = {
        GERADO: 'info',
        ENVIADO: 'info',
        APROVADO: 'success',
        EM_EXECUCAO: 'warning',
        CONCLUIDO: 'success',
        CANCELADO: 'danger'
      }[orc.status_operacional] || 'info';

      const badgeFinModal = {
        A_FATURAR: 'warning',
        FATURADO: 'info',
        PAGO: 'success',
        CANCELADO: 'danger'
      }[orc.status_financeiro] || 'info';

      const statusOpTextoModal = orc.status_operacional_display || window.EMCUtils.formatarStatus(orc.status_operacional);
      const statusFinTextoModal = orc.status_financeiro_display || window.EMCUtils.formatarStatus(orc.status_financeiro);

      // Definição das etapas da esteira operacional
      const etapas = [
        { key: 'GERADO', label: 'GERADO', cor: 'var(--color-surface-container-highest)' },
        { key: 'ENVIADO', label: 'ENVIADO', cor: '#71797E' },
        { key: 'APROVADO', label: 'APROVADO', cor: '#2e7d32' },
        { key: 'EM_EXECUCAO', label: 'EM EXECUÇÃO', cor: 'var(--color-rust-orange)' },
        { key: 'CONCLUIDO', label: 'CONCLUÍDO', cor: '#1b5e20' }
      ];

      const indexAtual = etapas.findIndex(e => e.key === orc.status_operacional);

      let botoesEtapas = '';
      etapas.forEach((e) => {
        const isAtual = e.key === orc.status_operacional;
        if (isAtual) {
          botoesEtapas += `
            <button type="button" class="btn btn-sm" style="background-color: ${e.cor}; color: #fff; font-weight: 700; border: 2px solid var(--color-on-surface); box-shadow: 0 0 6px rgba(0,0,0,0.4); cursor: default;" title="Status Atual">
              ● ${e.label}
            </button>
          `;
        } else {
          botoesEtapas += `
            <button type="button" class="btn btn-secondary btn-sm" onclick="window.OrcamentosView.mudarStatusOperacional(${orc.id}, '${e.key}', '${e.label}')" title="Mudar diretamente para ${e.label}" style="opacity: 0.85;">
              ${e.label}
            </button>
          `;
        }
      });

      let botaoVoltar = '';
      let botaoAvancar = '';

      if (indexAtual > 0 && orc.status_operacional !== 'CANCELADO') {
        const anterior = etapas[indexAtual - 1];
        botaoVoltar = `
          <button type="button" class="btn btn-secondary btn-sm" onclick="window.OrcamentosView.mudarStatusOperacional(${orc.id}, '${anterior.key}', '${anterior.label}')" title="Retornar para ${anterior.label}">
            ◀ VOLTAR (${anterior.label})
          </button>
        `;
      }

      if (indexAtual >= 0 && indexAtual < etapas.length - 1 && orc.status_operacional !== 'CANCELADO') {
        const proximo = etapas[indexAtual + 1];
        botaoAvancar = `
          <button type="button" class="btn btn-primary btn-sm" style="background-color: #2e7d32; border-color: #2e7d32;" onclick="window.OrcamentosView.mudarStatusOperacional(${orc.id}, '${proximo.key}', '${proximo.label}')" title="Avançar para ${proximo.label}">
            AVANÇAR (${proximo.label}) ▶
          </button>
        `;
      }

      window.EMCUtils.openModal({
        title: `ORÇAMENTO #${orc.id} - ${orc.cliente_nome}`,
        size: 'lg',
        hideFooter: true,
        content: `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; font-size: 13px;">
            <div>
              • <strong>Cliente:</strong> ${window.EMCUtils.escapeHtml(orc.cliente_nome)}<br>
              ${(orc.equipamentos_envolvidos && orc.equipamentos_envolvidos.length > 1)
                ? `• <strong>Veículos / Equipamentos (${orc.equipamentos_envolvidos.length}):</strong> <span class="status-chip info mono-text" style="font-size: 11px;">${orc.equipamentos_envolvidos.map(e => window.EMCUtils.escapeHtml(e.display || (e.placa ? `[${e.placa}] ${e.descricao}` : e.descricao))).join(', ')}</span><br>`
                : `• <strong>Equipamento:</strong> ${window.EMCUtils.escapeHtml(orc.equipamento_descricao || '-')}<br>`
              }
              • <strong>Data Geração:</strong> ${window.EMCUtils.formatarDataPtBr(orc.data_geracao)}<br>
              • <strong>Validade:</strong> ${window.EMCUtils.formatarDataPtBr(orc.data_validade)}
            </div>
            <div>
              • <strong>Status Operacional:</strong> <span class="status-chip ${badgeOpModal}">${window.EMCUtils.escapeHtml(statusOpTextoModal)}</span><br>
              • <strong>Status Financeiro:</strong> <span class="status-chip ${badgeFinModal}">${window.EMCUtils.escapeHtml(statusFinTextoModal)}</span><br>
              • <strong>Desconto Comercial:</strong> ${window.EMCUtils.formatarMoeda(orc.valor_desconto_aplicado || 0)}<br>
              • <strong>Total do Orçamento:</strong> <span class="mono-text" style="font-weight: 700; color: var(--color-rust-orange); font-size: 16px;">${window.EMCUtils.formatarMoeda(orc.valor_total || orc.valor_bruto)}</span>
            </div>
          </div>

          <div class="table-container mb-16">
            <table class="table">
              <thead>
                <tr>
                  <th>TIPO</th>
                  <th>VEÍCULO / EQUIPAMENTO</th>
                  <th>ITEM / DESCRIÇÃO</th>
                  <th>QTD</th>
                  <th>CUSTO (SNAP)</th>
                  <th>VENDA (SNAP)</th>
                  <th>SUBTOTAL</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>

          <!-- Stepper de Transição Operacional -->
          <div class="card mb-16" style="background-color: var(--color-surface-container); padding: 14px 16px; border-left: 3px solid var(--color-rust-orange);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; margin-bottom: 10px;">
              <div>
                <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); text-transform: uppercase;">Fluxo Operacional (Clique no status para alterar):</span>
                <div style="font-size: 13px; font-weight: 700; margin-top: 2px;">
                  Status Atual: <span class="status-chip ${badgeOpModal}">${window.EMCUtils.escapeHtml(statusOpTextoModal)}</span>
                  ${(orc.status_operacional === 'APROVADO' || orc.status_operacional === 'EM_EXECUCAO' || orc.status_operacional === 'CONCLUIDO') ? `
                    <span class="status-chip success mono-text" style="font-size: 11px; margin-left: 6px;">ELEGÍVEL PARA FATURAMENTO NA CONTA CORRENTE</span>
                  ` : ''}
                </div>
              </div>
              <div style="display: flex; gap: 8px; align-items: center;">
                ${botaoVoltar}
                ${botaoAvancar}
              </div>
            </div>

            <!-- Barra de Seleção de Todos os Status (Ativo / Inativo) -->
            <div style="display: flex; gap: 6px; flex-wrap: wrap; align-items: center; padding-top: 8px; border-top: 1px solid var(--color-outline-variant);">
              <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); margin-right: 4px;">SELECIONAR:</span>
              ${botoesEtapas}
            </div>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; flex-wrap: wrap;">
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-primary" onclick="window.OrcamentosView.baixarPdf(${orc.id})">BAIXAR PDF</button>
              ${orc.status_operacional !== 'CANCELADO' ? `
                <button class="btn btn-secondary" onclick="window.OrcamentosView.renovarOrcamento(${orc.id})">RENOVAR VALIDADE</button>
              ` : ''}
            </div>

            ${orc.status_operacional !== 'CANCELADO' ? `
              <button class="btn btn-danger" onclick="window.OrcamentosView.abrirModalCancelar(${orc.id})">CANCELAR ORÇAMENTO</button>
            ` : ''}
          </div>
        `
      });
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar detalhes do orçamento.', 'error');
    }
  },

  async mudarStatusOperacional(orcId, novoStatus, label) {
    try {
      window.EMCUtils.showToast(`Atualizando status para ${label}...`, 'info');
      const endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.ALTERAR_STATUS_OPERACIONAL.replace('{id}', orcId);
      await window.api.post(endpoint, { novo_status: novoStatus });
      window.EMCUtils.showToast(`Status alterado para ${label} com sucesso!`, 'success');

      // Atualiza lista em segundo plano
      this.carregarListaOrcamentos();

      // Recarrega o modal na hora fechando e reabrindo instantaneamente
      window.EMCUtils.closeModal();
      await this.verDetalhes(orcId);
    } catch (err) {
      window.EMCUtils.showToast(err.message || `Erro ao alterar status para ${label}.`, 'error');
    }
  },

  async transitarStatus(orcId, acao, nomeLegivel) {
    try {
      let endpoint = '';
      if (acao === 'enviar') endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.ENVIAR.replace('{id}', orcId);
      else if (acao === 'aprovar') endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.APROVAR.replace('{id}', orcId);
      else if (acao === 'iniciar-execucao') endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.INICIAR_EXECUCAO.replace('{id}', orcId);
      else if (acao === 'concluir') endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.CONCLUIR.replace('{id}', orcId);

      window.EMCUtils.showToast(`Atualizando orçamento #${orcId}...`, 'info');
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast(`Orçamento #${orcId} atualizado para ${nomeLegivel} com sucesso!`, 'success');

      this.carregarListaOrcamentos();

      // Recarrega o modal na hora fechando e reabrindo instantaneamente
      window.EMCUtils.closeModal();
      await this.verDetalhes(orcId);
    } catch (err) {
      window.EMCUtils.showToast(err.message || `Erro ao atualizar orçamento para ${nomeLegivel}.`, 'error');
    }
  },

  async renovarOrcamento(orcId) {
    try {
      const endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.RENOVAR.replace('{id}', orcId);
      const res = await window.api.post(endpoint, {});

      if (res.inflacao_detectada) {
        window.EMCUtils.showToast(`Orçamento renovado! ALERTA DE INFLAÇÃO: Custo de insumos subiu em ${window.EMCUtils.formatarMoeda(res.diferenca_custo)}.`, 'warning', 6000);
      } else {
        window.EMCUtils.showToast('Validade do orçamento renovada com sucesso!', 'success');
      }

      this.carregarListaOrcamentos();
      window.EMCUtils.closeModal();
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao renovar orçamento.', 'error');
    }
  },

  abrirModalCancelar(orcId) {
    window.EMCUtils.openModal({
      title: `CANCELAR ORÇAMENTO #${orcId}`,
      size: 'sm',
      confirmText: 'CONFIRMAR CANCELAMENTO',
      content: `
        <p style="color: var(--color-on-surface-variant); font-size: 13px; margin-bottom: 12px;">
          O cancelamento de orçamentos exige compulsoriamente a digitação de uma justificativa formal (mínimo 10 caracteres).
        </p>
        <div class="form-group">
          <label class="form-label" for="cancelar-orc-motivo">Motivo do Cancelamento *</label>
          <textarea id="cancelar-orc-motivo" class="form-control" rows="3" placeholder="EX: CLIENTE DESISTIU DO SERVIÇO POR MOTIVOS ORÇAMENTÁRIOS" required autofocus></textarea>
        </div>
      `,
      onConfirm: async () => {
        const motivo_cancelamento = document.getElementById('cancelar-orc-motivo').value.trim();
        if (!motivo_cancelamento || motivo_cancelamento.length < 10) {
          window.EMCUtils.showToast('A justificativa deve conter no mínimo 10 caracteres.', 'warning');
          return false;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.CANCELAR.replace('{id}', orcId);
          await window.api.post(endpoint, { motivo_cancelamento });
          window.EMCUtils.showToast(`Orçamento #${orcId} cancelado com sucesso.`, 'info');
          this.carregarListaOrcamentos();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao cancelar orçamento.', 'error');
          return false;
        }
      }
    });
  },

  async baixarPdf(orcId) {
    try {
      window.EMCUtils.showToast('Gerando documento PDF industrial...', 'info');
      const endpoint = window.CONFIG.ENDPOINTS.ORCAMENTOS.GERAR_PDF.replace('{id}', orcId);
      await window.api.downloadFile(endpoint, `Orcamento_${orcId}.pdf`);
      window.EMCUtils.showToast('PDF baixado com sucesso!', 'success');
    } catch (e) {
      window.EMCUtils.showToast(e.message || 'Erro ao gerar PDF do orçamento.', 'error');
    }
  }
};
