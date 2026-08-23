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

        <button class="btn btn-primary" id="btn-novo-orcamento">+ NOVO ORÇAMENTO</button>
      </div>

      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <input type="text" id="filtro-orc-busca" class="form-control" placeholder="BUSCAR POR CLIENTE, EQUIPAMENTO OU ID..." style="max-width: 380px;">
          <select id="filtro-orc-status" class="form-control" style="width: 180px;">
            <option value="">TODOS OS STATUS</option>
            <option value="GERADO">GERADO</option>
            <option value="ENVIADO">ENVIADO</option>
            <option value="APROVADO">APROVADO</option>
            <option value="EM_EXECUCAO">EM EXECUÇÃO</option>
            <option value="CONCLUIDO">CONCLUÍDO</option>
            <option value="CANCELADO">CANCELADO</option>
          </select>
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

    document.getElementById('btn-novo-orcamento')?.addEventListener('click', () => this.abrirModalNovoOrcamento());
    document.getElementById('filtro-orc-busca')?.addEventListener('input', () => this.carregarListaOrcamentos());
    document.getElementById('filtro-orc-status')?.addEventListener('change', () => this.carregarListaOrcamentos());

    this.carregarListaOrcamentos();
  },

  async carregarListaOrcamentos() {
    const tbody = document.getElementById('lista-orc-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-orc-busca')?.value.trim() || '';
    const status = document.getElementById('filtro-orc-status')?.value || '';

    try {
      const query = new URLSearchParams();
      if (busca) query.append('search', busca);
      if (status) query.append('status_operacional', status);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.ORCAMENTOS.LISTA}?${query.toString()}`);
      const lista = res.results || res || [];

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

        html += `
          <tr>
            <td class="mono-text"><strong>#${orc.id}</strong></td>
            <td><strong>${window.EMCUtils.escapeHtml(orc.cliente_nome || 'Cliente')}</strong></td>
            <td>${window.EMCUtils.escapeHtml(orc.equipamento_descricao || 'Geral / Oficina')}</td>
            <td class="mono-text" style="font-size: 12px;">
              ${window.EMCUtils.formatarDataPtBr(orc.data_geracao)} ➔ ${window.EMCUtils.formatarDataPtBr(orc.data_validade)}
            </td>
            <td><span class="status-chip ${badgeOp}">${orc.status_operacional}</span></td>
            <td><span class="status-chip ${badgeFin}">${orc.status_financeiro}</span></td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange); font-size: 15px;">
              ${window.EMCUtils.formatarMoeda(orc.valor_total || orc.valor_bruto)}
            </td>
            <td style="text-align: right; white-space: nowrap;">
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
      window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES),
      window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS),
      window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS),
      window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.ITENS)
    ]);

    const listaClientes = clientes.results || clientes || [];
    const listaEquip = equipamentos.results || equipamentos || [];
    const listaProd = produtos.results || produtos || [];
    const listaItens = itens.results || itens || [];

    let optionsCli = '<option value="">SELECIONE O CLIENTE...</option>';
    listaClientes.forEach((c) => {
      optionsCli += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome_razao)}</option>`;
    });

    let optionsEq = '<option value="">SEM EQUIPAMENTO ESPECÍFICO (OFICINA GERAL)</option>';
    listaEquip.forEach((e) => {
      const placa = e.placa ? ` [${e.placa}]` : '';
      optionsEq += `<option value="${e.id}">${window.EMCUtils.escapeHtml(e.descricao)}${placa}</option>`;
    });

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
          <div style="display: grid; grid-template-columns: 2fr 1fr 140px; gap: 12px; margin-bottom: 16px;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="orc-cliente">Cliente *</label>
              <select id="orc-cliente" class="form-control" required>${optionsCli}</select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="orc-equipamento">Equipamento / Máquina</label>
              <select id="orc-equipamento" class="form-control">${optionsEq}</select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="orc-validade-dias">Validade (Dias)</label>
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

            <!-- Seletor dinâmico baseado no tipo -->
            <div id="seletor-produto-container" style="display: grid; grid-template-columns: 2fr 100px 140px 140px auto; gap: 8px; align-items: flex-end;">
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

            <div id="seletor-item-container" style="display: none; grid-template-columns: 2fr 100px 140px 140px auto; gap: 8px; align-items: flex-end;">
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

            <div id="seletor-livre-container" style="display: none; grid-template-columns: 2fr 100px 140px 140px auto; gap: 8px; align-items: flex-end;">
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
                  <th>DESCRIÇÃO / ESPECIFICAÇÃO</th>
                  <th>QUANTIDADE</th>
                  <th>CUSTO BASE (SNAP)</th>
                  <th>VALOR VENDA</th>
                  <th>SUBTOTAL</th>
                  <th style="text-align: right;">AÇÃO</th>
                </tr>
              </thead>
              <tbody id="orc-itens-grid-tbody">
                <tr><td colspan="7" class="text-center mono-text" style="padding: 16px;">Nenhum item inserido no orçamento.</td></tr>
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
        const cliente_id = document.getElementById('orc-cliente').value;
        const equipamento_id = document.getElementById('orc-equipamento').value || null;
        const validade_dias = parseInt(document.getElementById('orc-validade-dias').value, 10) || 15;
        const valor_desconto_aplicado = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('orc-desconto-input').value);

        if (!cliente_id) {
          window.EMCUtils.showToast('Selecione um cliente para o orçamento.', 'error');
          return false;
        }

        if (!this.orcItensTemp.length) {
          window.EMCUtils.showToast('Insira ao menos um item no orçamento.', 'warning');
          return false;
        }

        try {
          const payload = {
            cliente_id,
            equipamento_id,
            validade_dias,
            valor_desconto_aplicado,
            itens: this.orcItensTemp.map(it => ({
              produto_id: it.produto_id || null,
              item_id: it.item_id || null,
              descricao_livre: it.descricao_livre || null,
              quantidade: it.quantidade,
              custo_snapshot: it.custo_snapshot,
              valor_venda_snapshot: it.valor_venda_snapshot
            }))
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

      this.orcItensTemp.push({
        tipo: 'PRODUTO',
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

      this.orcItensTemp.push({
        tipo: 'ITEM',
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

      this.orcItensTemp.push({
        tipo: 'LIVRE',
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
      tbody.innerHTML = '<tr><td colspan="7" class="text-center mono-text" style="padding: 16px;">Nenhum item inserido no orçamento.</td></tr>';
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

      html += `
        <tr>
          <td><span class="status-chip ${badgeTipo}">${it.tipo}</span></td>
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
        rows += `
          <tr>
            <td><strong>${window.EMCUtils.escapeHtml(it.produto_nome || it.item_nome || it.descricao_livre || 'Item')}</strong></td>
            <td class="mono-text">${parseFloat(it.quantidade).toFixed(2)}</td>
            <td class="mono-text">${window.EMCUtils.formatarMoeda(it.custo_snapshot)}</td>
            <td class="mono-text">${window.EMCUtils.formatarMoeda(it.valor_venda_snapshot)}</td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(sub)}</td>
          </tr>
        `;
      });

      window.EMCUtils.openModal({
        title: `ORÇAMENTO #${orc.id} - ${orc.cliente_nome}`,
        size: 'lg',
        hideFooter: true,
        content: `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; font-size: 13px;">
            <div>
              • <strong>Cliente:</strong> ${window.EMCUtils.escapeHtml(orc.cliente_nome)}<br>
              • <strong>Equipamento:</strong> ${window.EMCUtils.escapeHtml(orc.equipamento_descricao || '-')}<br>
              • <strong>Data Geração:</strong> ${window.EMCUtils.formatarDataPtBr(orc.data_geracao)}<br>
              • <strong>Validade:</strong> ${window.EMCUtils.formatarDataPtBr(orc.data_validade)}
            </div>
            <div>
              • <strong>Status Operacional:</strong> <span class="status-chip info">${orc.status_operacional}</span><br>
              • <strong>Status Financeiro:</strong> <span class="status-chip warning">${orc.status_financeiro}</span><br>
              • <strong>Desconto Comercial:</strong> ${window.EMCUtils.formatarMoeda(orc.valor_desconto_aplicado || 0)}<br>
              • <strong>Total do Orçamento:</strong> <span class="mono-text" style="font-weight: 700; color: var(--color-rust-orange); font-size: 16px;">${window.EMCUtils.formatarMoeda(orc.valor_total || orc.valor_bruto)}</span>
            </div>
          </div>

          <div class="table-container mb-16">
            <table class="table">
              <thead>
                <tr>
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
