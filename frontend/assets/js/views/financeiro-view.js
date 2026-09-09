/**
 * EMC Soldas - View de Tesouraria e Estruturas Financeiras
 * Contas a Pagar/Receber (Competência), Caixa Real (Extrato), Cartões e Estornos.
 */

window.FinanceiroView = {
  currentTab: 'extrato',

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

    document.getElementById('btn-transferencia-inter')?.addEventListener('click', () => this.abrirModalTransferencia());
    document.getElementById('btn-novo-lancamento')?.addEventListener('click', () => this.abrirModalNovoLancamento());

    const content = document.getElementById('financeiro-tab-content');
    if (this.currentTab === 'extrato') {
      this.renderExtrato(content);
    } else if (this.currentTab === 'pagar') {
      this.renderContasPagar(content);
    } else if (this.currentTab === 'receber') {
      this.renderContasReceber(content);
    } else if (this.currentTab === 'cartoes') {
      this.renderCartoes(content);
    }
  },

  // ==========================================================================
  // 1. EXTRATO REAL (REGIME DE CAIXA)
  // ==========================================================================
  async renderExtrato(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-extrato-busca" class="form-control" placeholder="BUSCAR POR HISTÓRICO OU ID..." style="flex: 1; min-width: 200px;">
          <div style="width: 220px; min-width: 180px; flex-shrink: 0;" id="wrapper-extrato-conta">
            <select id="filtro-extrato-conta" class="form-control">
              <option value="">TODAS AS CONTAS BANCÁRIAS</option>
            </select>
          </div>
          <select id="filtro-extrato-tipo" class="form-control" style="width: 160px; min-width: 150px; flex-shrink: 0;">
            <option value="">TODOS OS TIPOS</option>
            <option value="ENTRADA">RECEITAS (+)</option>
            <option value="SAIDA">DESPESAS (-)</option>
          </select>
          <span id="total-extrato-badge" class="status-chip secondary mono-text" style="padding: 7px 12px; flex-shrink: 0;">0 LANÇAMENTOS</span>
          <button class="btn btn-primary" id="btn-novo-extrato-avulso" style="white-space: nowrap; flex-shrink: 0;">+ LANÇAMENTO AVULSO</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>DATA PAGTO</th>
              <th>DESCRIÇÃO / HISTÓRICO</th>
              <th>CONTA BANCÁRIA</th>
              <th>MEIO</th>
              <th>TIPO</th>
              <th>VALOR</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-extrato-tbody">
            <tr><td colspan="8" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    // Carrega contas para o filtro com flags multi-seleção
    const contas = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS).catch(() => []);
    const listaContas = contas.results || contas || [];
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
        onChange: () => this.carregarListaExtrato()
      });
    }

    document.getElementById('filtro-extrato-tipo')?.addEventListener('change', () => this.carregarListaExtrato());
    document.getElementById('filtro-extrato-busca')?.addEventListener('input', () => this.carregarListaExtrato());
    document.getElementById('btn-novo-extrato-avulso')?.addEventListener('click', () => this.abrirModalNovoLancamento());

    this.carregarListaExtrato();
  },

  async carregarListaExtrato() {
    const tbody = document.getElementById('lista-extrato-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-extrato-busca')?.value.trim() || '';
    const selConta = document.getElementById('filtro-extrato-conta');
    const contaMulti = selConta?._emcMultiSelect ? selConta._emcMultiSelect.getValues().join(',') : (selConta?.value || '');
    const tipo = document.getElementById('filtro-extrato-tipo')?.value || '';

    try {
      const query = new URLSearchParams({ status_pagamento: 'PAGO' });
      if (busca) query.append('search', busca);
      if (contaMulti) query.append('conta_id', contaMulti);
      if (tipo) query.append('tipo_lancamento', tipo);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?${query.toString()}`);
      const lista = res.results || res || [];

      const badge = document.getElementById('total-extrato-badge');
      if (badge) {
        const count = lista.length;
        badge.textContent = `${count} ${count === 1 ? 'LANÇAMENTO' : 'LANÇAMENTOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhuma movimentação realizada no extrato.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((l) => {
        const isEntrada = l.tipo_lancamento === 'ENTRADA';
        const corValor = isEntrada ? 'var(--color-success)' : 'var(--color-error)';
        const sinal = isEntrada ? '+' : '-';

        html += `
          <tr>
            <td class="mono-text">#${l.id}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataHoraPtBr(l.data_pagamento || l.data_vencimento)}</td>
            <td><strong>${window.EMCUtils.escapeHtml(l.descricao || 'Lançamento')}</strong></td>
            <td>${window.EMCUtils.escapeHtml(l.conta_nome || 'Conta')}</td>
            <td><span class="status-chip info">${window.EMCUtils.escapeHtml(l.meio_pagamento_nome || 'PIX/TED')}</span></td>
            <td><span class="status-chip ${isEntrada ? 'success' : 'danger'}">${l.tipo_lancamento}</span></td>
            <td class="mono-text" style="font-weight: 700; color: ${corValor}; font-size: 15px;">
              ${sinal} ${window.EMCUtils.formatarMoeda(l.valor)}
            </td>
            <td style="text-align: right;">
              <button class="btn btn-danger btn-sm" onclick="window.FinanceiroView.abrirModalEstorno(${l.id})">ESTORNAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
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
    `;

    const selStatusPagar = document.getElementById('filtro-pagar-status');
    if (selStatusPagar) {
      window.EMCUtils.initMultiSelectCombobox(selStatusPagar, {
        placeholder: 'TODOS OS STATUS',
        prefix: 'STATUS',
        onChange: () => this.carregarListaContasPagar()
      });
    }

    document.getElementById('filtro-pagar-busca')?.addEventListener('input', () => this.carregarListaContasPagar());
    document.getElementById('btn-novo-pagar-avulso')?.addEventListener('click', () => this.abrirModalNovoLancamento('SAIDA'));

    this.carregarListaContasPagar();
  },

  async carregarListaContasPagar() {
    const tbody = document.getElementById('lista-pagar-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-pagar-busca')?.value.trim() || '';
    const selStatus = document.getElementById('filtro-pagar-status');
    const statusVal = selStatus?._emcMultiSelect ? selStatus._emcMultiSelect.getValues().join(',') : (selStatus?.value || '');

    try {
      const query = new URLSearchParams({ tipo_lancamento: 'SAIDA' });
      if (busca) query.append('search', busca);
      if (statusVal) query.append('status_pagamento', statusVal);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?${query.toString()}`);
      const lista = res.results || res || [];

      const badge = document.getElementById('total-pagar-badge');
      if (badge) {
        const count = lista.length;
        badge.textContent = `${count} ${count === 1 ? 'TÍTULO' : 'TÍTULOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhuma conta a pagar encontrada.</td></tr>';
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
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
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
    `;

    const selStatusReceber = document.getElementById('filtro-receber-status');
    if (selStatusReceber) {
      window.EMCUtils.initMultiSelectCombobox(selStatusReceber, {
        placeholder: 'TODOS OS STATUS',
        prefix: 'STATUS',
        onChange: () => this.carregarListaContasReceber()
      });
    }

    document.getElementById('filtro-receber-busca')?.addEventListener('input', () => this.carregarListaContasReceber());
    document.getElementById('btn-novo-receber-avulso')?.addEventListener('click', () => this.abrirModalNovoLancamento('ENTRADA'));

    this.carregarListaContasReceber();
  },

  async carregarListaContasReceber() {
    const tbody = document.getElementById('lista-receber-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-receber-busca')?.value.trim() || '';
    const selStatus = document.getElementById('filtro-receber-status');
    const statusVal = selStatus?._emcMultiSelect ? selStatus._emcMultiSelect.getValues().join(',') : (selStatus?.value || '');

    try {
      const query = new URLSearchParams({ tipo_lancamento: 'ENTRADA' });
      if (busca) query.append('search', busca);
      if (statusVal) query.append('status_pagamento', statusVal);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?${query.toString()}`);
      const lista = res.results || res || [];

      const badge = document.getElementById('total-receber-badge');
      if (badge) {
        const count = lista.length;
        badge.textContent = `${count} ${count === 1 ? 'TÍTULO' : 'TÍTULOS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum título a receber encontrado.</td></tr>';
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
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
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

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.TRANSFERIR, {
            conta_origem_id, conta_destino_id, valor
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

  async abrirModalNovoLancamento(defaultTipo = 'SAIDA') {
    const [contas, categorias, meios] = await Promise.all([
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS),
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS),
      window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.MEIOS_PAGAMENTO)
    ]);

    const listaContas = contas.results || contas || [];
    const listaCat = categorias.results || categorias || [];
    const listaMeios = meios.results || meios || [];

    let optionsContas = '<option value="">SELECIONE A CONTA...</option>';
    listaContas.forEach((c) => { optionsContas += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)}</option>`; });

    let optionsCat = '<option value="">SELECIONE A CATEGORIA DRE...</option>';
    listaCat.forEach((cat) => { optionsCat += `<option value="${cat.id}">${window.EMCUtils.escapeHtml(cat.nome)} (${cat.tipo})</option>`; });

    let optionsMeios = '<option value="">SELECIONE O MEIO...</option>';
    listaMeios.forEach((m) => { optionsMeios += `<option value="${m.id}">${window.EMCUtils.escapeHtml(m.nome)}</option>`; });

    window.EMCUtils.openModal({
      title: defaultTipo === 'ENTRADA' ? 'NOVO TÍTULO A RECEBER (AVULSO)' : (defaultTipo === 'SAIDA' ? 'NOVA DESPESA A PAGAR (AVULSA)' : 'NOVO LANÇAMENTO AVULSO'),
      size: 'md',
      confirmText: 'SALVAR LANÇAMENTO',
      content: `
        <form id="form-novo-lanc">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label">Tipo de Movimentação *</label>
              <select id="nl-tipo" class="form-control">
                <option value="SAIDA" ${defaultTipo === 'SAIDA' ? 'selected' : ''}>SAÍDA (DESPESA)</option>
                <option value="ENTRADA" ${defaultTipo === 'ENTRADA' ? 'selected' : ''}>ENTRADA (RECEITA)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Valor (R$) *</label>
              <input type="text" id="nl-valor" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00" required>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">Descrição / Histórico *</label>
            <input type="text" id="nl-desc" class="form-control" placeholder="EX: PAGAMENTO ENERGIA ELÉTRICA OFICINA" required>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label">Categoria Financeira (DRE) *</label>
              <select id="nl-cat" class="form-control" required>${optionsCat}</select>
            </div>
            <div class="form-group">
              <label class="form-label">Data de Vencimento *</label>
              <input type="date" id="nl-venc" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label">Conta Bancária</label>
              <select id="nl-conta" class="form-control">${optionsContas}</select>
            </div>
            <div class="form-group">
              <label class="form-label">Meio de Pagamento</label>
              <select id="nl-meio" class="form-control">${optionsMeios}</select>
            </div>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const tipo_lancamento = document.getElementById('nl-tipo').value;
        const valor = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('nl-valor').value);
        const descricao = document.getElementById('nl-desc').value.trim();
        const categoria_id = document.getElementById('nl-cat').value;
        const data_vencimento = document.getElementById('nl-venc').value;
        const conta_id = document.getElementById('nl-conta').value || null;
        const meio_pagamento_id = document.getElementById('nl-meio').value || null;

        if (!descricao || valor <= 0 || !categoria_id) {
          window.EMCUtils.showToast('Preencha os campos obrigatórios.', 'warning');
          return false;
        }

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS, {
            tipo_lancamento, valor, descricao, categoria_id, data_vencimento, conta_id, meio_pagamento_id
          });
          window.EMCUtils.showToast('Lançamento cadastrado com sucesso!', 'success');
          this.render(document.getElementById('app-root'));
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao criar lançamento.', 'error');
          return false;
        }
      }
    });
  }
};
