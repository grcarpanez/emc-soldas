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
      this.extratoListaAtual = lista;
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
            <td><span class="status-chip ${badge}">${window.EMCUtils.formatarStatus(l.status_pagamento)}</span></td>
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
            <td><span class="status-chip ${badge}">${window.EMCUtils.formatarStatus(l.status_pagamento)}</span></td>
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
  // 4. CARTÕES CORPORATIVOS E GESTÃO DE FATURAS
  // ==========================================================================
  cartoesLista: [],
  cartaoAtivo: null,
  faturasLista: [],
  faturaAtiva: null,

  async renderCartoes(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div>
            <h2 style="font-size: 18px; font-weight: 700; margin: 0;">CARTÕES CORPORATIVOS & FATURAS</h2>
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin: 4px 0 0 0;">
              CONTROLE DE LIMITES, RECALCULO DE FECHAMENTO, PARCELAMENTO EM N VEZES E LIQUIDAÇÃO
            </p>
          </div>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" id="btn-editar-cartao-ativo" style="display: none;">✏️ EDITAR CARTÃO</button>
            <button class="btn btn-primary btn-sm" id="btn-novo-cartao">+ NOVO CARTÃO CORPORATIVO</button>
          </div>
        </div>
      </div>

      <div id="cartoes-principal-view">
        <div style="text-align: center; padding: 32px;"><div class="loader-spinner"></div></div>
      </div>
    `;

    document.getElementById('btn-novo-cartao')?.addEventListener('click', () => this.abrirModalNovoCartao());
    document.getElementById('btn-editar-cartao-ativo')?.addEventListener('click', () => {
      if (this.cartaoAtivo) this.abrirModalNovoCartao(this.cartaoAtivo);
    });

    await this.carregarListaCartoes();
  },

  async carregarListaCartoes(cartaoIdParaSelecionar = null) {
    const viewContainer = document.getElementById('cartoes-principal-view');
    if (!viewContainer) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO);
      this.cartoesLista = res.results || (Array.isArray(res) ? res : []);

      if (!this.cartoesLista.length) {
        document.getElementById('btn-editar-cartao-ativo').style.display = 'none';
        viewContainer.innerHTML = `
          <div class="card text-center" style="padding: 48px 16px;">
            <p class="mono-text" style="font-size: 14px; color: var(--color-on-surface-variant); margin-bottom: 16px;">
              Nenhum Cartão Corporativo cadastrado no sistema.
            </p>
            <button class="btn btn-primary" onclick="window.FinanceiroView.abrirModalNovoCartao()">
              + CADASTRAR PRIMEIRO CARTÃO CORPORATIVO
            </button>
          </div>
        `;
        return;
      }

      document.getElementById('btn-editar-cartao-ativo').style.display = 'inline-block';

      // Define cartão ativo
      if (cartaoIdParaSelecionar) {
        this.cartaoAtivo = this.cartoesLista.find(c => c.id === Number(cartaoIdParaSelecionar)) || this.cartoesLista[0];
      } else if (!this.cartaoAtivo || !this.cartoesLista.some(c => c.id === this.cartaoAtivo.id)) {
        this.cartaoAtivo = this.cartoesLista[0];
      } else {
        this.cartaoAtivo = this.cartoesLista.find(c => c.id === this.cartaoAtivo.id) || this.cartoesLista[0];
      }

      this.renderEstruturaCartaoAtivo();
    } catch (err) {
      viewContainer.innerHTML = `<div class="card" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</div>`;
    }
  },

  renderEstruturaCartaoAtivo() {
    const viewContainer = document.getElementById('cartoes-principal-view');
    if (!viewContainer || !this.cartaoAtivo) return;

    const optionsCartoes = this.cartoesLista.map(c => `
      <option value="${c.id}" ${c.id === this.cartaoAtivo.id ? 'selected' : ''}>
        💳 ${window.EMCUtils.escapeHtml(c.nome)} (Venc. Dia ${c.dia_vencimento} / Fech. Dia ${c.dia_fechamento_padrao})
      </option>
    `).join('');

    viewContainer.innerHTML = `
      <!-- Seletor de Cartão -->
      <div class="card mb-16" style="padding: 12px 16px; background-color: var(--color-surface-container);">
        <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
          <label class="form-label mono-text" style="margin: 0; font-weight: 700; white-space: nowrap;">CARTÃO ATIVO:</label>
          <select id="select-cartao-ativo" class="form-control" style="max-width: 480px; font-weight: 600;">
            ${optionsCartoes}
          </select>
          <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">
            Conta Preferencial: ${this.cartaoAtivo.conta_bancaria_nome ? window.EMCUtils.escapeHtml(this.cartaoAtivo.conta_bancaria_nome) : 'NÃO DEFINIDA'}
          </span>
        </div>
      </div>

      <!-- KPIs Flip Cards Industriais do Cartão -->
      <div id="cartao-kpis-container" class="mb-16">
        <div style="text-align: center; padding: 16px;"><div class="loader-spinner"></div></div>
      </div>

      <!-- Faturas e Lançamentos -->
      <div class="card mb-16">
        <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
          <h3 style="font-size: 14px; font-weight: 700; margin: 0;">HISTÓRICO E NAVEGAÇÃO DE FATURAS</h3>
          <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">SELECIONE A COMPETÊNCIA DESEJADA</span>
        </div>
        <div id="cartao-faturas-timeline" style="display: flex; gap: 8px; overflow-x: auto; padding: 12px 4px; border-bottom: 1px solid var(--color-outline-variant);">
          <div class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">Carregando faturas...</div>
        </div>
        <div id="fatura-ativa-detalhe-container" style="padding-top: 16px;">
          <div style="text-align: center; padding: 24px;"><div class="loader-spinner"></div></div>
        </div>
      </div>
    `;

    document.getElementById('select-cartao-ativo')?.addEventListener('change', (e) => {
      this.selecionarCartao(e.target.value);
    });

    this.carregarMetricasEFaturasCartao();
  },

  async selecionarCartao(cartaoId) {
    this.cartaoAtivo = this.cartoesLista.find(c => c.id === Number(cartaoId));
    this.faturaAtiva = null;
    this.renderEstruturaCartaoAtivo();
  },

  async carregarMetricasEFaturasCartao() {
    if (!this.cartaoAtivo) return;

    try {
      // 1. Busca Métricas e Limite Disponível
      const endpointLimite = window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO + `${this.cartaoAtivo.id}/limite-disponivel/`;
      const [resLimite, resFaturas] = await Promise.all([
        window.api.get(endpointLimite),
        window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO + `${this.cartaoAtivo.id}/faturas/`)
      ]);

      // Renderiza Flip Cards de KPI
      const kpisContainer = document.getElementById('cartao-kpis-container');
      if (kpisContainer) {
        const limiteTotal = parseFloat(resLimite.limite_total || 0);
        const totalComprometido = parseFloat(resLimite.total_comprometido || 0);
        const limiteDisponivel = parseFloat(resLimite.limite_disponivel || 0);
        const faturaAbertaAtual = parseFloat(resLimite.total_fatura_aberta_atual || 0);

        const corDisponivel = limiteDisponivel < (limiteTotal * 0.15) ? 'var(--color-error)' : 'var(--color-success)';

        kpisContainer.innerHTML = `
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px;">
            <div class="card" style="border-left: 4px solid var(--color-outline); padding: 12px 16px;">
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); font-weight: 700;">LIMITE TOTAL CONTRATUAL</div>
              <div class="mono-text font-bold" style="font-size: 20px; color: var(--color-on-surface); margin-top: 4px;">
                ${window.EMCUtils.formatarMoeda(limiteTotal)}
              </div>
            </div>

            <div class="card" style="border-left: 4px solid var(--color-rust-orange); padding: 12px 16px;">
              <div class="mono-text" style="font-size: 11px; color: var(--color-rust-orange); font-weight: 700;">LIMITE COMPROMETIDO (TOTAL)</div>
              <div class="mono-text font-bold" style="font-size: 20px; color: var(--color-rust-orange); margin-top: 4px;">
                ${window.EMCUtils.formatarMoeda(totalComprometido)}
              </div>
            </div>

            <div class="card" style="border-left: 4px solid ${corDisponivel}; padding: 12px 16px;">
              <div class="mono-text" style="font-size: 11px; color: ${corDisponivel}; font-weight: 700;">LIMITE DISPONÍVEL IMEDIATO</div>
              <div class="mono-text font-bold" style="font-size: 20px; color: ${corDisponivel}; margin-top: 4px;">
                ${window.EMCUtils.formatarMoeda(limiteDisponivel)}
              </div>
            </div>

            <div class="card" style="border-left: 4px solid var(--color-warning); padding: 12px 16px;">
              <div class="mono-text" style="font-size: 11px; color: var(--color-warning); font-weight: 700;">FATURA VIGENTE (ABERTA)</div>
              <div class="mono-text font-bold" style="font-size: 20px; color: var(--color-warning); margin-top: 4px;">
                ${window.EMCUtils.formatarMoeda(faturaAbertaAtual)}
              </div>
            </div>
          </div>
        `;
      }

      // 2. Renderiza Linha do Tempo de Faturas (Ordem Cronológica Crescente)
      this.faturasLista = resFaturas.results || (Array.isArray(resFaturas) ? resFaturas : []);
      this.faturasLista.sort((a, b) => (a.mes_referencia || '').localeCompare(b.mes_referencia || ''));
      const timelineContainer = document.getElementById('cartao-faturas-timeline');

      if (!this.faturasLista.length) {
        if (timelineContainer) {
          timelineContainer.innerHTML = '<span class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">Nenhuma fatura gerada para este cartão. Lance uma compra para abrir a primeira competência.</span>';
        }
        const detalheContainer = document.getElementById('fatura-ativa-detalhe-container');
        if (detalheContainer) {
          detalheContainer.innerHTML = `
            <div style="text-align: center; padding: 24px;">
              <button class="btn btn-primary" onclick="window.FinanceiroView.abrirModalLancarDespesaCartao(window.FinanceiroView.cartaoAtivo)">
                + LANÇAR PRIMEIRA COMPRA NO CARTÃO
              </button>
            </div>
          `;
        }
        return;
      }

      // Seleciona primeira fatura aberta ou a mais recente
      if (!this.faturaAtiva || !this.faturasLista.some(f => f.id === this.faturaAtiva.id)) {
        const aberta = this.faturasLista.find(f => f.status === 'ABERTA');
        this.faturaAtiva = aberta || this.faturasLista[0];
      }

      if (timelineContainer) {
        timelineContainer.innerHTML = this.faturasLista.map(f => {
          const isAtiva = f.id === this.faturaAtiva.id;
          const statusClass = f.status === 'PAGA' ? 'success' : (f.status === 'FECHADA' ? 'warning' : 'info');
          const activeClass = isAtiva ? 'active' : '';

          return `
            <button type="button" class="fatura-timeline-btn ${activeClass}" 
                    onclick="window.FinanceiroView.selecionarFatura(${f.id})">
              <span class="fatura-mes">${f.mes_referencia}</span>
              <span class="status-chip ${statusClass}" style="font-size: 9px; padding: 2px 6px;">${f.status}</span>
            </button>
          `;
        }).join('');
      }

      await this.carregarDetalhesFaturaAtiva();
    } catch (err) {
      const detalheContainer = document.getElementById('fatura-ativa-detalhe-container');
      if (detalheContainer) {
        detalheContainer.innerHTML = `<div style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</div>`;
      }
    }
  },

  async selecionarFatura(faturaId) {
    this.faturaAtiva = this.faturasLista.find(f => f.id === Number(faturaId));
    await this.carregarMetricasEFaturasCartao();
  },

  async carregarDetalhesFaturaAtiva() {
    const detalheContainer = document.getElementById('fatura-ativa-detalhe-container');
    if (!detalheContainer || !this.faturaAtiva) return;

    detalheContainer.innerHTML = '<div style="text-align: center; padding: 24px;"><div class="loader-spinner"></div></div>';

    try {
      const endpointItens = window.CONFIG.ENDPOINTS.FINANCEIRO.FATURAS_CARTAO + `${this.faturaAtiva.id}/itens/`;
      const resItens = await window.api.get(endpointItens);
      const itens = resItens.results || (Array.isArray(resItens) ? resItens : []);

      const f = this.faturaAtiva;
      const statusBadge = f.status === 'PAGA' ? 'success' : (f.status === 'FECHADA' ? 'warning' : 'info');

      // Botões contextuais por status da fatura
      let acoesHtml = '';
      if (f.status === 'ABERTA') {
        acoesHtml = `
          <button class="btn btn-secondary btn-sm" onclick="window.FinanceiroView.abrirModalAjustarFechamento(window.FinanceiroView.faturaAtiva)">
            ✏️ AJUSTAR FECHAMENTO REAL
          </button>
          <button class="btn btn-primary btn-sm" onclick="window.FinanceiroView.abrirModalLancarDespesaCartao(window.FinanceiroView.cartaoAtivo, window.FinanceiroView.faturaAtiva)">
            + LANÇAR COMPRA NESTA FATURA
          </button>
          <button class="btn btn-secondary btn-sm" style="border-color: var(--color-rust-orange); color: var(--color-rust-orange);" onclick="window.FinanceiroView.fecharFaturaConfirmacao(window.FinanceiroView.faturaAtiva)">
            🔒 FECHAR FATURA
          </button>
        `;
      } else if (f.status === 'FECHADA') {
        acoesHtml = `
          <button class="btn btn-primary btn-sm" style="background-color: var(--color-success); border-color: var(--color-success);" onclick="window.FinanceiroView.abrirModalLiquidarFatura(window.FinanceiroView.faturaAtiva)">
            💰 LIQUIDAR / PAGAR FATURA
          </button>
        `;
      } else if (f.status === 'PAGA') {
        acoesHtml = `
          <span class="status-chip success" style="font-size: 12px; padding: 6px 12px;">
            ✅ FATURA INTEGRALMENTE QUITADA
          </span>
        `;
      }

      let tabelaItensHtml = '';
      if (!itens.length) {
        tabelaItensHtml = `
          <tr>
            <td colspan="8" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">
              Nenhuma despesa ou compra alocada nesta competência.
            </td>
          </tr>
        `;
      } else {
        tabelaItensHtml = itens.map(item => {
          const dtCompetencia = item.data_competencia || item.data_vencimento;
          const parcelaTag = item.total_parcelas > 1 ? `${item.numero_parcela}/${item.total_parcelas}` : 'ÚNICA';
          const anexoHtml = item.comprovante ? `
            <a href="${item.comprovante}" target="_blank" rel="noopener noreferrer" class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 10px;" title="Ver Anexo / NF">
              📎 VER
            </a>
          ` : '<span class="mono-text" style="color: var(--color-outline);">-</span>';

          const remanejarBtn = (f.status === 'ABERTA') ? `
            <button class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 10px;" onclick="window.FinanceiroView.abrirModalRemanejarDespesa(${item.id})">
              REMANEJAR
            </button>
          ` : '-';

          return `
            <tr>
              <td class="mono-text">#${item.id}</td>
              <td class="mono-text">${window.EMCUtils.formatarDataPtBr(dtCompetencia)}</td>
              <td><strong>${window.EMCUtils.escapeHtml(item.descricao)}</strong></td>
              <td><span class="status-chip info" style="font-size: 9px;">${window.EMCUtils.escapeHtml(item.categoria?.nome || 'CATEGORIA')}</span></td>
              <td class="mono-text" style="text-align: center;"><span class="badge-parcela">${parcelaTag}</span></td>
              <td class="mono-text font-bold" style="color: var(--color-error); text-align: right;">
                ${window.EMCUtils.formatarMoeda(item.valor)}
              </td>
              <td style="text-align: center;">${anexoHtml}</td>
              <td style="text-align: right;">${remanejarBtn}</td>
            </tr>
          `;
        }).join('');
      }

      detalheContainer.innerHTML = `
        <!-- Cabeçalho de Dados da Fatura Ativa -->
        <div style="background-color: var(--color-surface-container); padding: 12px 16px; margin-bottom: 16px; border-left: 4px solid var(--color-rust-orange);">
          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <h4 style="margin: 0; font-size: 16px; font-weight: 700;">COMPETÊNCIA ${f.mes_referencia}</h4>
                <span class="status-chip ${statusBadge}">${f.status}</span>
              </div>
              <div class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 4px;">
                Corte / Fechamento Real: <strong>${window.EMCUtils.formatarDataPtBr(f.data_fechamento_real)}</strong> | 
                Vencimento do Pagamento: <strong>${window.EMCUtils.formatarDataPtBr(f.data_vencimento_calculada || f.data_fechamento_real)}</strong>
              </div>
            </div>

            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
              <div style="text-align: right;">
                <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">TOTAL DA FATURA</div>
                <div class="mono-text font-bold" style="font-size: 18px; color: var(--color-error);">
                  ${window.EMCUtils.formatarMoeda(f.total_despesas || 0)}
                </div>
              </div>
              <div style="display: flex; gap: 6px; flex-wrap: wrap;">
                ${acoesHtml}
              </div>
            </div>
          </div>
        </div>

        <!-- Tabela de Compras / Despesas da Fatura -->
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th style="width: 60px;">ID</th>
                <th style="width: 110px;">DATA COMPRA</th>
                <th>DESCRIÇÃO / HISTÓRICO</th>
                <th>CATEGORIA</th>
                <th style="width: 80px; text-align: center;">PARCELA</th>
                <th style="width: 120px; text-align: right;">VALOR</th>
                <th style="width: 90px; text-align: center;">ANEXO</th>
                <th style="width: 100px; text-align: right;">AÇÕES</th>
              </tr>
            </thead>
            <tbody>
              ${tabelaItensHtml}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      detalheContainer.innerHTML = `<div style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</div>`;
    }
  },

  // --------------------------------------------------------------------------
  // Modais de Cartões e Faturas
  // --------------------------------------------------------------------------
  async abrirModalNovoCartao(cartaoEdicao = null) {
    const isEdicao = !!cartaoEdicao;

    // Se for edição, obtém dados atualizados diretamente da API REST
    let cartao = cartaoEdicao;
    if (isEdicao && cartaoEdicao?.id) {
      try {
        const fresco = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO}${cartaoEdicao.id}/`);
        if (fresco && fresco.id) {
          cartao = fresco;
          this.cartaoAtivo = fresco;
          const idx = this.cartoesLista.findIndex(c => c.id === fresco.id);
          if (idx !== -1) {
            this.cartoesLista[idx] = fresco;
          }
        }
      } catch (err) {
        console.warn('Erro ao obter dados frescos do cartão:', err);
      }
    }

    const resContas = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS);
    const listaContas = resContas.results || (Array.isArray(resContas) ? resContas : []);

    const contaIdAtual = cartao?.conta_bancaria_id ?? 
                         (typeof cartao?.conta_bancaria === 'object' ? cartao?.conta_bancaria?.id : cartao?.conta_bancaria) ?? 
                         null;

    let optsContas = '<option value="">-- NENHUMA (SEM DÉBITO EM CONTA) --</option>';
    listaContas.forEach(c => {
      const isSelected = contaIdAtual !== null && contaIdAtual !== undefined && String(c.id) === String(contaIdAtual);
      optsContas += `<option value="${c.id}" ${isSelected ? 'selected' : ''}>${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`;
    });

    const dHoje = new Date();
    const mesAtual = dHoje.toISOString().substring(0, 7);
    const dProx = new Date(dHoje.getFullYear(), dHoje.getMonth() + 1, 1);
    const mesProximo = dProx.toISOString().substring(0, 7);

    window.EMCUtils.openModal({
      title: isEdicao ? `EDITAR CARTÃO CORPORATIVO #${cartao.id}` : 'NOVO CARTÃO CORPORATIVO',
      size: 'md',
      confirmText: isEdicao ? 'SALVAR ALTERAÇÕES' : 'CADASTRAR CARTÃO',
      content: `
        <div class="form-group">
          <label class="form-label">Identificação / Nome do Cartão *</label>
          <input type="text" id="cartao-nome" class="form-control" placeholder="EX: VISA CORPORATIVO DIRETORIA" value="${cartao ? window.EMCUtils.escapeHtml(cartao.nome) : ''}" required autofocus>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
          <div class="form-group">
            <label class="form-label">Dia de Fechamento Padrão (1 a 31) *</label>
            <input type="number" min="1" max="31" id="cartao-dia-fech" class="form-control mono-text" value="${cartao?.dia_fechamento_padrao || 20}" required>
          </div>
          <div class="form-group">
            <label class="form-label">Dia de Vencimento (1 a 31) *</label>
            <input type="number" min="1" max="31" id="cartao-dia-venc" class="form-control mono-text" value="${cartao?.dia_vencimento || 28}" required>
          </div>
        </div>

        <div class="form-group">
          <label class="form-label">Limite Total Contratual (R$) *</label>
          <input type="text" id="cartao-limite" class="form-control mono-text" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(cartao?.limite || 5000)}">
        </div>

        <div class="form-group">
          <label class="form-label">Conta Bancária Preferencial de Débito</label>
          <select id="cartao-conta-pref" class="form-control">${optsContas}</select>
        </div>

        <div class="form-group" style="margin-bottom: 0;">
          <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-size: 13px;">
            <input type="checkbox" id="cartao-permite-emergencial" ${cartao?.permite_limite_emergencial ? 'checked' : ''}>
            Permitir Limite Emergencial (Não travar compras que ultrapassem o limite)
          </label>
        </div>

        ${isEdicao ? `
          <div style="background: var(--color-surface-container); border: 1px solid var(--color-outline-variant); border-left: 3px solid var(--color-rust-orange); padding: 12px; margin-top: 14px;">
            <label class="form-label" style="display: flex; align-items: center; gap: 6px; color: var(--color-rust-orange); font-weight: 700; margin-bottom: 4px;">
              ⚡ REPERCUSSÃO NAS FATURAS EXISTENTES
            </label>
            <div style="font-size: 11.5px; color: var(--color-on-surface-variant); margin-bottom: 8px; line-height: 1.4;">
              Ao alterar os dias de fechamento ou vencimento, escolha a partir de qual competência as faturas devem ser recalculadas e seus lançamentos remanejados:
            </div>
            <select id="cartao-escopo-recalculo" class="form-control" style="font-size: 12.5px;">
              <option value="ATUAL">A partir da competência atual (${mesAtual}) e futuras</option>
              <option value="PROXIMA">A partir da próxima competência (${mesProximo}) e futuras</option>
              <option value="ESPECIFICA">A partir de uma competência específica...</option>
            </select>
            <div id="wrapper-competencia-especifica" style="display: none; margin-top: 8px;">
              <label class="form-label">Competência Inicial para Recálculo (Mês/Ano) *</label>
              <input type="month" id="cartao-mes-especifico" class="form-control mono-text font-bold" value="${mesAtual}" style="max-width: 220px;">
              <small style="color: var(--color-on-surface-variant); font-size: 11px; display: block; margin-top: 4px;">
                Permite selecionar qualquer competência retroativa ou futura (formato AAAA-MM).
              </small>
            </div>
          </div>
        ` : ''}
      `,
      onConfirm: async () => {
        const nome = document.getElementById('cartao-nome')?.value.trim();
        const dia_fechamento_padrao = parseInt(document.getElementById('cartao-dia-fech')?.value, 10);
        const dia_vencimento = parseInt(document.getElementById('cartao-dia-venc')?.value, 10);
        const limite = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('cartao-limite')?.value || '0');
        const conta_bancaria_id = document.getElementById('cartao-conta-pref')?.value || null;
        const permite_limite_emergencial = document.getElementById('cartao-permite-emergencial')?.checked || false;

        if (!nome || !dia_fechamento_padrao || !dia_vencimento || limite <= 0) {
          window.EMCUtils.showToast('Preencha corretamente os campos obrigatórios.', 'warning');
          return false;
        }

        let recalcular_faturas = false;
        let competencia_inicial_recalculo = null;
        let confirmar_retroativo_fechadas = false;

        if (isEdicao) {
          const escopo = document.getElementById('cartao-escopo-recalculo')?.value || 'ATUAL';
          recalcular_faturas = true;
          if (escopo === 'ATUAL') {
            competencia_inicial_recalculo = mesAtual;
          } else if (escopo === 'PROXIMA') {
            competencia_inicial_recalculo = mesProximo;
          } else if (escopo === 'ESPECIFICA') {
            competencia_inicial_recalculo = document.getElementById('cartao-mes-especifico')?.value || mesAtual;
          }

          // Verificação prévia de faturas fechadas ou pagas no escopo
          try {
            const resFat = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO}${cartao.id}/faturas/`);
            const listaFat = resFat.results || (Array.isArray(resFat) ? resFat : []);
            const faturasAfetadas = listaFat.filter(f => f.mes_referencia >= competencia_inicial_recalculo && (f.status === 'FECHADA' || f.status === 'PAGA'));

            if (faturasAfetadas.length > 0) {
              const htmlFaturas = faturasAfetadas.map(f => `• Competência ${f.mes_referencia} (${f.status}) - Fechamento: ${window.EMCUtils.formatarDataPtBr(f.data_fechamento_real)}`).join('<br>');
              const confirmar = await new Promise((resolve) => {
                window.EMCUtils.openModal({
                  title: '⚠️ ALERTA: FATURAS FECHADAS OU PAGAS AFETADAS',
                  size: 'md',
                  confirmText: 'CONFIRMAR E RECALCULAR MESMO ASSIM',
                  cancelText: 'CANCELAR ALTERAÇÃO',
                  content: `
                    <div style="background: var(--color-surface-container); border: 1px solid var(--color-error); border-left: 4px solid var(--color-error); padding: 12px; margin-bottom: 14px;">
                      <div style="color: var(--color-error); font-weight: 700; font-size: 13px; margin-bottom: 6px;">
                        ⚡ ATENÇÃO: A alteração atingirá faturas com ciclo já encerrado!
                      </div>
                      <div style="font-size: 12px; color: var(--color-on-surface); line-height: 1.5; margin-bottom: 10px;">
                        Foram identificadas <strong>${faturasAfetadas.length}</strong> fatura(s) com status <strong>FECHADA</strong> ou <strong>PAGA</strong> a partir da competência <strong>${competencia_inicial_recalculo}</strong>:
                      </div>
                      <div class="mono-text" style="font-size: 11.5px; background: var(--color-surface); padding: 8px; border: 1px solid var(--color-outline-variant); margin-bottom: 12px;">
                        ${htmlFaturas}
                      </div>
                      <div style="font-size: 11.5px; color: var(--color-on-surface-variant); line-height: 1.4;">
                        <strong>Consequências desta ação:</strong>
                        <ul style="margin: 4px 0 0 16px; padding: 0;">
                          <li><strong>Faturas Fechadas:</strong> O valor consolidado no título de Contas a Pagar será recalculado com o novo total decorrente das compras que saíram ou entraram.</li>
                          <li><strong>Faturas Pagas:</strong> A fatura já possui liquidação financeira registrada no banco/caixa. Mover compras de/para uma fatura já paga gerará divergência em relação ao valor já debitado do extrato bancário.</li>
                        </ul>
                      </div>
                    </div>
                    <div style="font-size: 12.5px; font-weight: 600; text-align: center; color: var(--color-on-surface);">
                      Deseja prosseguir com o recálculo retroativo mesmo assim?
                    </div>
                  `,
                  onConfirm: () => {
                    resolve(true);
                    return true;
                  },
                  onCancel: () => {
                    resolve(false);
                  }
                });
              });

              if (!confirmar) {
                window.EMCUtils.showToast('Operação cancelada pelo usuário.', 'info');
                return false;
              }
              confirmar_retroativo_fechadas = true;
            }
          } catch (errCheck) {
            console.warn('Erro ao verificar faturas fechadas:', errCheck);
          }
        }

        const payload = {
          nome,
          dia_fechamento_padrao,
          dia_vencimento,
          limite,
          conta_bancaria: conta_bancaria_id ? Number(conta_bancaria_id) : null,
          conta_bancaria_id: conta_bancaria_id ? Number(conta_bancaria_id) : null,
          permite_limite_emergencial,
          recalcular_faturas,
          competencia_inicial_recalculo,
          confirmar_retroativo_fechadas
        };

        try {
          let cartaoIdFinal = cartao?.id;
          if (isEdicao) {
            const resp = await window.api.put(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO}${cartao.id}/`, payload);
            let msg = 'Cartão atualizado com sucesso!';
            if (resp?.recalculo && resp.recalculo.faturas_recalculadas > 0) {
              msg += ` ${resp.recalculo.faturas_recalculadas} fatura(s) recalculada(s) a partir de ${resp.recalculo.competencia_inicial}.`;
            }
            window.EMCUtils.showToast(msg, 'success');
          } else {
            const novo = await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO, payload);
            window.EMCUtils.showToast('Cartão cadastrado com sucesso!', 'success');
            cartaoIdFinal = novo?.id;
          }
          await this.carregarListaCartoes(cartaoIdFinal);
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao salvar cartão.', 'error');
          return false;
        }
      }
    });

    setTimeout(() => {
      const selectConta = document.getElementById('cartao-conta-pref');
      if (selectConta && contaIdAtual !== null && contaIdAtual !== undefined) {
        selectConta.value = String(contaIdAtual);
      }
      if (isEdicao) {
        const escopoSelect = document.getElementById('cartao-escopo-recalculo');
        const wrapperEsp = document.getElementById('wrapper-competencia-especifica');
        if (escopoSelect && wrapperEsp) {
          escopoSelect.addEventListener('change', () => {
            wrapperEsp.style.display = escopoSelect.value === 'ESPECIFICA' ? 'block' : 'none';
          });
        }
      }
    }, 50);
  },

  abrirModalAjustarFechamento(fatura) {
    window.EMCUtils.openModal({
      title: `AJUSTE DE FECHAMENTO REAL - FATURA ${fatura.mes_referencia}`,
      size: 'md',
      confirmText: 'CONFIRMAR E RECALCULAR ITENS',
      content: `
        <div style="background-color: var(--color-surface-container); border-left: 3px solid var(--color-rust-orange); padding: 10px 12px; margin-bottom: 16px; font-size: 12px; line-height: 1.5;">
          ⚡ <strong>Recálculo Automatizado:</strong> Ao alterar a data de fechamento real desta fatura:
          <ul style="margin: 6px 0 0 16px; padding: 0;">
            <li>Se <strong>antecipar</strong> o fechamento, compras realizadas após a nova data serão transferidas automaticamente para a próxima fatura em aberto.</li>
            <li>Se <strong>postergar</strong> o fechamento, compras já registradas na próxima fatura dentro do novo intervalo serão puxadas de volta para esta fatura.</li>
          </ul>
        </div>

        <div class="form-group">
          <label class="form-label">Data de Fechamento Real Vigente</label>
          <input type="text" class="form-control mono-text" value="${window.EMCUtils.formatarDataPtBr(fatura.data_fechamento_real)}" disabled>
        </div>

        <div class="form-group">
          <label class="form-label">Nova Data de Fechamento Real *</label>
          <input type="date" id="nova-data-fechamento" class="form-control mono-text" value="${fatura.data_fechamento_real}" required autofocus>
        </div>
      `,
      onConfirm: async () => {
        const novaData = document.getElementById('nova-data-fechamento')?.value;
        if (!novaData) return false;

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FINANCEIRO.AJUSTAR_FECHAMENTO.replace('{id}', fatura.id);
          const res = await window.api.post(endpoint, { data_fechamento_real: novaData });

          const dados = res.dados || res;
          let msg = 'Fechamento ajustado com sucesso!';
          if (dados.itens_movidos_adiante > 0) {
            msg += ` ${dados.itens_movidos_adiante} compra(s) transferida(s) para a próxima fatura.`;
          }
          if (dados.itens_puxados_de_volta > 0) {
            msg += ` ${dados.itens_puxados_de_volta} compra(s) puxada(s) de volta para esta fatura.`;
          }

          window.EMCUtils.showToast(msg, 'success');
          await this.carregarMetricasEFaturasCartao();
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao ajustar fechamento da fatura.', 'error');
          return false;
        }
      }
    });
  },

  async fecharFaturaConfirmacao(fatura) {
    const valorFormatado = window.EMCUtils.formatarMoeda(fatura.total_despesas || 0);
    const mesRef = fatura.mes_referencia || 'COMPETÊNCIA ATUAL';
    const cartaoNome = this.cartaoAtivo?.nome_identificador || 'CARTÃO CORPORATIVO';

    const contentHtml = `
      <div style="padding: 4px 0;">
        <p style="font-size: 13.5px; line-height: 1.5; margin-bottom: 14px; color: var(--color-on-surface);">
          Confirma o fechamento definitivo da fatura com os dados consolidados abaixo?
        </p>

        <div class="card p-12 mb-16" style="background-color: var(--color-surface-container-low); border: 1px solid var(--color-steel-gray);">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 11px; font-family: var(--font-mono); color: var(--color-on-surface-variant); text-transform: uppercase;">CARTÃO</span>
            <strong style="font-size: 13px;">${window.EMCUtils.escapeHtml(cartaoNome)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
            <span style="font-size: 11px; font-family: var(--font-mono); color: var(--color-on-surface-variant); text-transform: uppercase;">COMPETÊNCIA</span>
            <span class="status-chip info" style="font-size: 11px; font-weight: 700;">${window.EMCUtils.escapeHtml(mesRef)}</span>
          </div>
          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px dashed var(--color-steel-gray); padding-top: 8px; margin-top: 6px;">
            <span style="font-size: 12px; font-weight: 700; color: var(--color-rust-orange);">TOTAL DA FATURA</span>
            <span style="font-family: var(--font-mono); font-size: 16px; font-weight: 800; color: var(--color-on-surface);">${valorFormatado}</span>
          </div>
        </div>

        <div class="alert-banner alert-warning" style="font-size: 12px; line-height: 1.5; margin-bottom: 0;">
          <strong>[INTEGRAÇÃO CONTÁBIL]</strong> Ao confirmar o fechamento, as despesas da competência serão consolidadas e será gerado automaticamente um título a pagar no <strong>Contas a Pagar</strong>.
        </div>
      </div>
    `;

    const confirmado = await window.EMCUtils.confirmDialog({
      title: `FECHAMENTO DE FATURA - ${mesRef}`,
      contentHtml,
      confirmText: 'CONFIRMAR FECHAMENTO',
      cancelText: 'CANCELAR',
      confirmVariant: 'primary',
      size: 'sm'
    });

    if (!confirmado) return;

    try {
      const endpoint = window.CONFIG.ENDPOINTS.FINANCEIRO.FECHAR_FATURA.replace('{id}', fatura.id);
      await window.api.post(endpoint, {});
      window.EMCUtils.showToast(`Fatura ${fatura.mes_referencia} fechada com sucesso! Título gerado no Contas a Pagar.`, 'success');
      await this.carregarMetricasEFaturasCartao();
    } catch (e) {
      window.EMCUtils.showToast(e.message || 'Erro ao fechar fatura.', 'error');
    }
  },

  async abrirModalLiquidarFatura(fatura) {
    const resContas = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS);
    const listaContas = resContas.results || (Array.isArray(resContas) ? resContas : []);

    const contaCartaoId = this.cartaoAtivo?.conta_bancaria_id ?? 
                          (typeof this.cartaoAtivo?.conta_bancaria === 'object' ? this.cartaoAtivo?.conta_bancaria?.id : this.cartaoAtivo?.conta_bancaria) ?? 
                          null;

    let optsContas = '<option value="">-- SELECIONE A CONTA BANCÁRIA DE DÉBITO * --</option>';
    listaContas.forEach(c => {
      const selecionada = contaCartaoId !== null && contaCartaoId !== undefined && String(contaCartaoId) === String(c.id) ? 'selected' : '';
      optsContas += `<option value="${c.id}" ${selecionada}>${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)} | Limite: ${window.EMCUtils.formatarMoeda(c.limite_credito)})</option>`;
    });

    const valorTotalFatura = parseFloat(fatura.total_despesas || 0);

    window.EMCUtils.openModal({
      title: `LIQUIDAÇÃO / PAGAMENTO DA FATURA ${fatura.mes_referencia}`,
      size: 'md',
      confirmText: 'CONFIRMAR PAGAMENTO',
      content: `
        <div style="background-color: var(--color-surface-container); border-left: 3px solid var(--color-success); padding: 10px 12px; margin-bottom: 16px; font-size: 12px; line-height: 1.5;">
          💳 <strong>Pagamento Total ou Parcial (Rollover):</strong>
          Caso pague um valor inferior ao total da fatura (R$ ${window.EMCUtils.formatarMoeda(valorTotalFatura)}), o saldo remanescente será automaticamente transferido como encargo/rollover para a fatura do mês seguinte.
        </div>

        <div class="form-group">
          <label class="form-label">Valor Total da Fatura</label>
          <input type="text" class="form-control mono-text" value="${window.EMCUtils.formatarMoeda(valorTotalFatura)}" disabled>
        </div>

        <div class="form-group">
          <label class="form-label">Valor a Liquidar (R$) *</label>
          <input type="text" id="liq-fatura-valor" class="form-control mono-text font-bold" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(valorTotalFatura)}" required>
        </div>

        <div class="form-group">
          <label class="form-label">Conta Bancária de Saída *</label>
          <select id="liq-fatura-conta" class="form-control" required>${optsContas}</select>
        </div>

        <div class="form-group">
          <label class="form-label">Data do Pagamento *</label>
          <input type="date" id="liq-fatura-data" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
        </div>

        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Comprovante de Pagamento (Opcional)</label>
          <input type="file" id="liq-fatura-comprovante" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.xml,.csv,.txt">
        </div>
      `,
      onConfirm: async () => {
        const valorPago = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('liq-fatura-valor')?.value || '0');
        const contaId = document.getElementById('liq-fatura-conta')?.value;
        const dataPagamento = document.getElementById('liq-fatura-data')?.value;

        if (valorPago <= 0 || !contaId || !dataPagamento) {
          window.EMCUtils.showToast('Preencha os campos obrigatórios.', 'warning');
          return false;
        }

        let comprovantePath = null;
        let nomeComprovante = null;

        const fileInput = document.getElementById('liq-fatura-comprovante');
        if (fileInput?.files?.length > 0) {
          try {
            window.EMCUtils.showToast('Enviando comprovante de pagamento...', 'info');
            const formData = new FormData();
            formData.append('arquivo', fileInput.files[0]);
            const resUp = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
            comprovantePath = resUp.comprovante_path;
            nomeComprovante = resUp.nome_arquivo_comprovante;
          } catch (errUp) {
            window.EMCUtils.showToast(`Erro ao enviar comprovante: ${errUp.message}`, 'error');
            return false;
          }
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FINANCEIRO.LIQUIDAR_FATURA.replace('{id}', fatura.id);
          const payload = {
            valor_pago: valorPago,
            conta_id: Number(contaId),
            data_pagamento: `${dataPagamento}T12:00:00`,
            comprovante: comprovantePath,
            nome_arquivo_comprovante: nomeComprovante
          };

          await window.api.post(endpoint, payload);
          window.EMCUtils.showToast('Fatura liquidada com sucesso! Débito efetuado em conta bancária.', 'success');
          await this.carregarMetricasEFaturasCartao();
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao liquidar fatura.', 'error');
          return false;
        }
      }
    });

    setTimeout(() => {
      const selectConta = document.getElementById('liq-fatura-conta');
      if (selectConta && contaCartaoId !== null && contaCartaoId !== undefined) {
        selectConta.value = String(contaCartaoId);
      }
    }, 50);
  },

  async abrirModalLancarDespesaCartao(cartao, fatura = null) {
    const resCat = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS}?ativo=true`);
    const listaCat = resCat.results || (Array.isArray(resCat) ? resCat : []);
    const catsDespesa = listaCat.filter(c => c.tipo === 'DESPESA' || c.tipo === 'AMBOS');

    let optsCat = '<option value="">-- SELECIONE A CATEGORIA DRE * --</option>';
    catsDespesa.forEach(c => {
      optsCat += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)}</option>`;
    });

    window.EMCUtils.openModal({
      title: `LANÇAR COMPRA NO CARTÃO ${cartao.nome}`,
      size: 'md',
      confirmText: 'REGISTRAR COMPRA',
      content: `
        <div class="form-group">
          <label class="form-label">Descrição / Histórico da Compra *</label>
          <input type="text" id="cd-desc" class="form-control" placeholder="EX: COMPRA DE ELETRODOS E DISCOS DE CORTE" required autofocus>
        </div>

        <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 10px;">
          <div class="form-group">
            <label class="form-label">Valor Total da Compra (R$) *</label>
            <input type="text" id="cd-valor" class="form-control mono-text font-bold" data-mask="moeda-atm" value="R$ 0,00" required>
          </div>
          <div class="form-group">
            <label class="form-label">Número de Parcelas *</label>
            <select id="cd-parcelas" class="form-control mono-text">
              <option value="1">1x (À vista no cartão)</option>
              <option value="2">2x</option>
              <option value="3">3x</option>
              <option value="4">4x</option>
              <option value="5">5x</option>
              <option value="6">6x</option>
              <option value="10">10x</option>
              <option value="12">12x</option>
            </select>
          </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 140px; gap: 10px;">
          <div class="form-group">
            <label class="form-label">Categoria DRE *</label>
            <select id="cd-cat" class="form-control" required>${optsCat}</select>
          </div>
          <div class="form-group">
            <label class="form-label">Data da Compra *</label>
            <input type="date" id="cd-data" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
          </div>
        </div>

        <div class="form-group" style="margin-bottom: 0;">
          <label class="form-label">Anexar Comprovante / Nota Fiscal (Opcional)</label>
          <input type="file" id="cd-comprovante" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.xml,.csv,.txt">
        </div>
      `,
      onConfirm: async () => {
        const descricao = document.getElementById('cd-desc')?.value.trim();
        const valor = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('cd-valor')?.value || '0');
        const totalParcelas = parseInt(document.getElementById('cd-parcelas')?.value || '1', 10);
        const categoriaId = document.getElementById('cd-cat')?.value;
        const dataCompra = document.getElementById('cd-data')?.value;

        if (!descricao || valor <= 0 || !categoriaId || !dataCompra) {
          window.EMCUtils.showToast('Preencha os campos obrigatórios.', 'warning');
          return false;
        }

        let comprovantePath = null;
        let nomeComprovante = null;

        const fileInput = document.getElementById('cd-comprovante');
        if (fileInput?.files?.length > 0) {
          try {
            window.EMCUtils.showToast('Enviando anexo da compra...', 'info');
            const formData = new FormData();
            formData.append('arquivo', fileInput.files[0]);
            const resUp = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
            comprovantePath = resUp.comprovante_path;
            nomeComprovante = resUp.nome_arquivo_comprovante;
          } catch (errUp) {
            window.EMCUtils.showToast(`Erro ao enviar anexo: ${errUp.message}`, 'error');
            return false;
          }
        }

        try {
          // Utiliza o endpoint lancar-multi-meio para consistência total com N parcelas e comprovante único
          const payload = {
            descricao,
            categoria_id: Number(categoriaId),
            valor_total: valor,
            data_compra: dataCompra,
            comprovante: comprovantePath,
            nome_arquivo_comprovante: nomeComprovante,
            matriz_pagamentos: [
              {
                tipo_meio: 'CARTAO',
                cartao_id: cartao.id,
                total_parcelas: totalParcelas,
                valor: valor,
                descricao: `COMPRA CARTÃO ${cartao.nome}`
              }
            ]
          };

          await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAR_MULTI_MEIO, payload);
          window.EMCUtils.showToast(`Compra de R$ ${window.EMCUtils.formatarMoeda(valor)} registrada com sucesso em ${totalParcelas}x!`, 'success');
          await this.carregarMetricasEFaturasCartao();
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao registrar compra no cartão.', 'error');
          return false;
        }
      }
    });
  },

  async abrirModalRemanejarDespesa(lancamentoId) {
    if (!this.faturasLista.length) return;

    let optsFaturas = '<option value="">-- SELECIONE A NOVA FATURA DESTINO --</option>';
    this.faturasLista.filter(f => f.status === 'ABERTA' && f.id !== this.faturaAtiva?.id).forEach(f => {
      optsFaturas += `<option value="${f.id}">Fatura ${f.mes_referencia} (Fechamento: ${window.EMCUtils.formatarDataPtBr(f.data_fechamento_real)})</option>`;
    });

    window.EMCUtils.openModal({
      title: `REMANEJAR DESPESA #${lancamentoId}`,
      size: 'sm',
      confirmText: 'TRANSFERIR COMPETÊNCIA',
      content: `
        <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-bottom: 12px;">
          Transfira esta compra para outra fatura em aberto deste cartão.
        </p>
        <div class="form-group">
          <label class="form-label">Nova Fatura Aberta *</label>
          <select id="reman-fatura-id" class="form-control">${optsFaturas}</select>
        </div>
      `,
      onConfirm: async () => {
        const novaFaturaId = document.getElementById('reman-fatura-id')?.value;
        if (!novaFaturaId) {
          window.EMCUtils.showToast('Selecione a fatura de destino.', 'warning');
          return false;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FINANCEIRO.REMANEJAR_DESPESA.replace('{id}', lancamentoId);
          await window.api.post(endpoint, { nova_fatura_cartao_id: Number(novaFaturaId) });
          window.EMCUtils.showToast('Despesa remanejada com sucesso!', 'success');
          await this.carregarMetricasEFaturasCartao();
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao remanejar despesa.', 'error');
          return false;
        }
      }
    });
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
    const l = (this.extratoListaAtual || []).find((x) => x.id === lancamentoId);
    const isContaAgendada = l ? (l.eh_conta_agendada || ['AGENDA', 'FATURA', 'CARTAO'].includes(l.origem)) : false;

    window.EMCUtils.openModal({
      title: `ESTORNO DE LANÇAMENTO #${lancamentoId}`,
      size: 'sm',
      confirmText: 'CONFIRMAR ESTORNO',
      content: `
        <div style="background-color: var(--color-surface-container); border-left: 3px solid ${isContaAgendada ? 'var(--color-warning)' : 'var(--color-primary)'}; padding: 10px 12px; margin-bottom: 12px; font-size: 12px; line-height: 1.4; color: var(--color-on-surface);">
          ${isContaAgendada ? `
            ⚡ <strong>Conta Liquidada:</strong> Este lançamento foi originado de uma <strong>Conta a Pagar/Receber</strong> agendada. Ao estornar, o saldo bancário será revertido e o título voltará para o estado <strong>"NÃO PAGO" (A Vencer)</strong> na sua agenda financeira.
          ` : `
            ⚡ <strong>Lançamento Avulso (Compra Direta):</strong> Esta movimentação foi liquidada no ato da compra e não possui conta agendada. Ao estornar, o saldo bancário será revertido e o lançamento será <strong>excluído</strong> (não gerará conta a pagar pendente).
          `}
        </div>
        <p style="color: var(--color-on-surface-variant); font-size: 12px; margin-bottom: 12px;">
          O estorno gravará compulsoriamente a justificativa no log perpétuo de auditoria.
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
          const res = await window.api.post(endpoint, { justificativa });
          window.EMCUtils.showToast(res.message || 'Lançamento estornado e saldo bancário revertido!', 'success');
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
    const [contas, categorias, meios, cartoes] = await Promise.all([
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS),
      window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS}?ativo=true`),
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.MEIOS_PAGAMENTO),
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CARTOES_CREDITO).catch(() => [])
    ]);

    const listaContas = contas.results || contas || [];
    const listaCat = categorias.results || categorias || [];
    const listaMeios = meios.results || meios || [];
    const listaCartoes = cartoes.results || cartoes || [];

    let optionsContas = `<option value="">${isExtrato ? 'SELECIONE A CONTA BANCÁRIA / CAIXA *' : 'SELECIONE A CONTA (OPCIONAL)...'}</option>`;
    listaContas.forEach((c) => { optionsContas += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (SALDO: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`; });

    let optionsMeios = '<option value="">SELECIONE O MEIO...</option>';
    listaMeios.forEach((m) => { optionsMeios += `<option value="${m.id}">${window.EMCUtils.escapeHtml(m.nome)}</option>`; });

    let optionsCartoes = '<option value="">-- SELECIONE O CARTÃO (OPCIONAL) --</option>';
    listaCartoes.forEach((c) => {
      const disp = c.limite_disponivel !== undefined ? c.limite_disponivel : c.limite;
      optionsCartoes += `<option value="${c.id}">💳 ${window.EMCUtils.escapeHtml(c.nome)} (Disp: ${window.EMCUtils.formatarMoeda(disp)})</option>`;
    });

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
              <label class="form-label" for="nl-valor">Valor Total (R$) *</label>
              <input type="text" id="nl-valor" class="form-control mono-text font-bold" data-mask="moeda-atm" value="R$ 0,00" required>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="nl-desc">Descrição / Histórico *</label>
            <input type="text" id="nl-desc" class="form-control" placeholder="EX: PAGAMENTO FORNECEDOR / COMPRA BALCÃO" required>
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

          <!-- Chaveamento de Múltiplas Formas de Pagamento (Caixa de Mercado) -->
          <div id="wrapper-toggle-matriz" style="background-color: var(--color-surface-container); border-left: 3px solid var(--color-rust-orange); padding: 10px 12px; margin-bottom: 12px; margin-top: 12px;">
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; font-weight: 700; font-size: 13px; margin: 0;">
              <input type="checkbox" id="nl-toggle-multi-meio">
              DIVIDIR EM MÚLTIPLAS FORMAS DE PAGAMENTO (MATRIZ / CAIXA DE MERCADO)
            </label>
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 4px;">
              Pague parte em dinheiro/PIX e parte no cartão corporativo parcelado, mantendo anexo e rastreabilidade unificados.
            </div>
          </div>

          <!-- 1. Pagamento Simples Tradicional -->
          <div id="container-pagamento-simples">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" for="nl-meio">Meio de Pagamento</label>
                <select id="nl-meio" class="form-control">${optionsMeios}</select>
              </div>
              <div class="form-group" id="wrapper-nl-conta" style="margin-bottom: 0;">
                <label class="form-label" for="nl-conta">Conta Bancária / Caixa ${isExtrato ? '*' : ''}</label>
                <select id="nl-conta" class="form-control" ${isExtrato ? 'required' : ''}>${optionsContas}</select>
              </div>
              <div class="form-group" id="wrapper-nl-cartao" style="margin-bottom: 0; display: ${defaultTipo === 'SAIDA' ? 'block' : 'none'};">
                <label class="form-label" for="nl-cartao">Cartão de Crédito Corporativo</label>
                <select id="nl-cartao" class="form-control">${optionsCartoes}</select>
              </div>
              <div class="form-group" id="wrapper-nl-parcelas" style="margin-bottom: 0; display: none;">
                <label class="form-label" for="nl-parcelas">Número de Parcelas</label>
                <select id="nl-parcelas" class="form-control mono-text">
                  <option value="1">1x (À Vista na Fatura)</option>
                  <option value="2">2x</option>
                  <option value="3">3x</option>
                  <option value="4">4x</option>
                  <option value="5">5x</option>
                  <option value="6">6x</option>
                  <option value="10">10x</option>
                  <option value="12">12x</option>
                </select>
              </div>
            </div>
          </div>

          <!-- 2. Matriz de Pagamentos Multi-Meio -->
          <div id="container-matriz-pagamento" style="display: none; border: 1px solid var(--color-outline-variant); padding: 12px; margin-bottom: 12px; background: var(--color-surface);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <strong style="font-size: 13px;">MATRIZ DE DISTRIBUIÇÃO DO PAGAMENTO:</strong>
              <button type="button" class="btn btn-secondary btn-sm" id="btn-add-forma-pagto">+ ADICIONAR FORMA</button>
            </div>

            <div id="matriz-linhas-container" style="display: flex; flex-direction: column; gap: 8px; margin-bottom: 12px;"></div>

            <!-- Balanço Matemático em Tempo Real -->
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; background: var(--color-surface-container); padding: 8px 12px; border: 1px solid var(--color-outline-variant);" class="mono-text">
              <div>
                <span style="font-size: 10px; color: var(--color-on-surface-variant); display: block;">VALOR DA COMPRA</span>
                <strong id="matriz-display-total" style="font-size: 14px;">R$ 0,00</strong>
              </div>
              <div>
                <span style="font-size: 10px; color: var(--color-on-surface-variant); display: block;">TOTAL ALOCADO</span>
                <strong id="matriz-display-alocado" style="font-size: 14px; color: var(--color-primary);">R$ 0,00</strong>
              </div>
              <div>
                <span style="font-size: 10px; color: var(--color-on-surface-variant); display: block;">DIFERENÇA RESTANTE</span>
                <strong id="matriz-display-diferenca" style="font-size: 14px; color: var(--color-error);">R$ 0,00</strong>
              </div>
            </div>
          </div>

          <div class="form-group" style="margin-bottom: 0; margin-top: 10px;">
            <label class="form-label" for="nl-comprovante">Anexar Comprovante / Nota Fiscal (Único e Reutilizável)</label>
            <input type="file" id="nl-comprovante" class="form-control" accept=".pdf,.png,.jpg,.jpeg,.xml,.csv,.txt">
          </div>
        </form>
      `,
      onConfirm: async () => {
        const tipo_lancamento = document.getElementById('nl-tipo')?.value;
        const valorTotal = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('nl-valor')?.value || '0');
        const descricao = document.getElementById('nl-desc')?.value.trim();
        const categoria_id = document.getElementById('nl-cat')?.value;
        const data_vencimento = document.getElementById('nl-venc')?.value;
        const isMultiMeio = document.getElementById('nl-toggle-multi-meio')?.checked;

        if (!descricao || valorTotal <= 0 || !categoria_id) {
          window.EMCUtils.showToast('Preencha os campos obrigatórios (Descrição, Valor e Categoria).', 'warning');
          return false;
        }

        let comprovantePath = null;
        let nomeComprovante = null;

        const fileInput = document.getElementById('nl-comprovante');
        if (fileInput?.files?.length > 0) {
          try {
            window.EMCUtils.showToast('Enviando comprovante...', 'info');
            const formData = new FormData();
            formData.append('arquivo', fileInput.files[0]);
            const resUp = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_COMPROVANTE, formData);
            comprovantePath = resUp.comprovante_path;
            nomeComprovante = resUp.nome_arquivo_comprovante;
          } catch (errUp) {
            window.EMCUtils.showToast(`Erro ao enviar comprovante: ${errUp.message}`, 'error');
            return false;
          }
        }

        // Fluxo 1: Matriz de Pagamentos Multi-Meio
        if (isMultiMeio) {
          const linhas = document.querySelectorAll('.matriz-pagto-row');
          if (!linhas.length) {
            window.EMCUtils.showToast('Adicione ao menos uma forma de pagamento na matriz.', 'warning');
            return false;
          }

          const matrizPayload = [];
          let somaMatriz = 0;

          for (const row of linhas) {
            const meioId = Number(row.querySelector('.matriz-meio-id')?.value);
            const valorLinha = window.EMCUtils.converterMoedaATMParaFloat(row.querySelector('.matriz-row-valor')?.value || '0');
            somaMatriz += valorLinha;

            if (valorLinha <= 0) {
              window.EMCUtils.showToast('Todas as formas de pagamento devem ter valor maior que zero.', 'warning');
              return false;
            }

            const isCartao = isMeioCartaoCredito(meioId);

            if (isCartao) {
              const cartaoId = row.querySelector('.matriz-cartao-id')?.value;
              const parcelas = parseInt(row.querySelector('.matriz-parcelas')?.value || '1', 10);
              if (!cartaoId) {
                window.EMCUtils.showToast('Selecione o Cartão Corporativo na matriz.', 'warning');
                return false;
              }
              matrizPayload.push({
                tipo_meio: 'CARTAO',
                meio_pagamento_id: meioId,
                cartao_id: Number(cartaoId),
                total_parcelas: parcelas,
                valor: valorLinha,
                descricao: `PARC. CARTAO (${parcelas}X)`
              });
            } else {
              const contaId = row.querySelector('.matriz-conta-id')?.value;
              if (!contaId) {
                window.EMCUtils.showToast('Selecione a Conta Bancária de saída na matriz.', 'warning');
                return false;
              }
              const meioObj = listaMeios.find(m => m.id === meioId);
              matrizPayload.push({
                tipo_meio: 'CONTA',
                meio_pagamento_id: meioId,
                conta_id: Number(contaId),
                valor: valorLinha,
                descricao: `PAGTO ${meioObj?.nome || 'CONTA / CAIXA'}`
              });
            }
          }

          if (Math.abs(somaMatriz - valorTotal) > 0.01) {
            window.EMCUtils.showToast(`A soma da matriz (R$ ${somaMatriz.toFixed(2)}) deve ser exatamente igual ao valor da compra (R$ ${valorTotal.toFixed(2)}).`, 'warning');
            return false;
          }

          const payloadMulti = {
            descricao,
            categoria_id: Number(categoria_id),
            valor_total: valorTotal,
            data_compra: data_vencimento,
            comprovante: comprovantePath,
            nome_arquivo_comprovante: nomeComprovante,
            matriz_pagamentos: matrizPayload
          };

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAR_MULTI_MEIO, payloadMulti);
            window.EMCUtils.showToast(`Compra multi-meio registrada com sucesso (${matrizPayload.length} lançamentos vinculados)!`, 'success');
            if (this.currentTab === 'extrato') this.carregarListaExtrato();
            else if (this.currentTab === 'cartoes') this.carregarMetricasEFaturasCartao();
            else if (this.currentTab === 'pagar') this.carregarListaContasPagar();
            else this.render(document.getElementById('app-root'));
            return true;
          } catch (err) {
            window.EMCUtils.showToast(err.message || 'Erro ao registrar compra multi-meio.', 'error');
            return false;
          }
        }

        // Fluxo 2: Pagamento Simples Convencional
        const cartao_id = document.getElementById('nl-cartao')?.value;
        const parcelas = parseInt(document.getElementById('nl-parcelas')?.value || '1', 10);

        if (tipo_lancamento === 'SAIDA' && cartao_id) {
          const payloadCard = {
            descricao,
            categoria_id: Number(categoria_id),
            valor_total: valorTotal,
            data_compra: data_vencimento,
            comprovante: comprovantePath,
            nome_arquivo_comprovante: nomeComprovante,
            matriz_pagamentos: [{
              tipo_meio: 'CARTAO',
              meio_pagamento_id: meioCartaoCredito ? meioCartaoCredito.id : null,
              cartao_id: Number(cartao_id),
              total_parcelas: parcelas,
              valor: valorTotal,
              descricao: parcelas > 1 ? `PARC. CARTAO (${parcelas}X)` : 'COMPRA CARTAO'
            }]
          };

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAR_MULTI_MEIO, payloadCard);
            window.EMCUtils.showToast(parcelas > 1 ? `Despesa parcelada em ${parcelas}x no cartão com sucesso!` : 'Despesa registrada no cartão com sucesso!', 'success');
            if (this.currentTab === 'extrato') this.carregarListaExtrato();
            else if (this.currentTab === 'cartoes') this.carregarMetricasEFaturasCartao();
            else if (this.currentTab === 'pagar') this.carregarListaContasPagar();
            else this.render(document.getElementById('app-root'));
            return true;
          } catch (err) {
            window.EMCUtils.showToast(err.message || 'Erro ao registrar despesa no cartão.', 'error');
            return false;
          }
        }

        const conta_id = document.getElementById('nl-conta')?.value || null;
        const meio_pagamento_id = document.getElementById('nl-meio')?.value || null;

        if (isExtrato && !conta_id) {
          window.EMCUtils.showToast('Selecione a Conta Bancária / Caixa para o lançamento no Extrato.', 'warning');
          return false;
        }

        const payload = {
          tipo_lancamento,
          valor: valorTotal,
          descricao,
          categoria: parseInt(categoria_id, 10),
          categoria_id: parseInt(categoria_id, 10),
          data_vencimento,
          conta: conta_id ? parseInt(conta_id, 10) : null,
          conta_id: conta_id ? parseInt(conta_id, 10) : null,
          meio_pagamento: meio_pagamento_id ? parseInt(meio_pagamento_id, 10) : null,
          meio_pagamento_id: meio_pagamento_id ? parseInt(meio_pagamento_id, 10) : null,
          comprovante: comprovantePath,
          nome_arquivo_comprovante: nomeComprovante
        };

        if (isExtrato) {
          payload.status_pagamento = 'PAGO';
          payload.data_pagamento = `${data_vencimento}T12:00:00`;
          payload.origem = 'AVULSO';
        } else {
          payload.origem = 'AGENDA';
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

    // Detecção do meio de Cartão de Crédito
    const meioCartaoCredito = listaMeios.find(m => {
      const n = (m.nome || '').toUpperCase();
      return (n.includes('CART') && n.includes('CRED')) || n.includes('CREDITO');
    }) || listaMeios.find(m => (m.nome || '').toUpperCase().includes('CART'));

    const isMeioCartaoCredito = (meioId) => {
      const m = listaMeios.find(x => x.id === Number(meioId));
      if (!m) return false;
      const n = (m.nome || '').toUpperCase();
      return (n.includes('CART') && n.includes('CRED')) || n.includes('CREDITO');
    };

    // Sincronização Reativa do Pagamento Simples
    const selCartao = document.getElementById('nl-cartao');
    const selMeio = document.getElementById('nl-meio');
    const wrapConta = document.getElementById('wrapper-nl-conta');
    const wrapCartao = document.getElementById('wrapper-nl-cartao');
    const wrapParcelas = document.getElementById('wrapper-nl-parcelas');
    const selTipo = document.getElementById('nl-tipo');

    selCartao?.addEventListener('change', () => {
      if (selCartao.value) {
        if (meioCartaoCredito) {
          selMeio.value = String(meioCartaoCredito.id);
          selMeio.disabled = true;
        }
        if (wrapConta) wrapConta.style.display = 'none';
        if (wrapParcelas) wrapParcelas.style.display = 'block';
      } else {
        selMeio.disabled = false;
        selMeio.value = '';
        if (wrapConta) wrapConta.style.display = 'block';
        if (wrapParcelas) wrapParcelas.style.display = 'none';
      }
    });

    selMeio?.addEventListener('change', () => {
      const isCartao = isMeioCartaoCredito(selMeio.value);
      if (isCartao) {
        if (wrapCartao) wrapCartao.style.display = 'block';
        if (wrapParcelas) wrapParcelas.style.display = 'block';
        if (wrapConta) wrapConta.style.display = 'none';
        if (!selCartao.value && listaCartoes.length > 0) {
          selCartao.focus();
        }
      } else if (selMeio.value) {
        // Outro meio selecionado (PIX, Dinheiro, etc.): oculta a opção de cartão de crédito
        if (wrapCartao) {
          wrapCartao.style.display = 'none';
          selCartao.value = '';
        }
        if (wrapParcelas) wrapParcelas.style.display = 'none';
        if (wrapConta) wrapConta.style.display = 'block';
      } else {
        // Meio em branco
        if (selTipo?.value === 'SAIDA') {
          if (wrapCartao) wrapCartao.style.display = 'block';
        }
        if (wrapConta) wrapConta.style.display = 'block';
        if (wrapParcelas) wrapParcelas.style.display = 'none';
      }
    });

    selTipo?.addEventListener('change', () => {
      if (selTipo.value === 'ENTRADA') {
        if (wrapCartao) {
          wrapCartao.style.display = 'none';
          selCartao.value = '';
        }
        if (wrapParcelas) wrapParcelas.style.display = 'none';
        if (wrapConta) wrapConta.style.display = 'block';
        selMeio.disabled = false;
      } else {
        if (!selMeio.value || isMeioCartaoCredito(selMeio.value)) {
          if (wrapCartao) wrapCartao.style.display = 'block';
        }
      }
      atualizarCategoriasDinamicas(selTipo.value);
    });

    // Lógica Dinâmica da Matriz de Pagamentos
    const toggleMatriz = document.getElementById('nl-toggle-multi-meio');
    const boxSimples = document.getElementById('container-pagamento-simples');
    const boxMatriz = document.getElementById('container-matriz-pagamento');
    const matrizLinhas = document.getElementById('matriz-linhas-container');

    const atualizarBalancoMatriz = () => {
      const vTotal = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('nl-valor')?.value || '0');
      let soma = 0;
      document.querySelectorAll('.matriz-row-valor').forEach(inp => {
        soma += window.EMCUtils.converterMoedaATMParaFloat(inp.value || '0');
      });
      const diff = vTotal - soma;

      const dispTotal = document.getElementById('matriz-display-total');
      const dispAlocado = document.getElementById('matriz-display-alocado');
      const dispDiff = document.getElementById('matriz-display-diferenca');

      if (dispTotal) dispTotal.textContent = window.EMCUtils.formatarMoeda(vTotal);
      if (dispAlocado) dispAlocado.textContent = window.EMCUtils.formatarMoeda(soma);
      if (dispDiff) {
        dispDiff.textContent = window.EMCUtils.formatarMoeda(diff);
        dispDiff.style.color = Math.abs(diff) < 0.01 ? 'var(--color-success)' : 'var(--color-error)';
      }
    };

    const adicionarLinhaMatriz = (meioDefaultId = null, valorDefault = 0) => {
      const row = document.createElement('div');
      row.className = 'matriz-pagto-row';
      row.style.cssText = 'display: grid; grid-template-columns: 160px 1fr 130px 36px; gap: 8px; align-items: center; background: var(--color-surface-container); padding: 6px 8px; border: 1px solid var(--color-outline-variant);';

      const optsContasRow = listaContas.map(c => `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`).join('');
      const optsCartoesRow = listaCartoes.map(c => `<option value="${c.id}">💳 ${window.EMCUtils.escapeHtml(c.nome)}</option>`).join('');

      let defaultId = meioDefaultId;
      if (!defaultId && listaMeios.length > 0) {
        const d = listaMeios.find(m => (m.nome || '').toUpperCase().includes('DINH')) ||
                  listaMeios.find(m => (m.nome || '').toUpperCase().includes('PIX')) ||
                  listaMeios[0];
        defaultId = d ? d.id : null;
      }

      row.innerHTML = `
        <select class="form-control matriz-meio-id" style="font-size: 11.5px;">
          ${listaMeios.map(m => `<option value="${m.id}" ${String(m.id) === String(defaultId) ? 'selected' : ''}>${window.EMCUtils.escapeHtml(m.nome)}</option>`).join('')}
        </select>

        <div class="matriz-alvo-container">
          <!-- Renderizado dinamicamente -->
        </div>

        <input type="text" class="form-control mono-text matriz-row-valor font-bold" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(valorDefault)}">

        <button type="button" class="btn btn-secondary btn-sm btn-remover-linha-matriz" style="color: var(--color-error); padding: 4px;" title="Remover Forma">✕</button>
      `;

      const alvoContainer = row.querySelector('.matriz-alvo-container');
      const meioSelect = row.querySelector('.matriz-meio-id');

      const renderAlvo = (selectedMeioId) => {
        const isCartao = isMeioCartaoCredito(selectedMeioId);
        if (isCartao) {
          alvoContainer.innerHTML = `
            <div style="display: grid; grid-template-columns: 1fr 90px; gap: 6px;">
              <select class="form-control matriz-cartao-id" style="font-size: 11.5px;">${optsCartoesRow || '<option value="">NENHUM CARTÃO CADASTRADO</option>'}</select>
              <select class="form-control mono-text matriz-parcelas" style="font-size: 11.5px;">
                <option value="1">1x</option>
                <option value="2">2x</option>
                <option value="3">3x</option>
                <option value="4">4x</option>
                <option value="5">5x</option>
                <option value="6">6x</option>
                <option value="10">10x</option>
                <option value="12">12x</option>
              </select>
            </div>
          `;
        } else {
          alvoContainer.innerHTML = `
            <select class="form-control matriz-conta-id" style="font-size: 11.5px;">${optsContasRow || '<option value="">NENHUMA CONTA CADASTRADA</option>'}</select>
          `;
        }
      };

      meioSelect.addEventListener('change', (e) => renderAlvo(e.target.value));
      renderAlvo(defaultId);

      row.querySelector('.matriz-row-valor').addEventListener('input', atualizarBalancoMatriz);
      row.querySelector('.btn-remover-linha-matriz').addEventListener('click', () => {
        row.remove();
        atualizarBalancoMatriz();
      });

      matrizLinhas.appendChild(row);
      window.EMCUtils.aplicarMascaras();
      atualizarBalancoMatriz();
    };

    toggleMatriz?.addEventListener('change', (e) => {
      const checked = e.target.checked;
      boxSimples.style.display = checked ? 'none' : 'block';
      boxMatriz.style.display = checked ? 'block' : 'none';

      if (checked && !matrizLinhas.children.length) {
        const total = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('nl-valor')?.value || '0');
        adicionarLinhaMatriz(null, total > 0 ? total : 0);
      }
      atualizarBalancoMatriz();
    });

    document.getElementById('btn-add-forma-pagto')?.addEventListener('click', () => {
      const vTotal = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('nl-valor')?.value || '0');
      let soma = 0;
      document.querySelectorAll('.matriz-row-valor').forEach(inp => {
        soma += window.EMCUtils.converterMoedaATMParaFloat(inp.value || '0');
      });
      const restante = Math.max(0, vTotal - soma);
      const defaultMeio = meioCartaoCredito ? meioCartaoCredito.id : null;
      adicionarLinhaMatriz(defaultMeio, restante);
    });

    document.getElementById('nl-valor')?.addEventListener('input', atualizarBalancoMatriz);

    // Filtragem Dinâmica de Categorias com base no Tipo de Movimentação selecionado
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

      if (valorAnterior && filtradas.some((c) => String(c.id) === String(valorAnterior))) {
        selCat.value = valorAnterior;
      }
    };

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
            <span class="status-chip secondary mono-text">STATUS: ${window.EMCUtils.formatarStatus(lancamento.status_pagamento)}</span>
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
