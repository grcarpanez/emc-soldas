/**
 * EMC Soldas - View de Tesouraria e Estruturas Financeiras
 * Contas a Pagar/Receber (Competência), Caixa Real (Extrato), Cartões e Estornos.
 */

window.FinanceiroView = {
  currentTab: 'extrato',
  extratoCurrentPage: 1,
  extratoPageSize: 25,
  extratoTotalCount: 0,
  pagarCurrentPage: 1,
  pagarPageSize: 25,
  pagarTotalCount: 0,
  receberCurrentPage: 1,
  receberPageSize: 25,
  receberTotalCount: 0,

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">TESOURARIA & FLUXO DE CAIXA</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CONTAS A PAGAR, A RECEBER, EXTRATO REAL E CARTÕES CORPORATIVOS</p>
        </div>

        <div style="display: flex; gap: 8px;">
          <button class="btn btn-secondary" id="btn-transferencia-inter">+ TRANSFERÊNCIA INTER-CONTAS</button>
          <button class="btn btn-primary" id="btn-novo-lancamento">+ NOVO LANÇAMENTO</button>
        </div>
      </div>

      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'extrato' ? 'active' : ''}" id="tab-btn-fin-extrato">
          EXTRATO REAL (CAIXA)
        </button>
        <button class="tab-btn ${this.currentTab === 'pagar' ? 'active' : ''}" id="tab-btn-fin-pagar">
          CONTAS A PAGAR
        </button>
        <button class="tab-btn ${this.currentTab === 'receber' ? 'active' : ''}" id="tab-btn-fin-receber">
          CONTAS A RECEBER
        </button>
        <button class="tab-btn ${this.currentTab === 'cartoes' ? 'active' : ''}" id="tab-btn-fin-cartoes">
          CARTÕES CORPORATIVOS
        </button>
        <button class="tab-btn ${this.currentTab === 'contas' ? 'active' : ''}" id="tab-btn-fin-contas">
          CONTAS BANCÁRIAS
        </button>
      </div>

      <div id="financeiro-tab-content"></div>
    `;

    document.getElementById('tab-btn-fin-extrato')?.addEventListener('click', () => {
      this.currentTab = 'extrato';
      this.render(container);
    });
    document.getElementById('tab-btn-fin-pagar')?.addEventListener('click', () => {
      this.currentTab = 'pagar';
      this.render(container);
    });
    document.getElementById('tab-btn-fin-receber')?.addEventListener('click', () => {
      this.currentTab = 'receber';
      this.render(container);
    });
    document.getElementById('tab-btn-fin-cartoes')?.addEventListener('click', () => {
      this.currentTab = 'cartoes';
      this.render(container);
    });
    document.getElementById('tab-btn-fin-contas')?.addEventListener('click', () => {
      this.currentTab = 'contas';
      this.render(container);
    });

    document.getElementById('btn-transferencia-inter')?.addEventListener('click', () => this.abrirModalTransferencia());
    document.getElementById('btn-novo-lancamento')?.addEventListener('click', () => {
      const tipo = this.currentTab === 'receber' ? 'ENTRADA' : 'SAIDA';
      const modo = this.currentTab === 'extrato' ? 'extrato' : 'competencia';
      this.abrirModalNovoLancamento(tipo, modo);
    });

    const content = document.getElementById('financeiro-tab-content');
    if (this.currentTab === 'extrato') {
      this.renderExtrato(content);
    } else if (this.currentTab === 'pagar') {
      this.renderContasPagar(content);
    } else if (this.currentTab === 'receber') {
      this.renderContasReceber(content);
    } else if (this.currentTab === 'cartoes') {
      this.renderCartoes(content);
    } else if (this.currentTab === 'contas') {
      this.renderContasBancarias(content);
    }
  },

  // ==========================================================================
  // 1. EXTRATO REAL (REGIME DE CAIXA)
  // ==========================================================================
  async renderExtrato(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-extrato-busca" class="form-control" placeholder="BUSCAR POR HISTÓRICO, CATEGORIA, CONTA OU ID..." style="flex: 1; min-width: 200px;">
          <div style="width: 270px; min-width: 240px; flex-shrink: 0;" id="wrapper-extrato-conta">
            <select id="filtro-extrato-conta" class="form-control">
              <option value="">TODAS AS CONTAS BANCÁRIAS</option>
            </select>
          </div>
          <select id="filtro-extrato-tipo" class="form-control" style="width: 190px; min-width: 175px; flex-shrink: 0;">
            <option value="">TODOS OS TIPOS</option>
            <option value="ENTRADA">RECEITAS (+)</option>
            <option value="SAIDA">DESPESAS (-)</option>
          </select>
          <span id="total-extrato-badge" class="status-chip secondary mono-text" style="padding: 7px 14px; flex-shrink: 0;">0 LANÇAMENTOS</span>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DATA PAGTO</th>
              <th>DESCRIÇÃO / HISTÓRICO</th>
              <th>CATEGORIA</th>
              <th>CONTA BANCÁRIA</th>
              <th>MEIO</th>
              <th>TIPO</th>
              <th>ANEXO</th>
              <th>VALOR</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-extrato-tbody">
            <tr><td colspan="10" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
      <div id="extrato-pagination-container"></div>
    `;

    // Carrega contas para o filtro com flags multi-seleção
    const contas = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS).catch(() => []);
    const listaContas = contas.results || (Array.isArray(contas) ? contas : []);
    let options = '<option value="">TODAS AS CONTAS BANCÁRIAS</option>';
    listaContas.forEach((c) => {
      options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)}</option>`;
    });
    const selConta = document.getElementById('filtro-extrato-conta');
    if (selConta) {
      selConta.innerHTML = options;
      window.EMCUtils.initMultiSelectCombobox(selConta, {
        placeholder: 'TODAS AS CONTAS BANCÁRIAS',
        prefix: 'CONTAS',
        onChange: () => {
          this.extratoCurrentPage = 1;
          this.carregarListaExtrato(1);
        }
      });
    }

    document.getElementById('filtro-extrato-tipo')?.addEventListener('change', () => {
      this.extratoCurrentPage = 1;
      this.carregarListaExtrato(1);
    });
    document.getElementById('filtro-extrato-busca')?.addEventListener('input', () => {
      this.extratoCurrentPage = 1;
      this.carregarListaExtrato(1);
    });

    this.carregarListaExtrato(this.extratoCurrentPage || 1);
  },

  async carregarListaExtrato(page = this.extratoCurrentPage || 1) {
    const tbody = document.getElementById('lista-extrato-tbody');
    if (!tbody) return;

    this.extratoCurrentPage = page;
    const busca = document.getElementById('filtro-extrato-busca')?.value.trim() || '';
    const selConta = document.getElementById('filtro-extrato-conta');
    const contaMulti = selConta?._emcMultiSelect ? selConta._emcMultiSelect.getValues().join(',') : (selConta?.value || '');
    const tipo = document.getElementById('filtro-extrato-tipo')?.value || '';

    try {
      const query = new URLSearchParams({
        status_pagamento: 'PAGO',
        ordering: '-data_pagamento,-id',
        page: this.extratoCurrentPage,
        page_size: this.extratoPageSize
      });
      if (busca) query.append('search', busca);
      if (contaMulti) query.append('conta_id', contaMulti);
      if (tipo) query.append('tipo_lancamento', tipo);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?${query.toString()}`);
      const lista = res.results || (Array.isArray(res) ? res : []);
      const total = res.count !== undefined ? res.count : lista.length;
      this.extratoTotalCount = total;

      const badge = document.getElementById('total-extrato-badge');
      if (badge) {
        badge.textContent = `${total} ${total === 1 ? 'LANÇAMENTO' : 'LANÇAMENTOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhuma movimentação realizada no extrato.</td></tr>';
        const pagContainer = document.getElementById('extrato-pagination-container');
        if (pagContainer) pagContainer.innerHTML = '';
        return;
      }

      let html = '';
      lista.forEach((l) => {
        const isEntrada = l.tipo_lancamento === 'ENTRADA';
        const corValor = isEntrada ? 'var(--color-success)' : 'var(--color-error)';
        const sinal = isEntrada ? '+' : '-';
        const temComprovante = !!l.comprovante;
        const nomeAnexo = l.nome_arquivo_comprovante || 'ANEXO';
        const rotuloAnexo = nomeAnexo.length > 11 ? nomeAnexo.substring(0, 9) + '...' : nomeAnexo;

        const tdAnexo = temComprovante ? `
          <a href="${l.comprovante}" target="_blank" class="badge-anexo-anexado" style="text-decoration: none;" title="Visualizar / Baixar: ${window.EMCUtils.escapeHtml(nomeAnexo)}">
            📎 ${window.EMCUtils.escapeHtml(rotuloAnexo)}
          </a>
        ` : `
          <button type="button" class="btn-anexo-pre-lancamento" title="Anexar Nota Fiscal ou Comprovante" onclick="window.FinanceiroView.triggerUploadComprovanteExtrato(${l.id})">
            📎 + ANEXO
          </button>
        `;

        html += `
          <tr>
            <td class="mono-text">#${l.id}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataHoraPtBr(l.data_pagamento || l.data_vencimento)}</td>
            <td><strong>${window.EMCUtils.escapeHtml(l.descricao || 'Lançamento')}</strong></td>
            <td><span class="status-chip secondary" style="font-size: 11px;">${window.EMCUtils.escapeHtml(l.categoria_nome || 'GERAL')}</span></td>
            <td>${window.EMCUtils.escapeHtml(l.conta_nome || 'Conta')}</td>
            <td><span class="status-chip info">${window.EMCUtils.escapeHtml(l.meio_pagamento_nome || 'PIX/TED')}</span></td>
            <td><span class="status-chip ${isEntrada ? 'success' : 'danger'}">${l.tipo_lancamento}</span></td>
            <td>${tdAnexo}</td>
            <td class="mono-text" style="font-weight: 700; color: ${corValor}; font-size: 15px;">
              ${sinal} ${window.EMCUtils.formatarMoeda(l.valor)}
            </td>
            <td style="text-align: right; white-space: nowrap;">
              <button class="btn btn-secondary btn-sm" style="margin-right: 4px;" onclick="window.FinanceiroView.abrirModalEditarLancamento(${l.id})">EDITAR</button>
              <button class="btn btn-danger btn-sm" onclick="window.FinanceiroView.abrirModalEstorno(${l.id})">ESTORNAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;

      // Renderiza barra de paginação industrial
      window.EMCUtils.renderPagination({
        container: '#extrato-pagination-container',
        currentPage: this.extratoCurrentPage,
        pageSize: this.extratoPageSize,
        totalCount: this.extratoTotalCount,
        pageSizeOptions: [25, 50, 100],
        itemLabel: 'lançamentos',
        onPageChange: (newPage) => {
          this.carregarListaExtrato(newPage);
          document.getElementById('filtro-extrato-busca')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        },
        onPageSizeChange: (newSize) => {
          this.extratoPageSize = newSize;
          this.carregarListaExtrato(1);
        }
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="10" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
      const pagContainer = document.getElementById('extrato-pagination-container');
      if (pagContainer) pagContainer.innerHTML = '';
    }
  },

  // ==========================================================================
  // 2. CONTAS A PAGAR (COMPETÊNCIA)
  // ==========================================================================
  async renderContasPagar(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-pagar-busca" class="form-control" placeholder="BUSCAR POR DESPESA, FORNECEDOR OU ID..." style="flex: 1; min-width: 200px;">
          <div style="width: 220px; min-width: 190px; flex-shrink: 0;" id="wrapper-pagar-status">
            <select id="filtro-pagar-status" class="form-control">
              <option value="A_VENCER" selected>A VENCER</option>
              <option value="VENCIDO">VENCIDAS EM ATRASO</option>
              <option value="PAGO">PAGAS</option>
              <option value="CANCELADO">CANCELADAS</option>
            </select>
          </div>
          <span id="total-pagar-badge" class="status-chip secondary mono-text" style="padding: 7px 12px; flex-shrink: 0;">0 TÍTULOS</span>
          <button class="btn btn-primary" id="btn-novo-pagar-avulso" style="white-space: nowrap; flex-shrink: 0;">+ NOVA DESPESA / TÍTULO</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DESCRIÇÃO / DESPESA</th>
              <th>CATEGORIA</th>
              <th>VENCIMENTO</th>
              <th>VALOR PREVISTO</th>
              <th>STATUS</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-pagar-tbody">
            <tr><td colspan="7" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
      <div id="pagar-pagination-container"></div>
    `;

    const selStatusPagar = document.getElementById('filtro-pagar-status');
    if (selStatusPagar) {
      window.EMCUtils.initMultiSelectCombobox(selStatusPagar, {
        placeholder: 'TODOS OS STATUS',
        prefix: 'STATUS',
        onChange: () => {
          this.pagarCurrentPage = 1;
          this.carregarListaContasPagar(1);
        }
      });
    }

    document.getElementById('filtro-pagar-busca')?.addEventListener('input', () => {
      this.pagarCurrentPage = 1;
      this.carregarListaContasPagar(1);
    });
    document.getElementById('btn-novo-pagar-avulso')?.addEventListener('click', () => this.abrirModalNovoLancamento('SAIDA'));

    this.carregarListaContasPagar(this.pagarCurrentPage || 1);
  },

  async carregarListaContasPagar(page = this.pagarCurrentPage || 1) {
    const tbody = document.getElementById('lista-pagar-tbody');
    if (!tbody) return;

    this.pagarCurrentPage = page;
    const busca = document.getElementById('filtro-pagar-busca')?.value.trim() || '';
    const selStatus = document.getElementById('filtro-pagar-status');
    const statusVal = selStatus?._emcMultiSelect ? selStatus._emcMultiSelect.getValues().join(',') : (selStatus?.value || '');

    try {
      const query = new URLSearchParams({
        tipo_lancamento: 'SAIDA',
        page: this.pagarCurrentPage,
        page_size: this.pagarPageSize
      });
      if (busca) query.append('search', busca);
      if (statusVal) query.append('status_pagamento', statusVal);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?${query.toString()}`);
      const lista = res.results || (Array.isArray(res) ? res : []);
      const total = res.count !== undefined ? res.count : lista.length;
      this.pagarTotalCount = total;

      const badge = document.getElementById('total-pagar-badge');
      if (badge) {
        badge.textContent = `${total} ${total === 1 ? 'TÍTULO' : 'TÍTULOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhuma conta a pagar encontrada.</td></tr>';
        const pagContainer = document.getElementById('pagar-pagination-container');
        if (pagContainer) pagContainer.innerHTML = '';
        return;
      }

      let html = '';
      lista.forEach((l) => {
        const badge = l.status_pagamento === 'PAGO' ? 'success' : (l.status_pagamento === 'VENCIDO' ? 'danger' : 'warning');
        html += `
          <tr>
            <td class="mono-text">#${l.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(l.descricao)}</strong></td>
            <td>${window.EMCUtils.escapeHtml(l.categoria_nome || 'Geral')}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(l.data_vencimento)}</td>
            <td class="mono-text" style="color: var(--color-error); font-weight: 700;">
              ${window.EMCUtils.formatarMoeda(l.valor)}
            </td>
            <td><span class="status-chip ${badge}">${l.status_pagamento}</span></td>
            <td style="text-align: right;">
              ${l.status_pagamento !== 'PAGO' ? `
                <button class="btn btn-primary btn-sm" onclick="window.FinanceiroView.abrirModalLiquidarLancamento(${l.id})">PAGAR (BAIXA)</button>
              ` : '<span class="mono-text" style="font-size: 11px; color: var(--color-success);">LIQUIDADO</span>'}
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;

      // Renderiza barra de paginação industrial
      window.EMCUtils.renderPagination({
        container: '#pagar-pagination-container',
        currentPage: this.pagarCurrentPage,
        pageSize: this.pagarPageSize,
        totalCount: this.pagarTotalCount,
        pageSizeOptions: [25, 50, 100],
        itemLabel: 'títulos',
        onPageChange: (newPage) => {
          this.carregarListaContasPagar(newPage);
          document.getElementById('filtro-pagar-busca')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        },
        onPageSizeChange: (newSize) => {
          this.pagarPageSize = newSize;
          this.carregarListaContasPagar(1);
        }
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
      const pagContainer = document.getElementById('pagar-pagination-container');
      if (pagContainer) pagContainer.innerHTML = '';
    }
  },

  // ==========================================================================
  // 3. CONTAS A RECEBER (COMPETÊNCIA)
  // ==========================================================================
  async renderContasReceber(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-receber-busca" class="form-control" placeholder="BUSCAR POR RECEITA, CLIENTE OU ID..." style="flex: 1; min-width: 200px;">
          <div style="width: 220px; min-width: 190px; flex-shrink: 0;" id="wrapper-receber-status">
            <select id="filtro-receber-status" class="form-control">
              <option value="A_VENCER" selected>A VENCER</option>
              <option value="VENCIDO">VENCIDAS EM ATRASO</option>
              <option value="PAGO">RECEBIDAS</option>
              <option value="CANCELADO">CANCELADAS</option>
            </select>
          </div>
          <span id="total-receber-badge" class="status-chip secondary mono-text" style="padding: 7px 12px; flex-shrink: 0;">0 TÍTULOS</span>
          <button class="btn btn-primary" id="btn-novo-receber-avulso" style="white-space: nowrap; flex-shrink: 0;">+ NOVO TÍTULO AVULSO</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DESCRIÇÃO / FATURA</th>
              <th>VENCIMENTO</th>
              <th>VALOR PREVISTO</th>
              <th>STATUS</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-receber-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
      <div id="receber-pagination-container"></div>
    `;

    const selStatusReceber = document.getElementById('filtro-receber-status');
    if (selStatusReceber) {
      window.EMCUtils.initMultiSelectCombobox(selStatusReceber, {
        placeholder: 'TODOS OS STATUS',
        prefix: 'STATUS',
        onChange: () => {
          this.receberCurrentPage = 1;
          this.carregarListaContasReceber(1);
        }
      });
    }

    document.getElementById('filtro-receber-busca')?.addEventListener('input', () => {
      this.receberCurrentPage = 1;
      this.carregarListaContasReceber(1);
    });
    document.getElementById('btn-novo-receber-avulso')?.addEventListener('click', () => this.abrirModalNovoLancamento('ENTRADA'));

    this.carregarListaContasReceber(this.receberCurrentPage || 1);
  },

  async carregarListaContasReceber(page = this.receberCurrentPage || 1) {
    const tbody = document.getElementById('lista-receber-tbody');
    if (!tbody) return;

    this.receberCurrentPage = page;
    const busca = document.getElementById('filtro-receber-busca')?.value.trim() || '';
    const selStatus = document.getElementById('filtro-receber-status');
    const statusVal = selStatus?._emcMultiSelect ? selStatus._emcMultiSelect.getValues().join(',') : (selStatus?.value || '');

    try {
      const query = new URLSearchParams({
        tipo_lancamento: 'ENTRADA',
        page: this.receberCurrentPage,
        page_size: this.receberPageSize
      });
      if (busca) query.append('search', busca);
      if (statusVal) query.append('status_pagamento', statusVal);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?${query.toString()}`);
      const lista = res.results || (Array.isArray(res) ? res : []);
      const total = res.count !== undefined ? res.count : lista.length;
      this.receberTotalCount = total;

      const badge = document.getElementById('total-receber-badge');
      if (badge) {
        badge.textContent = `${total} ${total === 1 ? 'TÍTULO' : 'TÍTULOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum título a receber encontrado.</td></tr>';
        const pagContainer = document.getElementById('receber-pagination-container');
        if (pagContainer) pagContainer.innerHTML = '';
        return;
      }

      let html = '';
      lista.forEach((l) => {
        const badge = l.status_pagamento === 'PAGO' ? 'success' : (l.status_pagamento === 'VENCIDO' ? 'danger' : 'warning');
        html += `
          <tr>
            <td class="mono-text">#${l.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(l.descricao)}</strong></td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(l.data_vencimento)}</td>
            <td class="mono-text" style="color: var(--color-success); font-weight: 700;">
              ${window.EMCUtils.formatarMoeda(l.valor)}
            </td>
            <td><span class="status-chip ${badge}">${l.status_pagamento}</span></td>
            <td style="text-align: right;">
              ${l.status_pagamento !== 'PAGO' ? `
                <button class="btn btn-primary btn-sm" onclick="window.FinanceiroView.abrirModalLiquidarLancamento(${l.id})">RECEBER (BAIXA)</button>
              ` : '<span class="mono-text" style="font-size: 11px; color: var(--color-success);">RECEBIDO</span>'}
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;

      // Renderiza barra de paginação industrial
      window.EMCUtils.renderPagination({
        container: '#receber-pagination-container',
        currentPage: this.receberCurrentPage,
        pageSize: this.receberPageSize,
        totalCount: this.receberTotalCount,
        pageSizeOptions: [25, 50, 100],
        itemLabel: 'títulos',
        onPageChange: (newPage) => {
          this.carregarListaContasReceber(newPage);
          document.getElementById('filtro-receber-busca')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        },
        onPageSizeChange: (newSize) => {
          this.receberPageSize = newSize;
          this.carregarListaContasReceber(1);
        }
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
      const pagContainer = document.getElementById('receber-pagination-container');
      if (pagContainer) pagContainer.innerHTML = '';
    }
  },

  // ==========================================================================
  // 4. CARTÕES CORPORATIVOS
  // ==========================================================================
  async renderCartoes(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">GESTÃO DE CARTÕES DE CRÉDITO CORPORATIVOS E FATURAS EM ABERTO</p>
          <button class="btn btn-primary" id="btn-novo-cartao">+ NOVO CARTÃO DE CRÉDITO</button>
        </div>
      </div>

      <div id="cartoes-cards-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
        <div style="grid-column: 1 / -1; text-align: center; padding: 24px;"><div class="loader-spinner"></div></div>
      </div>
    `;

    document.getElementById('btn-novo-cartao')?.addEventListener('click', () => {
      window.EMCUtils.openModal({
        title: 'NOVO CARTÃO DE CRÉDITO CORPORATIVO',
        size: 'sm',
        confirmText: 'CADASTRAR CARTÃO',
        content: `
          <div class="form-group">
            <label class="form-label">Nome do Cartão *</label>
            <input type="text" id="cartao-nome" class="form-control" placeholder="EX: ITAU MASTERCARD MASTER" required autofocus>
          </div>
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
            <div class="form-group">
              <label class="form-label">Dia Vencimento</label>
              <input type="number" min="1" max="31" id="cartao-dia-venc" class="form-control mono-text" value="10" required>
            </div>
            <div class="form-group">
              <label class="form-label">Dia Fechamento</label>
              <input type="number" min="1" max="31" id="cartao-dia-fech" class="form-control mono-text" value="3" required>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">Limite Total (R$)</label>
            <input type="text" id="cartao-limite" class="form-control mono-text" data-mask="moeda-atm" value="R$ 10.000,00">
          </div>
        `,
        onConfirm: async () => {
          const nome = document.getElementById('cartao-nome').value.trim();
          const dia_vencimento = parseInt(document.getElementById('cartao-dia-venc').value, 10);
          const dia_fechamento_padrao = parseInt(document.getElementById('cartao-dia-fech').value, 10);
          const limite = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('cartao-limite').value);

          if (!nome) return false;

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO, {
              nome, dia_vencimento, dia_fechamento_padrao, limite
            });
            window.EMCUtils.showToast('Cartão cadastrado com sucesso!', 'success');
            this.renderCartoes(container);
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao cadastrar cartão.', 'error');
            return false;
          }
        }
      });
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO);
      const cartoes = res.results || res || [];
      const grid = document.getElementById('cartoes-cards-grid');

      if (!cartoes.length) {
        grid.innerHTML = '<p class="mono-text" style="grid-column: 1 / -1; text-align: center; color: var(--color-on-surface-variant); padding: 24px;">Nenhum cartão corporativo cadastrado.</p>';
        return;
      }

      let html = '';
      cartoes.forEach((c) => {
        html += `
          <div class="card" style="border-top: 3px solid var(--color-rust-orange);">
            <div class="card-header">
              <h3>${window.EMCUtils.escapeHtml(c.nome)}</h3>
              <span class="status-chip info">VENC. DIA ${c.dia_vencimento}</span>
            </div>
            <div style="margin-bottom: 16px; font-size: 13px; line-height: 1.8;">
              • <strong>Limite Total:</strong> ${window.EMCUtils.formatarMoeda(c.limite)}<br>
              • <strong>Dia de Fechamento:</strong> Dia ${c.dia_fechamento_padrao}<br>
              • <strong>Fatura Aberta:</strong> <span class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${window.EMCUtils.formatarMoeda(c.total_fatura_aberta || 0)}</span>
            </div>
            <div class="text-right">
              <button class="btn btn-secondary btn-sm" onclick="window.FinanceiroView.verFaturasCartao(${c.id})">FATURAS</button>
            </div>
          </div>
        `;
      });
      grid.innerHTML = html;
    } catch (err) {
      document.getElementById('cartoes-cards-grid').innerHTML = `<p style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</p>`;
    }
  },

  async abrirModalLiquidarLancamento(lancamentoId) {
    const [contas, meios] = await Promise.all([
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS),
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.MEIOS_PAGAMENTO)
    ]);

    const listaContas = contas.results || contas || [];
    const listaMeios = meios.results || meios || [];

    let optionsContas = '<option value="">SELECIONE A CONTA BANCÁRIA...</option>';
    listaContas.forEach((c) => {
      optionsContas += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`;
    });

    let optionsMeios = '<option value="">SELECIONE O MEIO FÍSICO...</option>';
    listaMeios.forEach((m) => {
      optionsMeios += `<option value="${m.id}">${window.EMCUtils.escapeHtml(m.nome)}</option>`;
    });

    window.EMCUtils.openModal({
      title: `LIQUIDAÇÃO / BAIXA DO TÍTULO #${lancamentoId}`,
      size: 'sm',
      confirmText: 'CONFIRMAR BAIXA (CAIXA REAL)',
      content: `
        <div class="form-group">
          <label class="form-label">Conta Bancária *</label>
          <select id="liq-conta-id" class="form-control">${optionsContas}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Meio de Pagamento *</label>
          <select id="liq-meio-id" class="form-control">${optionsMeios}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Data da Efetivação *</label>
          <input type="date" id="liq-data" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
        </div>
      `,
      onConfirm: async () => {
        const conta_id = document.getElementById('liq-conta-id').value;
        const meio_pagamento_id = document.getElementById('liq-meio-id').value;
        const data_pagamento = document.getElementById('liq-data').value;

        if (!conta_id || !meio_pagamento_id) {
          window.EMCUtils.showToast('Selecione a conta bancária e o meio de pagamento.', 'warning');
          return false;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FINANCEIRO.LIQUIDAR.replace('{id}', lancamentoId);
          await window.api.post(endpoint, { conta_id, meio_pagamento_id, data_pagamento });
          window.EMCUtils.showToast('Título liquidado no Caixa Real com sucesso!', 'success');
          this.render(document.getElementById('app-root'));
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao liquidar título.', 'error');
          return false;
        }
      }
    });
  },

  abrirModalEstorno(lancamentoId) {
    window.EMCUtils.openModal({
      title: `ESTORNO DE LANÇAMENTO #${lancamentoId}`,
      size: 'sm',
      confirmText: 'CONFIRMAR ESTORNO',
      content: `
        <p style="color: var(--color-on-surface-variant); font-size: 13px; margin-bottom: 12px;">
          O estorno reverterá o saldo na conta bancária e gravará compulsoriamente a justificativa no log perpétuo de auditoria.
        </p>
        <div class="form-group">
          <label class="form-label">Justificativa do Estorno *</label>
          <textarea id="estorno-justificativa" class="form-control" rows="3" placeholder="EX: LANÇAMENTO DUPLICADO OU VALOR DIGITADO INCORRETAMENTE" required autofocus></textarea>
        </div>
      `,
      onConfirm: async () => {
        const justificativa = document.getElementById('estorno-justificativa').value.trim();
        if (!justificativa || justificativa.length < 10) {
          window.EMCUtils.showToast('A justificativa deve conter no mínimo 10 caracteres.', 'warning');
          return false;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FINANCEIRO.ESTORNAR.replace('{id}', lancamentoId);
          await window.api.post(endpoint, { justificativa });
          window.EMCUtils.showToast('Lançamento estornado e saldo bancário revertido!', 'success');
          this.carregarListaExtrato();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao estornar.', 'error');
          return false;
        }
      }
    });
  },

  triggerUploadComprovanteExtrato(lancamentoId) {
    let input = document.getElementById('input-upload-comprovante-extrato-temp');
    if (!input) {
      input = document.createElement('input');
      input.type = 'file';
      input.id = 'input-upload-comprovante-extrato-temp';
      input.accept = '.pdf,.png,.jpg,.jpeg,.xml,.csv,.txt';
      input.style.display = 'none';
      document.body.appendChild(input);
    }

    const newFileInput = input.cloneNode(true);
    input.parentNode.replaceChild(newFileInput, input);

    newFileInput.addEventListener('change', async (e) => {
      const file = e.target.files?.[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('arquivo', file);

      try {
        window.EMCUtils.showToast('Enviando comprovante...', 'info');
        const res = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
        
        await window.api.patch(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}${lancamentoId}/`, {
          comprovante: res.comprovante_path,
          nome_arquivo_comprovante: res.nome_arquivo_comprovante
        });

        window.EMCUtils.showToast(`Comprovante "${res.nome_arquivo_comprovante}" anexado com sucesso!`, 'success');
        this.carregarListaExtrato();
      } catch (err) {
        window.EMCUtils.showToast(`Erro ao anexar comprovante: ${err.message || 'Falha no envio'}`, 'error');
      }
    });

    newFileInput.click();
  },

  async abrirModalTransferencia() {
    const contas = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS).catch(() => []);
    const listaContas = contas.results || contas || [];

    let options = '<option value="">SELECIONE...</option>';
    listaContas.forEach((c) => {
      options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`;
    });

    window.EMCUtils.openModal({
      title: 'TRANSFERÊNCIA ENTRE CONTAS BANCÁRIAS',
      size: 'sm',
      confirmText: 'TRANSFERIR SALDO',
      content: `
        <div class="form-group">
          <label class="form-label">Conta de Origem (Saída) *</label>
          <select id="transf-origem" class="form-control">${options}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Conta de Destino (Entrada) *</label>
          <select id="transf-destino" class="form-control">${options}</select>
        </div>
        <div class="form-group">
          <label class="form-label">Valor da Transferência *</label>
          <input type="text" id="transf-valor" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
        </div>
        <div class="form-group">
          <label class="form-label">Comprovante de Transferência (Opcional)</label>
          <input type="file" id="transf-comprovante" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.xml,.csv,.txt">
        </div>
      `,
      onConfirm: async () => {
        const conta_origem_id = document.getElementById('transf-origem').value;
        const conta_destino_id = document.getElementById('transf-destino').value;
        const valor = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('transf-valor').value);

        if (!conta_origem_id || !conta_destino_id || valor <= 0) {
          window.EMCUtils.showToast('Selecione as contas e informe o valor.', 'warning');
          return false;
        }

        if (conta_origem_id === conta_destino_id) {
          window.EMCUtils.showToast('A conta de origem e destino não podem ser iguais.', 'warning');
          return false;
        }

        let comprovante_path = null;
        let nome_arquivo_comprovante = null;

        const fileInput = document.getElementById('transf-comprovante');
        if (fileInput?.files?.length > 0) {
          try {
            window.EMCUtils.showToast('Enviando comprovante da transferência...', 'info');
            const formData = new FormData();
            formData.append('arquivo', fileInput.files[0]);
            const resUp = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
            comprovante_path = resUp.comprovante_path;
            nome_arquivo_comprovante = resUp.nome_arquivo_comprovante;
          } catch (errUp) {
            window.EMCUtils.showToast(`Erro ao enviar comprovante: ${errUp.message}`, 'error');
            return false;
          }
        }

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.TRANSFERIR, {
            conta_origem_id, conta_destino_id, valor, comprovante_path, nome_arquivo_comprovante
          });
          window.EMCUtils.showToast('Transferência inter-contas realizada com sucesso!', 'success');
          this.carregarListaExtrato();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao realizar transferência.', 'error');
          return false;
        }
      }
    });
  },

  async abrirModalNovoLancamento(defaultTipo = 'SAIDA', modo = 'competencia') {
    const isExtrato = modo === 'extrato' || this.currentTab === 'extrato';
    const [contas, categorias, meios] = await Promise.all([
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS),
      window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS}?ativo=true`),
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.MEIOS_PAGAMENTO)
    ]);

    const listaContas = contas.results || contas || [];
    const listaCat = categorias.results || categorias || [];
    const listaMeios = meios.results || meios || [];

    let optionsContas = `<option value="">${isExtrato ? 'SELECIONE A CONTA BANCÁRIA / CAIXA *' : 'SELECIONE A CONTA (OPCIONAL)...'}</option>`;
    listaContas.forEach((c) => { optionsContas += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (SALDO: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`; });

    let optionsMeios = '<option value="">SELECIONE O MEIO...</option>';
    listaMeios.forEach((m) => { optionsMeios += `<option value="${m.id}">${window.EMCUtils.escapeHtml(m.nome)}</option>`; });

    let modalTitle = 'NOVO LANÇAMENTO AVULSO';
    if (isExtrato) {
      modalTitle = 'NOVO LANÇAMENTO AVULSO NO EXTRATO (CAIXA REAL)';
    } else if (defaultTipo === 'ENTRADA') {
      modalTitle = 'NOVO TÍTULO A RECEBER (AVULSO)';
    } else if (defaultTipo === 'SAIDA') {
      modalTitle = 'NOVA DESPESA A PAGAR (AVULSA)';
    }

    const modalId = window.EMCUtils.openModal({
      title: modalTitle,
      size: 'lg',
      confirmText: 'SALVAR LANÇAMENTO',
      content: `
        ${isExtrato ? `
          <div style="background-color: var(--color-surface-container); border-left: 3px solid var(--color-primary); padding: 8px 12px; margin-bottom: 12px; font-size: 11.5px; line-height: 1.4; color: var(--color-on-surface-variant);">
            ⚡ <strong>Regime de Caixa:</strong> Este lançamento registrará uma movimentação já <strong>LIQUIDADA (PAGA)</strong> no Extrato Real, creditando ou debitando o saldo da conta selecionada instantaneamente.
          </div>
        ` : ''}

        <form id="form-novo-lanc">
          <div class="form-grid-2">
            <div class="form-group">
              <label class="form-label" for="nl-tipo">Tipo de Movimentação *</label>
              <select id="nl-tipo" class="form-control">
                <option value="SAIDA" ${defaultTipo === 'SAIDA' ? 'selected' : ''}>SAÍDA (DESPESA)</option>
                <option value="ENTRADA" ${defaultTipo === 'ENTRADA' ? 'selected' : ''}>ENTRADA (RECEITA)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" for="nl-valor">Valor (R$) *</label>
              <input type="text" id="nl-valor" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00" required>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="nl-desc">Descrição / Histórico *</label>
            <input type="text" id="nl-desc" class="form-control" placeholder="EX: PAGAMENTO ENERGIA ELETRICA OFICINA" required>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 160px; gap: 10px; margin-bottom: 10px;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="nl-cat">Categoria Financeira (DRE) *</label>
              <select id="nl-cat" class="form-control" required>
                <option value="">SELECIONE A CATEGORIA...</option>
              </select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="nl-venc">${isExtrato ? 'Data Movimentação *' : 'Data Vencimento *'}</label>
              <input type="date" id="nl-venc" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 10px; margin-bottom: 10px;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="nl-conta">Conta Bancária / Caixa ${isExtrato ? '*' : ''}</label>
              <select id="nl-conta" class="form-control" ${isExtrato ? 'required' : ''}>${optionsContas}</select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="nl-meio">Meio de Pagamento</label>
              <select id="nl-meio" class="form-control">${optionsMeios}</select>
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 0;">
            <label class="form-label" for="nl-comprovante">Anexar Comprovante / Nota Fiscal (Opcional)</label>
            <input type="file" id="nl-comprovante" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.xml,.csv,.txt">
          </div>
        </form>
      `,
      onConfirm: async () => {
        const tipo_lancamento = document.getElementById('nl-tipo')?.value;
        const valor = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('nl-valor')?.value || '0');
        const descricao = document.getElementById('nl-desc')?.value.trim();
        const categoria_id = document.getElementById('nl-cat')?.value;
        const data_vencimento = document.getElementById('nl-venc')?.value;
        const conta_id = document.getElementById('nl-conta')?.value || null;
        const meio_pagamento_id = document.getElementById('nl-meio')?.value || null;

        if (!descricao || valor <= 0 || !categoria_id) {
          window.EMCUtils.showToast('Preencha os campos obrigatórios (Descrição, Valor e Categoria).', 'warning');
          return false;
        }

        if (isExtrato && !conta_id) {
          window.EMCUtils.showToast('Selecione a Conta Bancária / Caixa para o lançamento no Extrato.', 'warning');
          return false;
        }

        const payload = {
          tipo_lancamento,
          valor,
          descricao,
          categoria: parseInt(categoria_id, 10),
          categoria_id: parseInt(categoria_id, 10),
          data_vencimento,
          conta: conta_id ? parseInt(conta_id, 10) : null,
          conta_id: conta_id ? parseInt(conta_id, 10) : null,
          meio_pagamento: meio_pagamento_id ? parseInt(meio_pagamento_id, 10) : null,
          meio_pagamento_id: meio_pagamento_id ? parseInt(meio_pagamento_id, 10) : null
        };

        if (isExtrato) {
          payload.status_pagamento = 'PAGO';
          payload.data_pagamento = `${data_vencimento}T12:00:00`;
        }

        const fileInput = document.getElementById('nl-comprovante');
        if (fileInput?.files?.length > 0) {
          try {
            window.EMCUtils.showToast('Enviando comprovante do lançamento...', 'info');
            const formData = new FormData();
            formData.append('arquivo', fileInput.files[0]);
            const resUp = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
            payload.comprovante = resUp.comprovante_path;
            payload.nome_arquivo_comprovante = resUp.nome_arquivo_comprovante;
          } catch (errUp) {
            window.EMCUtils.showToast(`Erro ao enviar comprovante: ${errUp.message}`, 'error');
            return false;
          }
        }

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS, payload);
          window.EMCUtils.showToast('Lançamento cadastrado com sucesso!', 'success');
          if (this.currentTab === 'extrato') {
            this.carregarListaExtrato();
          } else if (this.currentTab === 'pagar') {
            this.carregarListaContasPagar();
          } else if (this.currentTab === 'receber') {
            this.carregarListaContasReceber();
          } else {
            this.render(document.getElementById('app-root'));
          }
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao criar lançamento.', 'error');
          return false;
        }
      }
    });

    // Função de Filtragem Dinâmica de Categorias com base no Tipo de Movimentação selecionado
    const atualizarCategoriasDinamicas = (tipoMov) => {
      const selCat = document.getElementById('nl-cat');
      if (!selCat) return;

      const valorAnterior = selCat.value;
      let filtradas = [];

      if (tipoMov === 'SAIDA') {
        filtradas = listaCat.filter((c) => c.tipo === 'DESPESA' || c.tipo === 'AMBOS');
      } else if (tipoMov === 'ENTRADA') {
        filtradas = listaCat.filter((c) => c.tipo === 'RECEITA' || c.tipo === 'AMBOS');
      } else {
        filtradas = listaCat;
      }

      let opts = '<option value="">SELECIONE A CATEGORIA...</option>';
      filtradas.forEach((cat) => {
        const tag = cat.tipo === 'AMBOS' ? '[AMBOS]' : (cat.tipo === 'RECEITA' ? '[ENTRADA]' : '[SAÍDA]');
        opts += `<option value="${cat.id}">${window.EMCUtils.escapeHtml(cat.nome)} ${tag}</option>`;
      });
      selCat.innerHTML = opts;

      // Mantém a categoria selecionada se ela for permitida no novo tipo
      if (valorAnterior && filtradas.some((c) => String(c.id) === String(valorAnterior))) {
        selCat.value = valorAnterior;
      }
    };

    // Popula imediatamente no início e adiciona o evento de troca
    atualizarCategoriasDinamicas(defaultTipo);
    document.getElementById('nl-tipo')?.addEventListener('change', (e) => {
      atualizarCategoriasDinamicas(e.target.value);
    });
  },

  async abrirModalEditarLancamento(lancamentoId) {
    try {
      const [lancamento, categorias] = await Promise.all([
        window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}${lancamentoId}/`),
        window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS}?ativo=true`)
      ]);

      const listaCat = categorias.results || categorias || [];
      const tipoLanc = lancamento.tipo_lancamento;
      let catsPermitidas = [];

      if (tipoLanc === 'SAIDA') {
        catsPermitidas = listaCat.filter((c) => c.tipo === 'DESPESA' || c.tipo === 'AMBOS');
      } else if (tipoLanc === 'ENTRADA') {
        catsPermitidas = listaCat.filter((c) => c.tipo === 'RECEITA' || c.tipo === 'AMBOS');
      } else {
        catsPermitidas = listaCat;
      }

      let optionsCat = '<option value="">SELECIONE A CATEGORIA...</option>';
      catsPermitidas.forEach((c) => {
        const selected = lancamento.categoria === c.id ? 'selected' : '';
        const tag = c.tipo === 'AMBOS' ? '[AMBOS]' : (c.tipo === 'RECEITA' ? '[ENTRADA]' : '[SAÍDA]');
        optionsCat += `<option value="${c.id}" ${selected}>${window.EMCUtils.escapeHtml(c.nome)} ${tag}</option>`;
      });

      window.EMCUtils.openModal({
        title: `EDITAR / RECLASSIFICAR LANÇAMENTO #${lancamento.id}`,
        size: 'md',
        confirmText: 'SALVAR ALTERAÇÕES',
        content: `
          <div style="background-color: var(--color-surface-container); border-left: 3px solid var(--color-primary); padding: 8px 12px; margin-bottom: 12px; font-size: 11.5px; line-height: 1.4; color: var(--color-on-surface-variant);">
            💡 <strong>Reclassificação Contábil:</strong> Altere a categoria deste lançamento para organizar seu fluxo de caixa ou para viabilizar a exclusão de uma categoria que será descontinuada.
          </div>

          <div style="display: flex; gap: 8px; margin-bottom: 12px; align-items: center; flex-wrap: wrap;">
            <span class="status-chip ${tipoLanc === 'ENTRADA' ? 'success' : 'danger'}">${tipoLanc}</span>
            <span class="status-chip secondary mono-text">VALOR: ${window.EMCUtils.formatarMoeda(lancamento.valor)}</span>
            <span class="status-chip info mono-text">CONTA: ${window.EMCUtils.escapeHtml(lancamento.conta_nome || 'NÃO INFORMADA')}</span>
            <span class="status-chip secondary mono-text">STATUS: ${lancamento.status_pagamento}</span>
          </div>

          <div class="form-group">
            <label class="form-label" for="edit-lanc-desc">Descrição / Histórico *</label>
            <input type="text" id="edit-lanc-desc" class="form-control" value="${window.EMCUtils.escapeHtml(lancamento.descricao || '')}" required>
          </div>

          <div class="form-group">
            <label class="form-label" for="edit-lanc-cat">Categoria Financeira (DRE) *</label>
            <select id="edit-lanc-cat" class="form-control" required>
              ${optionsCat}
            </select>
          </div>

          <div class="form-group">
            <label class="form-label" for="edit-lanc-comprovante">
              ${lancamento.comprovante ? `Comprovante Atual: <a href="${lancamento.comprovante}" target="_blank" style="color: var(--color-success); font-weight: 600; text-decoration: underline;">📎 ${window.EMCUtils.escapeHtml(lancamento.nome_arquivo_comprovante || 'Ver Arquivo')}</a> (Substituir abaixo)` : 'Anexar Comprovante / Nota Fiscal'}
            </label>
            <input type="file" id="edit-lanc-comprovante" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.xml,.csv,.txt">
          </div>
        `,
        onConfirm: async () => {
          const descricao = document.getElementById('edit-lanc-desc')?.value.trim();
          const categoria = parseInt(document.getElementById('edit-lanc-cat')?.value, 10);

          if (!descricao || !categoria) {
            window.EMCUtils.showToast('Preencha a descrição e selecione a categoria.', 'warning');
            return false;
          }

          const patchPayload = {
            descricao,
            categoria,
            categoria_id: categoria
          };

          const fileInput = document.getElementById('edit-lanc-comprovante');
          if (fileInput?.files?.length > 0) {
            try {
              window.EMCUtils.showToast('Enviando comprovante...', 'info');
              const formData = new FormData();
              formData.append('arquivo', fileInput.files[0]);
              const resUp = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
              patchPayload.comprovante = resUp.comprovante_path;
              patchPayload.nome_arquivo_comprovante = resUp.nome_arquivo_comprovante;
            } catch (errUp) {
              window.EMCUtils.showToast(`Erro ao enviar comprovante: ${errUp.message}`, 'error');
              return false;
            }
          }

          try {
            await window.api.patch(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}${lancamentoId}/`, patchPayload);
            window.EMCUtils.showToast('Lançamento atualizado com sucesso!', 'success');
            if (this.currentTab === 'extrato') {
              this.carregarListaExtrato();
            } else if (this.currentTab === 'pagar') {
              this.carregarListaContasPagar();
            } else if (this.currentTab === 'receber') {
              this.carregarListaContasReceber();
            }
            return true;
          } catch (err) {
            window.EMCUtils.showToast(err.message || 'Erro ao atualizar lançamento.', 'error');
            return false;
          }
        }
      });
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao carregar dados do lançamento.', 'error');
    }
  },

  // ==========================================================================
  // 5. GESTÃO DE CONTAS BANCÁRIAS E CAIXAS FÍSICOS
  // ==========================================================================
  contasBancariasCache: [],

  async renderContasBancarias(container) {
    container.innerHTML = `
      <!-- Cards de Métricas de Contas -->
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 20px;">
        <div class="card" style="border-left: 4px solid var(--color-primary);">
          <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); text-transform: uppercase;">SALDO TOTAL EM CONTAS</div>
          <div class="mono-text" id="kpi-contas-saldo" style="font-size: 22px; font-weight: 700; margin-top: 4px;">R$ 0,00</div>
          <div style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 4px;">Soma de todos os saldos bancários e caixas</div>
        </div>

        <div class="card" style="border-left: 4px solid var(--color-warning);">
          <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); text-transform: uppercase;">LIMITE CHEQUE ESPECIAL</div>
          <div class="mono-text" id="kpi-contas-limite" style="font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--color-warning);">R$ 0,00</div>
          <div style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 4px;">Crédito contratado para tolerância negativa</div>
        </div>

        <div class="card" style="border-left: 4px solid var(--color-success);">
          <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); text-transform: uppercase;">DISPONÍVEL TOTAL REAL</div>
          <div class="mono-text" id="kpi-contas-disponivel" style="font-size: 22px; font-weight: 700; margin-top: 4px; color: var(--color-success);">R$ 0,00</div>
          <div style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 4px;">Saldo Líquido + Limite de Cheque Especial</div>
        </div>
      </div>

      <!-- Barra de Ações -->
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <input type="text" id="filtro-contas-busca" class="form-control" placeholder="BUSCAR CONTA POR NOME OU ID..." style="max-width: 380px;">
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-primary" id="btn-nova-conta-bancaria">+ NOVA CONTA BANCÁRIA</button>
          </div>
        </div>
      </div>

      <!-- Tabela de Contas Bancárias -->
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th style="width: 70px;">ID</th>
              <th>NOME DA CONTA / CAIXA</th>
              <th class="text-right">SALDO ATUAL</th>
              <th class="text-right">LIMITE CHEQUE ESPECIAL</th>
              <th class="text-right">DISPONÍVEL TOTAL</th>
              <th class="text-center" style="width: 160px;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="tbody-contas-bancarias">
            <tr>
              <td colspan="6" class="text-center" style="padding: 40px 0;">
                <div class="loader-spinner"></div>
                <div class="mono-text mt-8">CARREGANDO CONTAS BANCÁRIAS...</div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-nova-conta-bancaria')?.addEventListener('click', () => this.abrirModalContaBancaria());
    document.getElementById('filtro-contas-busca')?.addEventListener('input', (e) => {
      const termo = e.target.value.toLowerCase().trim();
      const filtradas = this.contasBancariasCache.filter(c => 
        c.nome.toLowerCase().includes(termo) || String(c.id).includes(termo)
      );
      this.renderLinhasContasBancarias(filtradas);
    });

    this.carregarListaContasBancarias();
  },

  async carregarListaContasBancarias() {
    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS);
      this.contasBancariasCache = res.results || res || [];
      this.atualizarKpisContasBancarias(this.contasBancariasCache);
      this.renderLinhasContasBancarias(this.contasBancariasCache);
    } catch (err) {
      const tbody = document.getElementById('tbody-contas-bancarias');
      if (tbody) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger" style="padding: 24px;">${window.EMCUtils.escapeHtml(err.message || 'Erro ao carregar contas')}</td></tr>`;
      }
    }
  },

  atualizarKpisContasBancarias(contas) {
    let totalSaldo = 0;
    let totalLimite = 0;

    contas.forEach(c => {
      totalSaldo += parseFloat(c.saldo) || 0;
      totalLimite += parseFloat(c.limite_credito) || 0;
    });

    const totalDisponivel = totalSaldo + totalLimite;

    const elSaldo = document.getElementById('kpi-contas-saldo');
    const elLimite = document.getElementById('kpi-contas-limite');
    const elDisponivel = document.getElementById('kpi-contas-disponivel');

    if (elSaldo) {
      elSaldo.textContent = window.EMCUtils.formatarMoeda(totalSaldo);
      elSaldo.style.color = totalSaldo >= 0 ? 'var(--color-on-surface)' : 'var(--color-error)';
    }
    if (elLimite) {
      elLimite.textContent = window.EMCUtils.formatarMoeda(totalLimite);
    }
    if (elDisponivel) {
      elDisponivel.textContent = window.EMCUtils.formatarMoeda(totalDisponivel);
      elDisponivel.style.color = totalDisponivel >= 0 ? 'var(--color-success)' : 'var(--color-error)';
    }
  },

  renderLinhasContasBancarias(contas) {
    const tbody = document.getElementById('tbody-contas-bancarias');
    if (!tbody) return;

    if (!contas.length) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="text-center" style="padding: 40px 16px;">
            <p class="mono-text" style="color: var(--color-on-surface-variant); margin-bottom: 12px;">NENHUMA CONTA BANCÁRIA OU CAIXA CADASTRADO NO MOMENTO.</p>
            <button class="btn btn-primary btn-sm" onclick="window.FinanceiroView.abrirModalContaBancaria()">+ CADASTRAR PRIMEIRA CONTA</button>
          </td>
        </tr>
      `;
      return;
    }

    let html = '';
    contas.forEach(c => {
      const saldo = parseFloat(c.saldo) || 0;
      const limite = parseFloat(c.limite_credito) || 0;
      const disponivel = saldo + limite;
      const isPositivo = saldo >= 0;

      html += `
        <tr>
          <td class="mono-text font-bold">#${c.id}</td>
          <td>
            <strong>${window.EMCUtils.escapeHtml(c.nome)}</strong>
          </td>
          <td class="mono-text text-right" style="font-weight: 700; color: ${isPositivo ? 'var(--color-success)' : 'var(--color-error)'};">
            ${window.EMCUtils.formatarMoeda(saldo)}
          </td>
          <td class="mono-text text-right" style="color: var(--color-on-surface-variant);">
            ${window.EMCUtils.formatarMoeda(limite)}
          </td>
          <td class="mono-text text-right font-bold" style="color: ${disponivel >= 0 ? 'var(--color-success)' : 'var(--color-error)'};">
            ${window.EMCUtils.formatarMoeda(disponivel)}
          </td>
          <td class="text-center">
            <div style="display: flex; justify-content: center; gap: 6px;">
              <button class="btn btn-secondary btn-sm" onclick="window.FinanceiroView.abrirModalContaBancaria(${c.id})">EDITAR</button>
              <button class="btn btn-secondary btn-sm" onclick="window.FinanceiroView.recalcularSaldoConta(${c.id}, '${window.EMCUtils.escapeHtml(c.nome)}')">RECALCULAR</button>
              <button class="btn btn-danger btn-sm" onclick="window.FinanceiroView.excluirContaBancaria(${c.id}, '${window.EMCUtils.escapeHtml(c.nome)}')">EXCLUIR</button>
            </div>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
  },

  async abrirModalContaBancaria(contaId = null) {
    let conta = null;
    if (contaId) {
      conta = this.contasBancariasCache.find(c => c.id === contaId);
      if (!conta) {
        try {
          conta = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS}${contaId}/`);
        } catch (e) {
          window.EMCUtils.showToast('Erro ao carregar dados da conta.', 'error');
          return;
        }
      }
    }

    const isEdicao = !!conta;
    const saldoAtual = isEdicao ? parseFloat(conta.saldo) || 0 : 0;
    const limiteAtual = isEdicao ? parseFloat(conta.limite_credito) || 0 : 0;

    window.EMCUtils.openModal({
      title: isEdicao ? `EDITAR CONTA BANCÁRIA: #${conta.id}` : 'NOVA CONTA BANCÁRIA OU CAIXA',
      size: 'md',
      confirmText: isEdicao ? 'SALVAR ALTERAÇÕES' : 'CADASTRAR CONTA',
      content: `
        <form id="form-conta-bancaria">
          <div class="form-group">
            <label class="form-label">Nome da Conta / Banco / Caixa *</label>
            <input type="text" id="cb-nome" class="form-control" placeholder="EX: BANCO BRADESCO S.A. AG: 2868 CC: 59729-5" value="${isEdicao ? window.EMCUtils.escapeHtml(conta.nome) : ''}" required>
            <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-top: 4px;">Identificação oficial utilizada em extratos, relatórios e conciliação bancária.</span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;">
            <div class="form-group">
              <label class="form-label">${isEdicao ? 'Saldo Atual (R$)' : 'Saldo Inicial (R$)'} *</label>
              <input type="text" id="cb-saldo" class="form-control mono-text" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(saldoAtual)}" required>
            </div>

            <div class="form-group">
              <label class="form-label">Limite de Cheque Especial (R$)</label>
              <input type="text" id="cb-limite" class="form-control mono-text" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(limiteAtual)}">
              <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-top: 4px;">Tolerância máxima permitida para saldo negativo.</span>
            </div>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const nome = document.getElementById('cb-nome')?.value.trim();
        const saldo = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('cb-saldo')?.value || '0');
        const limite_credito = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('cb-limite')?.value || '0');

        if (!nome) {
          window.EMCUtils.showToast('Informe o nome da conta bancária.', 'warning');
          return false;
        }

        try {
          if (isEdicao) {
            await window.api.patch(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS}${conta.id}/`, {
              nome,
              saldo,
              limite_credito
            });
            window.EMCUtils.showToast('Conta bancária atualizada com sucesso!', 'success');
          } else {
            await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS, {
              nome,
              saldo,
              limite_credito
            });
            window.EMCUtils.showToast('Conta bancária cadastrada com sucesso!', 'success');
          }
          await this.carregarListaContasBancarias();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar conta bancária.', 'error');
          return false;
        }
      }
    });
  },

  async excluirContaBancaria(id, nome) {
    window.EMCUtils.openModal({
      title: 'CONFIRMAÇÃO DE INATIVAÇÃO DE CONTA',
      size: 'sm',
      confirmText: 'INATIVAR CONTA',
      content: `
        <p>Tem certeza que deseja inativar a conta bancária <strong>${window.EMCUtils.escapeHtml(nome)}</strong> (#${id})?</p>
        <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 8px;">
          A conta não será excluída fisicamente (governança de Soft Delete), mas ficará oculta para novas operações de caixa e conciliação bancária.
        </p>
      `,
      onConfirm: async () => {
        try {
          await window.api.delete(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS}${id}/`);
          window.EMCUtils.showToast('Conta bancária inativada com sucesso.', 'success');
          await this.carregarListaContasBancarias();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao inativar conta bancária.', 'error');
          return false;
        }
      }
    });
  },

  async recalcularSaldoConta(contaId, nome) {
    window.EMCUtils.openModal({
      title: 'AUDITORIA E RECÁLCULO DE SALDO',
      size: 'sm',
      confirmText: 'CONFIRMAR RECÁLCULO',
      content: `
        <p>Deseja auditar e recalcular o saldo da conta <strong>${window.EMCUtils.escapeHtml(nome)}</strong> (#${contaId})?</p>
        <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 8px;">
          O sistema somará todas as entradas pagas, subtrairá as saídas pagas e aplicará as transferências inter-contas ativas vinculadas a esta conta.
        </p>
      `,
      onConfirm: async () => {
        try {
          const res = await window.api.post(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS}${contaId}/recalcular-saldo/`);
          window.EMCUtils.showToast(`Saldo recalculado: ${window.EMCUtils.formatarMoeda(res.novo_saldo)} (Anterior: ${window.EMCUtils.formatarMoeda(res.saldo_anterior)})`, 'success');
          await this.carregarListaContasBancarias();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao recalcular saldo.', 'error');
          return false;
        }
      }
    });
  }
};
