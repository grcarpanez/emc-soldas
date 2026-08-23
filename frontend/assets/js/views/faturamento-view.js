/**
 * EMC Soldas - View de Faturamento Agregado & Conta Corrente de Clientes
 * Pré-Faturas (Rascunho), Fatura Final, Parcelamento a Receber, Baixas e Cortesias.
 */

window.FaturamentoView = {
  currentTab: 'faturas',

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">FATURAMENTO AGREGADO & CONTA CORRENTE</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CONSOLIDAÇÃO DE ORÇAMENTOS, PRÉ-FATURAS, REGRAS DE PAGAMENTO E BAIXAS</p>
        </div>
      </div>

      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'faturas' ? 'active' : ''}" id="tab-btn-fat-faturas">
          FATURAS EMITIDAS
        </button>
        <button class="tab-btn ${this.currentTab === 'conta-corrente' ? 'active' : ''}" id="tab-btn-fat-cc">
          CONTA CORRENTE (ORÇAMENTOS A FATURAR)
        </button>
      </div>

      <div id="faturamento-tab-content"></div>
    `;

    document.getElementById('tab-btn-fat-faturas')?.addEventListener('click', () => {
      this.currentTab = 'faturas';
      this.render(container);
    });
    document.getElementById('tab-btn-fat-cc')?.addEventListener('click', () => {
      this.currentTab = 'conta-corrente';
      this.render(container);
    });

    const content = document.getElementById('faturamento-tab-content');
    if (this.currentTab === 'faturas') {
      this.renderFaturas(content);
    } else {
      this.renderContaCorrente(content);
    }
  },

  // ==========================================================================
  // 1. LISTA DE FATURAS
  // ==========================================================================
  async renderFaturas(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <input type="text" id="filtro-fat-busca" class="form-control" placeholder="BUSCAR POR CLIENTE, NÚMERO OU ID..." style="max-width: 380px;">
          <select id="filtro-fat-status" class="form-control" style="width: 180px;">
            <option value="">TODOS OS STATUS</option>
            <option value="RASCUNHO">RASCUNHO (PRÉ-FATURA)</option>
            <option value="FATURADA">FATURADA</option>
            <option value="PAGA">PAGA (QUITADA)</option>
            <option value="CANCELADA">CANCELADA</option>
          </select>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>CLIENTE</th>
              <th>DATA EMISSÃO</th>
              <th>STATUS</th>
              <th>VALOR TOTAL</th>
              <th>REGRA DE PAGAMENTO</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-fat-tbody">
            <tr><td colspan="7" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('filtro-fat-busca')?.addEventListener('input', () => this.carregarListaFaturas());
    document.getElementById('filtro-fat-status')?.addEventListener('change', () => this.carregarListaFaturas());

    this.carregarListaFaturas();
  },

  async carregarListaFaturas() {
    const tbody = document.getElementById('lista-fat-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-fat-busca')?.value.trim() || '';
    const status = document.getElementById('filtro-fat-status')?.value || '';

    try {
      const query = new URLSearchParams();
      if (busca) query.append('search', busca);
      if (status) query.append('status', status);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAS}?${query.toString()}`);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhuma fatura encontrada.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((f) => {
        const badgeStatus = {
          RASCUNHO: 'warning',
          FATURADA: 'info',
          PAGA: 'success',
          CANCELADA: 'danger'
        }[f.status] || 'info';

        html += `
          <tr>
            <td class="mono-text"><strong>#${f.id}</strong></td>
            <td><strong>${window.EMCUtils.escapeHtml(f.cliente_nome || 'Cliente')}</strong></td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(f.data_emissao)}</td>
            <td><span class="status-chip ${badgeStatus}">${f.status}</span></td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700; font-size: 15px;">
              ${window.EMCUtils.formatarMoeda(f.valor_total_faturado || f.valor_bruto)}
            </td>
            <td>${window.EMCUtils.escapeHtml(f.regra_pagamento_nome || 'A Definir')}</td>
            <td style="text-align: right; white-space: nowrap;">
              <button class="btn btn-primary btn-sm" onclick="window.FaturamentoView.baixarPdfFatura(${f.id})">PDF</button>
              <button class="btn btn-secondary btn-sm" onclick="window.FaturamentoView.verDetalhesFatura(${f.id})">DETALHES</button>
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
  // 2. CONTA CORRENTE (ORÇAMENTOS A FATURAR)
  // ==========================================================================
  async renderContaCorrente(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant); margin-bottom: 12px;">
          SELECIONE O CLIENTE PARA AGRUPAR ORÇAMENTOS CONCLUÍDOS E GERAR PRÉ-FATURA:
        </p>
        <div style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
          <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 280px;">
            <label class="form-label" for="cc-filtro-cliente">Cliente</label>
            <select id="cc-filtro-cliente" class="form-control">
              <option value="">CARREGANDO CLIENTES...</option>
            </select>
          </div>
          <button class="btn btn-primary" id="btn-gerar-pre-fatura" style="height: 42px;">+ CONSOLIDAR EM PRÉ-FATURA</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th style="width: 40px;"><input type="checkbox" id="check-todos-orc"></th>
              <th>ORÇAMENTO</th>
              <th>EQUIPAMENTO</th>
              <th>DATA CONCLUSÃO</th>
              <th>STATUS OPERACIONAL</th>
              <th>VALOR BRUTO</th>
            </tr>
          </thead>
          <tbody id="cc-orcamentos-tbody">
            <tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Selecione um cliente acima para visualizar a conta corrente.</td></tr>
          </tbody>
        </table>
      </div>
    `;

    // Carrega clientes com orçamentos a faturar
    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES);
      const clientes = res.results || res || [];

      let options = '<option value="">SELECIONE UM CLIENTE...</option>';
      clientes.forEach((c) => {
        options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome_razao)}</option>`;
      });

      const selectCli = document.getElementById('cc-filtro-cliente');
      if (selectCli) selectCli.innerHTML = options;

      selectCli?.addEventListener('change', () => this.carregarOrcamentosCliente(selectCli.value));
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar clientes.', 'error');
    }

    document.getElementById('btn-gerar-pre-fatura')?.addEventListener('click', () => this.gerarPreFatura());
  },

  async carregarOrcamentosCliente(clienteId) {
    const tbody = document.getElementById('cc-orcamentos-tbody');
    if (!tbody) return;

    if (!clienteId) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Selecione um cliente acima.</td></tr>';
      return;
    }

    try {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>';
      const endpoint = `${window.CONFIG.ENDPOINTS.FATURAMENTO.CONTA_CORRENTE}?cliente_id=${clienteId}`;
      const res = await window.api.get(endpoint);
      const orcamentos = res.orcamentos || res || [];

      if (!orcamentos.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum orçamento concluído pendente de faturamento para este cliente.</td></tr>';
        return;
      }

      let html = '';
      orcamentos.forEach((orc) => {
        html += `
          <tr>
            <td><input type="checkbox" class="check-orc-item" value="${orc.id}" data-valor="${orc.valor_bruto || orc.valor_total}"></td>
            <td class="mono-text"><strong>#${orc.id}</strong></td>
            <td>${window.EMCUtils.escapeHtml(orc.equipamento_descricao || 'Oficina Geral')}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(orc.data_geracao)}</td>
            <td><span class="status-chip success">${orc.status_operacional}</span></td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${window.EMCUtils.formatarMoeda(orc.valor_bruto || orc.valor_total)}</td>
          </tr>
        `;
      });

      tbody.innerHTML = html;

      // Listener para marcar todos
      document.getElementById('check-todos-orc')?.addEventListener('change', (e) => {
        document.querySelectorAll('.check-orc-item').forEach((chk) => { chk.checked = e.target.checked; });
      });
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async gerarPreFatura() {
    const clienteId = document.getElementById('cc-filtro-cliente')?.value;
    const selecionados = Array.from(document.querySelectorAll('.check-orc-item:checked')).map(chk => parseInt(chk.value, 10));

    if (!clienteId || !selecionados.length) {
      window.EMCUtils.showToast('Selecione um cliente e ao menos um orçamento para consolidar.', 'warning');
      return;
    }

    try {
      const payload = {
        cliente_id: clienteId,
        orcamentos_ids: selecionados
      };

      const res = await window.api.post(window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAS, payload);
      window.EMCUtils.showToast(`Pré-Fatura #${res.id} gerada em rascunho com sucesso!`, 'success');
      this.currentTab = 'faturas';
      this.render(document.getElementById('app-root'));
      this.verDetalhesFatura(res.id);
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao gerar pré-fatura.', 'error');
    }
  },

  async verDetalhesFatura(faturaId) {
    try {
      const [fatura, regras] = await Promise.all([
        window.api.get(`${window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAS}${faturaId}/`),
        window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.REGRAS_PAGAMENTO)
      ]);

      const listaRegras = regras.results || regras || [];
      let optionsRegras = '<option value="">SELECIONE A FORMA DE PAGAMENTO...</option>';
      listaRegras.forEach((r) => {
        optionsRegras += `<option value="${r.id}" ${fatura.regra_pagamento_id === r.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(r.nome)}</option>`;
      });

      const orcamentos = fatura.orcamentos || [];
      let rowsOrc = '';
      orcamentos.forEach((o) => {
        rowsOrc += `
          <tr>
            <td class="mono-text"><strong>#${o.id}</strong></td>
            <td>${window.EMCUtils.escapeHtml(o.equipamento_descricao || '-')}</td>
            <td><span class="status-chip success">${o.status_operacional}</span></td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(o.valor_total || o.valor_bruto)}</td>
          </tr>
        `;
      });

      const parcelas = fatura.parcelas || fatura.lancamentos || [];
      let rowsParc = '';
      parcelas.forEach((p) => {
        const badge = p.status_pagamento === 'PAGO' ? 'success' : (p.status_pagamento === 'VENCIDO' ? 'danger' : 'warning');
        rowsParc += `
          <tr>
            <td class="mono-text">#${p.id}</td>
            <td>${window.EMCUtils.escapeHtml(p.descricao || 'Parcela')}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(p.data_vencimento)}</td>
            <td class="mono-text"><strong>${window.EMCUtils.formatarMoeda(p.valor)}</strong></td>
            <td><span class="status-chip ${badge}">${p.status_pagamento}</span></td>
          </tr>
        `;
      });

      window.EMCUtils.openModal({
        title: `FATURA #${fatura.id} - ${fatura.cliente_nome} [${fatura.status}]`,
        size: 'lg',
        hideFooter: true,
        content: `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; font-size: 13px;">
            <div>
              • <strong>Cliente:</strong> ${window.EMCUtils.escapeHtml(fatura.cliente_nome)}<br>
              • <strong>Data de Emissão:</strong> ${window.EMCUtils.formatarDataPtBr(fatura.data_emissao)}<br>
              • <strong>Status da Fatura:</strong> <span class="status-chip ${fatura.status === 'PAGA' ? 'success' : 'info'}">${fatura.status}</span>
            </div>
            <div>
              • <strong>Valor Bruto:</strong> ${window.EMCUtils.formatarMoeda(fatura.valor_bruto)}<br>
              • <strong>Desconto Comercial:</strong> ${window.EMCUtils.formatarMoeda(fatura.desconto_global || 0)}<br>
              • <strong>Valor Total Faturado:</strong> <span class="mono-text" style="font-size: 16px; font-weight: 700; color: var(--color-rust-orange);">${window.EMCUtils.formatarMoeda(fatura.valor_total_faturado || fatura.valor_bruto)}</span>
            </div>
          </div>

          <h4 style="margin-bottom: 8px;">ORÇAMENTOS CONSOLIDADOS</h4>
          <div class="table-container mb-16">
            <table class="table">
              <thead><tr><th>ORÇAMENTO</th><th>EQUIPAMENTO</th><th>STATUS</th><th>VALOR</th></tr></thead>
              <tbody>${rowsOrc}</tbody>
            </table>
          </div>

          ${fatura.status === 'RASCUNHO' ? `
            <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
              <h4 style="margin-bottom: 12px;">FECHAMENTO DE FATURA FINAL (GERAR CONTAS A RECEBER)</h4>
              <div style="display: grid; grid-template-columns: 2fr 1fr auto; gap: 12px; align-items: flex-end;">
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Regra de Pagamento Acordada *</label>
                  <select id="fechar-fat-regra" class="form-control">${optionsRegras}</select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Desconto Final (R$)</label>
                  <input type="text" id="fechar-fat-desconto" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
                </div>
                <button class="btn btn-primary" id="btn-confirmar-faturamento" style="height: 42px;">FATURAR DEFINITIVO</button>
              </div>
            </div>
          ` : ''}

          ${parcelas.length ? `
            <h4 style="margin-bottom: 8px;">PARCELAS NO CONTAS A RECEBER</h4>
            <div class="table-container mb-16">
              <table class="table">
                <thead><tr><th>ID</th><th>DESCRIÇÃO</th><th>VENCIMENTO</th><th>VALOR</th><th>STATUS</th></tr></thead>
                <tbody>${rowsParc}</tbody>
              </table>
            </div>
          ` : ''}

          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; gap: 8px;">
              <button class="btn btn-primary" onclick="window.FaturamentoView.baixarPdfFatura(${fatura.id})">BAIXAR PDF</button>
              ${fatura.status === 'FATURADA' ? `
                <button class="btn btn-secondary" onclick="window.FaturamentoView.abrirModalRecebimento(${fatura.id})">REGISTRAR RECEBIMENTO</button>
                <button class="btn btn-ghost" onclick="window.FaturamentoView.quitarCortesia(${fatura.id})">CORTESIA (100%)</button>
              ` : ''}
            </div>

            ${fatura.status !== 'CANCELADA' && fatura.status !== 'PAGA' ? `
              <button class="btn btn-danger" onclick="window.FaturamentoView.abrirModalCancelarFatura(${fatura.id})">CANCELAR FATURA</button>
            ` : ''}
          </div>
        `
      });

      document.getElementById('btn-confirmar-faturamento')?.addEventListener('click', async () => {
        const regra_pagamento_id = document.getElementById('fechar-fat-regra').value;
        const desconto_global = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('fechar-fat-desconto').value);

        if (!regra_pagamento_id) {
          window.EMCUtils.showToast('Selecione uma regra de pagamento para faturar.', 'warning');
          return;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAR.replace('{id}', faturaId);
          await window.api.post(endpoint, { regra_pagamento_id, desconto_global });
          window.EMCUtils.showToast('Fatura finalizada e parcelas geradas no Contas a Receber com sucesso!', 'success');
          this.carregarListaFaturas();
          this.verDetalhesFatura(faturaId);
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao faturar.', 'error');
        }
      });
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar detalhes da fatura.', 'error');
    }
  },

  async abrirModalRecebimento(faturaId) {
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
      optionsMeios += `<option value="${m.id}" data-maquininha="${m.permite_taxa_maquininha}">${window.EMCUtils.escapeHtml(m.nome)}</option>`;
    });

    window.EMCUtils.openModal({
      title: `BAIXA / RECEBIMENTO DA FATURA #${faturaId}`,
      size: 'md',
      confirmText: 'CONFIRMAR BAIXA (ENTRADA EM CAIXA)',
      content: `
        <form id="form-baixa-fatura">
          <div class="form-group">
            <label class="form-label" for="baixa-conta">Conta Bancária de Destino *</label>
            <select id="baixa-conta" class="form-control" required>${optionsContas}</select>
          </div>

          <div class="form-group">
            <label class="form-label" for="baixa-meio">Meio de Pagamento *</label>
            <select id="baixa-meio" class="form-control" required>${optionsMeios}</select>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="baixa-valor-bruto">Valor Bruto Recebido *</label>
              <input type="text" id="baixa-valor-bruto" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="baixa-data">Data do Recebimento *</label>
              <input type="date" id="baixa-data" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
            </div>
          </div>

          <!-- Bloco Dinâmico para Maquininha de Cartão -->
          <div id="bloco-taxa-maquininha" class="card mb-16" style="display: none; background-color: var(--color-surface-container-high);">
            <h4 style="margin-bottom: 8px;">DEDUÇÃO DE TAXA DE MAQUININHA</h4>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="baixa-taxa">Taxa da Maquininha (R$)</label>
              <input type="text" id="baixa-taxa" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
            </div>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const conta_id = document.getElementById('baixa-conta').value;
        const meio_pagamento_id = document.getElementById('baixa-meio').value;
        const valor_bruto = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('baixa-valor-bruto').value);
        const data_pagamento = document.getElementById('baixa-data').value;
        const taxa_maquininha = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('baixa-taxa')?.value || '0');

        if (!conta_id || !meio_pagamento_id || valor_bruto <= 0) {
          window.EMCUtils.showToast('Informe a conta, o meio de pagamento e o valor bruto.', 'warning');
          return false;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FATURAMENTO.RECEBER.replace('{id}', faturaId);
          await window.api.post(endpoint, {
            conta_id,
            meio_pagamento_id,
            valor: valor_bruto,
            data_pagamento,
            taxa_maquininha
          });

          window.EMCUtils.showToast('Recebimento liquidado no Caixa Real com sucesso!', 'success');
          this.carregarListaFaturas();
          this.verDetalhesFatura(faturaId);
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao registrar baixa.', 'error');
          return false;
        }
      }
    });

    document.getElementById('baixa-meio')?.addEventListener('change', (e) => {
      const opt = e.target.selectedOptions[0];
      const isMaquininha = opt?.dataset.maquininha === 'true';
      const bloco = document.getElementById('bloco-taxa-maquininha');
      if (bloco) bloco.style.display = isMaquininha ? 'block' : 'none';
    });
  },

  async quitarCortesia(faturaId) {
    window.EMCUtils.openModal({
      title: `QUITAR FATURA #${faturaId} EM CORTESIA (100% DESCONTO)`,
      size: 'sm',
      confirmText: 'CONFIRMAR CORTESIA',
      content: `
        <p style="color: var(--color-on-surface-variant); font-size: 13px;">
          Esta operação quitará a fatura comercialmente com 100% de desconto, registrando no histórico de cortesias do cliente sem gerar receita no Caixa Real.
        </p>
      `,
      onConfirm: async () => {
        try {
          const endpoint = window.CONFIG.ENDPOINTS.FATURAMENTO.CORTESIA.replace('{id}', faturaId);
          await window.api.post(endpoint, {});
          window.EMCUtils.showToast('Fatura quitada em Cortesia com sucesso!', 'success');
          this.carregarListaFaturas();
          this.verDetalhesFatura(faturaId);
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao aplicar cortesia.', 'error');
          return false;
        }
      }
    });
  },

  abrirModalCancelarFatura(faturaId) {
    window.EMCUtils.openModal({
      title: `CANCELAR FATURA #${faturaId}`,
      size: 'sm',
      confirmText: 'CONFIRMAR CANCELAMENTO',
      content: `
        <p style="color: var(--color-on-surface-variant); font-size: 13px; margin-bottom: 12px;">
          Ao cancelar a fatura, os orçamentos vinculados retornarão para 'A FATURAR' e os títulos gerados no Contas a Receber serão anulados.
        </p>
        <div class="form-group">
          <label class="form-label" for="cancelar-fat-motivo">Motivo do Cancelamento *</label>
          <textarea id="cancelar-fat-motivo" class="form-control" rows="3" placeholder="EX: CANCELAMENTO SOLICITADO PELO FINANCEIRO DO CLIENTE" required autofocus></textarea>
        </div>
      `,
      onConfirm: async () => {
        const motivo_cancelamento = document.getElementById('cancelar-fat-motivo').value.trim();
        if (!motivo_cancelamento || motivo_cancelamento.length < 10) {
          window.EMCUtils.showToast('A justificativa deve conter no mínimo 10 caracteres.', 'warning');
          return false;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FATURAMENTO.CANCELAR.replace('{id}', faturaId);
          await window.api.post(endpoint, { motivo_cancelamento });
          window.EMCUtils.showToast(`Fatura #${faturaId} cancelada e orçamentos liberados.`, 'info');
          this.carregarListaFaturas();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao cancelar fatura.', 'error');
          return false;
        }
      }
    });
  },

  async baixarPdfFatura(faturaId) {
    try {
      window.EMCUtils.showToast('Gerando espelho da fatura em PDF...', 'info');
      const endpoint = window.CONFIG.ENDPOINTS.FATURAMENTO.GERAR_PDF.replace('{id}', faturaId);
      await window.api.downloadFile(endpoint, `Fatura_${faturaId}.pdf`);
      window.EMCUtils.showToast('PDF da fatura baixado com sucesso!', 'success');
    } catch (e) {
      window.EMCUtils.showToast(e.message || 'Erro ao gerar PDF da fatura.', 'error');
    }
  }
};
