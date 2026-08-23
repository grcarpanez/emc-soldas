/**
 * EMC Soldas - View de Conciliação Bancária Inteligente Split-Screen
 * Upload de OFX/CSV, Match 1:1, Match Múltiplo e Lançamento Rápido no Ato.
 */

window.ConciliacaoView = {
  transacoesExtrato: [],
  lancamentosErp: [],
  selectedExtratoIndex: null,
  selectedErpIds: [],

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CONCILIAÇÃO BANCÁRIA SPLIT-SCREEN</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CRUZAMENTO INTELIGENTE ENTRE EXTRATO OFX/CSV E LANÇAMENTOS DO ERP</p>
        </div>

        <div style="display: flex; gap: 8px;">
          <input type="file" id="input-upload-extrato" accept=".ofx,.csv" style="display: none;">
          <button class="btn btn-primary" id="btn-trigger-upload-extrato">+ IMPORTAR EXTRATO (OFX / CSV)</button>
        </div>
      </div>

      <!-- Barra de Ferramentas de Matching -->
      <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div style="display: flex; gap: 12px; align-items: center;">
            <button class="btn btn-secondary btn-sm" id="btn-auto-match">⚡ AUTO-MATCH 1:1 (±3 DIAS)</button>
            <button class="btn btn-secondary btn-sm" id="btn-lancamento-rapido">+ LANÇAMENTO RÁPIDO NO ATO</button>
          </div>

          <div>
            <button class="btn btn-primary" id="btn-confirmar-conciliacao" disabled>CONFIRMAR CONCILIAÇÃO SELECIONADA</button>
          </div>
        </div>
      </div>

      <!-- Layout Split-Screen de 2 Colunas -->
      <div class="split-screen-container">
        <!-- Coluna Esquerda: Extrato Bancário Importado -->
        <div class="split-column">
          <div class="split-column-header">
            <h4>EXTRATO BANCÁRIO (OFX / CSV)</h4>
            <span class="mono-text" id="contador-extrato" style="font-size: 12px; color: var(--color-on-surface-variant);">0 TRANSAÇÕES</span>
          </div>
          <div class="split-column-body" id="coluna-extrato-body">
            <p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">
              Nenhum extrato importado no momento.<br>
              Clique em <strong>+ IMPORTAR EXTRATO</strong> acima para carregar o arquivo .OFX ou .CSV do banco.
            </p>
          </div>
        </div>

        <!-- Coluna Direita: Lançamentos do ERP -->
        <div class="split-column">
          <div class="split-column-header">
            <h4>LANÇAMENTOS NO ERP (NÃO CONCILIADOS)</h4>
            <span class="mono-text" id="contador-erp" style="font-size: 12px; color: var(--color-on-surface-variant);">CARREGANDO...</span>
          </div>
          <div class="split-column-body" id="coluna-erp-body">
            <div class="text-center" style="padding: 40px 0;"><div class="loader-spinner"></div></div>
          </div>
        </div>
      </div>
    `;

    document.getElementById('btn-trigger-upload-extrato')?.addEventListener('click', () => {
      document.getElementById('input-upload-extrato')?.click();
    });

    document.getElementById('input-upload-extrato')?.addEventListener('change', (e) => this.handleUploadExtrato(e));
    document.getElementById('btn-auto-match')?.addEventListener('click', () => this.executarAutoMatch());
    document.getElementById('btn-lancamento-rapido')?.addEventListener('click', () => this.abrirModalLancamentoRapido());
    document.getElementById('btn-confirmar-conciliacao')?.addEventListener('click', () => this.confirmarConciliacao());

    this.carregarLancamentosErp();
  },

  async carregarLancamentosErp() {
    const body = document.getElementById('coluna-erp-body');
    const contador = document.getElementById('contador-erp');
    if (!body) return;

    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?is_conciliado=false`);
      this.lancamentosErp = res.results || res || [];

      if (contador) contador.textContent = `${this.lancamentosErp.length} LANÇAMENTOS`;

      if (!this.lancamentosErp.length) {
        body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">Todos os lançamentos do ERP estão conciliados.</p>';
        return;
      }

      this.renderListaErp();
    } catch (err) {
      body.innerHTML = `<p style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</p>`;
    }
  },

  renderListaErp() {
    const body = document.getElementById('coluna-erp-body');
    if (!body) return;

    let html = '';
    this.lancamentosErp.forEach((l) => {
      const isSelected = this.selectedErpIds.includes(l.id);
      const isEntrada = l.tipo_lancamento === 'ENTRADA';

      html += `
        <div class="split-item ${isSelected ? 'selected' : ''}" onclick="window.ConciliacaoView.toggleSelectErp(${l.id})">
          <div>
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">#${l.id} • ${window.EMCUtils.formatarDataPtBr(l.data_vencimento || l.data_pagamento)}</div>
            <strong>${window.EMCUtils.escapeHtml(l.descricao)}</strong>
          </div>
          <div class="text-right">
            <div class="mono-text" style="font-weight: 700; color: ${isEntrada ? 'var(--color-success)' : 'var(--color-error)'}; font-size: 14px;">
              ${isEntrada ? '+' : '-'} ${window.EMCUtils.formatarMoeda(l.valor)}
            </div>
            <span class="status-chip ${isEntrada ? 'success' : 'danger'}" style="font-size: 9px; padding: 2px 4px;">${l.tipo_lancamento}</span>
          </div>
        </div>
      `;
    });

    body.innerHTML = html;
    this.atualizarBotaoConfirmar();
  },

  async handleUploadExtrato(event) {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('arquivo', file);

    try {
      window.EMCUtils.showToast('Processando extrato bancário...', 'info');
      const res = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_EXTRATO, formData);
      this.transacoesExtrato = res.transacoes || [];

      const contador = document.getElementById('contador-extrato');
      if (contador) contador.textContent = `${this.transacoesExtrato.length} TRANSAÇÕES`;

      this.renderListaExtrato();
      window.EMCUtils.showToast('Extrato importado com sucesso! Use o Auto-Match ou selecione manualmente.', 'success');
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Falha ao processar arquivo de extrato.', 'error');
    }
  },

  renderListaExtrato() {
    const body = document.getElementById('coluna-extrato-body');
    if (!body) return;

    if (!this.transacoesExtrato.length) {
      body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px;">Nenhuma transação encontrada no arquivo.</p>';
      return;
    }

    let html = '';
    this.transacoesExtrato.forEach((t, idx) => {
      const isSelected = this.selectedExtratoIndex === idx;
      const isEntrada = (parseFloat(t.valor) || 0) > 0;

      html += `
        <div class="split-item ${isSelected ? 'selected' : ''}" onclick="window.ConciliacaoView.selectExtratoItem(${idx})">
          <div>
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">${window.EMCUtils.formatarDataPtBr(t.data)} • DOC: ${t.documento || '-'}</div>
            <strong>${window.EMCUtils.escapeHtml(t.memo || t.descricao || 'Transação')}</strong>
          </div>
          <div class="text-right">
            <div class="mono-text" style="font-weight: 700; color: ${isEntrada ? 'var(--color-success)' : 'var(--color-error)'}; font-size: 14px;">
              ${window.EMCUtils.formatarMoeda(Math.abs(t.valor))}
            </div>
            <span class="status-chip ${isEntrada ? 'success' : 'danger'}" style="font-size: 9px; padding: 2px 4px;">${isEntrada ? 'CRÉDITO' : 'DÉBITO'}</span>
          </div>
        </div>
      `;
    });

    body.innerHTML = html;
    this.atualizarBotaoConfirmar();
  },

  selectExtratoItem(index) {
    this.selectedExtratoIndex = this.selectedExtratoIndex === index ? null : index;
    this.renderListaExtrato();
  },

  toggleSelectErp(lancamentoId) {
    if (this.selectedErpIds.includes(lancamentoId)) {
      this.selectedErpIds = this.selectedErpIds.filter(id => id !== lancamentoId);
    } else {
      this.selectedErpIds.push(lancamentoId);
    }
    this.renderListaErp();
  },

  atualizarBotaoConfirmar() {
    const btn = document.getElementById('btn-confirmar-conciliacao');
    if (!btn) return;

    const podeConfirmar = this.selectedExtratoIndex !== null && this.selectedErpIds.length > 0;
    btn.disabled = !podeConfirmar;
  },

  executarAutoMatch() {
    if (!this.transacoesExtrato.length || !this.lancamentosErp.length) {
      window.EMCUtils.showToast('Importe um extrato bancário para realizar o Auto-Match.', 'warning');
      return;
    }

    let matchesEncontrados = 0;
    this.transacoesExtrato.forEach((t, idx) => {
      const valorAbs = Math.abs(parseFloat(t.valor) || 0);
      const match = this.lancamentosErp.find(l => Math.abs(parseFloat(l.valor) - valorAbs) < 0.01 && !this.selectedErpIds.includes(l.id));

      if (match) {
        matchesEncontrados++;
        this.selectedExtratoIndex = idx;
        if (!this.selectedErpIds.includes(match.id)) {
          this.selectedErpIds.push(match.id);
        }
      }
    });

    this.renderListaExtrato();
    this.renderListaErp();

    if (matchesEncontrados > 0) {
      window.EMCUtils.showToast(`Auto-Match localizou ${matchesEncontrados} correspondência(s) provável(is)!`, 'success');
    } else {
      window.EMCUtils.showToast('Nenhum match automático 1:1 com valor idêntico encontrado.', 'info');
    }
  },

  abrirModalLancamentoRapido() {
    if (this.selectedExtratoIndex === null) {
      window.EMCUtils.showToast('Selecione primeiro uma linha do extrato bancário para criar o lançamento.', 'warning');
      return;
    }

    const t = this.transacoesExtrato[this.selectedExtratoIndex];
    const valorAbs = Math.abs(parseFloat(t.valor) || 0);
    const isEntrada = (parseFloat(t.valor) || 0) > 0;

    window.EMCUtils.openModal({
      title: 'LANÇAMENTO RÁPIDO NO ATO (CONCILIAÇÃO IMEDIATA)',
      size: 'sm',
      confirmText: 'CRIAR E CONCILIAR',
      content: `
        <div class="form-group">
          <label class="form-label">Descrição da Tarifa / Rendimento *</label>
          <input type="text" id="lr-desc" class="form-control" value="${window.EMCUtils.escapeHtml(t.memo || t.descricao || 'TARIFA BANCARIA')}" required>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
          <div class="form-group">
            <label class="form-label">Valor (R$)</label>
            <input type="text" id="lr-valor" class="form-control mono-text" value="${window.EMCUtils.formatarMoeda(valorAbs)}" readonly>
          </div>
          <div class="form-group">
            <label class="form-label">Tipo</label>
            <input type="text" class="form-control mono-text" value="${isEntrada ? 'RECEITA' : 'DESPESA'}" readonly>
          </div>
        </div>
      `,
      onConfirm: async () => {
        const descricao = document.getElementById('lr-desc').value.trim();
        if (!descricao) return false;

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.LANCAMENTO_RAPIDO, {
            descricao,
            valor: valorAbs,
            tipo_lancamento: isEntrada ? 'ENTRADA' : 'SAIDA',
            data_pagamento: t.data
          });

          window.EMCUtils.showToast('Lançamento criado e conciliado no ato com sucesso!', 'success');
          // Remove a transação conciliada
          this.transacoesExtrato.splice(this.selectedExtratoIndex, 1);
          this.selectedExtratoIndex = null;
          this.renderListaExtrato();
          this.carregarLancamentosErp();
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao criar lançamento rápido.', 'error');
          return false;
        }
      }
    });
  },

  async confirmarConciliacao() {
    if (this.selectedExtratoIndex === null || !this.selectedErpIds.length) return;

    try {
      await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.CONFIRMAR, {
        lancamentos_ids: this.selectedErpIds
      });

      window.EMCUtils.showToast('Conciliação efetivada e registrada no log de auditoria!', 'success');
      
      // Remove do extrato e limpa seleção
      this.transacoesExtrato.splice(this.selectedExtratoIndex, 1);
      this.selectedExtratoIndex = null;
      this.selectedErpIds = [];

      this.renderListaExtrato();
      this.carregarLancamentosErp();
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao confirmar conciliação.', 'error');
    }
  }
};
