/**
 * EMC Soldas - View de Conciliação Bancária Inteligente Split-Screen
 * Upload de OFX/CSV, Seleção de Conta Bancária, Match 1:1, Match Múltiplo e Lançamento Rápido no Ato.
 */

window.ConciliacaoView = {
  transacoesExtrato: [],
  lancamentosErp: [],
  contasBancarias: [],
  contaSelecionadaId: null,
  selectedExtratoIndex: null,
  selectedErpIds: [],
  metaExtrato: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CONCILIAÇÃO BANCÁRIA SPLIT-SCREEN</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CRUZAMENTO INTELIGENTE ENTRE EXTRATO OFX/CSV E LANÇAMENTOS DO ERP</p>
        </div>

        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <input type="file" id="input-upload-extrato" accept=".ofx,.csv,.txt" style="display: none;">
          <button class="btn btn-primary" id="btn-trigger-upload-extrato">+ IMPORTAR EXTRATO (OFX / CSV)</button>
        </div>
      </div>

      <!-- Barra de Ferramentas e Seletor de Conta Bancária -->
      <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); font-weight: 600;">CONTA BANCÁRIA:</span>
              <select id="select-conciliacao-conta" class="form-control" style="min-width: 220px; max-width: 320px;">
                <option value="">CARREGANDO CONTAS...</option>
              </select>
            </div>
            <button class="btn btn-secondary btn-sm" id="btn-auto-match">⚡ AUTO-MATCH 1:1 (±3 DIAS)</button>
            <button class="btn btn-secondary btn-sm" id="btn-lancamento-rapido">+ LANÇAMENTO RÁPIDO NO ATO</button>
          </div>

          <div>
            <button class="btn btn-primary" id="btn-confirmar-conciliacao" disabled>CONFIRMAR CONCILIAÇÃO SELECIONADA</button>
          </div>
        </div>

        <!-- Banner de Metadados do Extrato Importado (se houver) -->
        <div id="banner-meta-extrato" style="display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-outline-variant); font-size: 12px;"></div>
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
              Selecione a <strong>Conta Bancária</strong> acima e clique em <strong>+ IMPORTAR EXTRATO</strong> para carregar o arquivo .OFX ou .CSV.
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
      if (!this.contaSelecionadaId) {
        window.EMCUtils.showToast('Selecione uma conta bancária antes de importar o extrato.', 'warning');
        return;
      }
      document.getElementById('input-upload-extrato')?.click();
    });

    document.getElementById('input-upload-extrato')?.addEventListener('change', (e) => this.handleUploadExtrato(e));
    document.getElementById('select-conciliacao-conta')?.addEventListener('change', (e) => {
      this.contaSelecionadaId = e.target.value ? parseInt(e.target.value, 10) : null;
      this.carregarLancamentosErp();
    });

    document.getElementById('btn-auto-match')?.addEventListener('click', () => this.executarAutoMatch());
    document.getElementById('btn-lancamento-rapido')?.addEventListener('click', () => this.abrirModalLancamentoRapido());
    document.getElementById('btn-confirmar-conciliacao')?.addEventListener('click', () => this.confirmarConciliacao());

    await this.carregarContasBancarias();
    await this.carregarLancamentosErp();
  },

  async carregarContasBancarias() {
    const select = document.getElementById('select-conciliacao-conta');
    if (!select) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS);
      this.contasBancarias = res.results || res || [];

      if (!this.contasBancarias.length) {
        select.innerHTML = '<option value="">NENHUMA CONTA CADASTRADA</option>';
        window.EMCUtils.showToast('Nenhuma conta bancária encontrada. Acesse "Tesouraria & Caixa" > "Contas Bancárias" para cadastrar sua conta.', 'info');
        return;
      }

      let options = '<option value="">SELECIONE A CONTA...</option>';
      this.contasBancarias.forEach(c => {
        options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`;
      });
      select.innerHTML = options;

      // Seleciona automaticamente a primeira conta se não houver selecionada
      if (!this.contaSelecionadaId && this.contasBancarias.length > 0) {
        this.contaSelecionadaId = this.contasBancarias[0].id;
        select.value = String(this.contaSelecionadaId);
      }
    } catch (err) {
      select.innerHTML = '<option value="">ERRO AO CARREGAR CONTAS</option>';
    }
  },

  async carregarLancamentosErp() {
    const body = document.getElementById('coluna-erp-body');
    const contador = document.getElementById('contador-erp');
    if (!body) return;

    try {
      let url = `${window.CONFIG.ENDPOINTS.FINANCEIRO.LANCAMENTOS}?is_conciliado=false`;
      if (this.contaSelecionadaId) {
        url += `&conta_id=${this.contaSelecionadaId}`;
      }

      const res = await window.api.get(url);
      this.lancamentosErp = res.results || res || [];

      if (contador) contador.textContent = `${this.lancamentosErp.length} LANÇAMENTOS`;

      if (!this.lancamentosErp.length) {
        body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">Todos os lançamentos do ERP estão conciliados para esta conta.</p>';
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

    if (!this.lancamentosErp.length) {
      body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">Nenhum lançamento pendente no ERP.</p>';
      return;
    }

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
    if (this.contaSelecionadaId) {
      formData.append('conta_id', this.contaSelecionadaId);
    }

    try {
      window.EMCUtils.showToast('Processando extrato bancário...', 'info');
      const res = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_EXTRATO, formData);
      
      // Captura segura tanto por chave extrato quanto transacoes
      this.transacoesExtrato = res.extrato || res.transacoes || [];
      this.metaExtrato = res.meta || {};

      // Se o backend retornar os lançamentos processados do ERP com matching
      if (res.erp && res.erp.length > 0) {
        this.lancamentosErp = res.erp;
      }

      const contador = document.getElementById('contador-extrato');
      if (contador) contador.textContent = `${this.transacoesExtrato.length} TRANSAÇÕES`;

      this.renderBannerMeta();
      this.renderListaExtrato();
      this.renderListaErp();

      window.EMCUtils.showToast(`Extrato importado com sucesso! ${this.transacoesExtrato.length} transação(ões) carregada(s).`, 'success');
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Falha ao processar arquivo de extrato.', 'error');
    } finally {
      // Limpa input para permitir reupload do mesmo arquivo se necessário
      event.target.value = '';
    }
  },

  renderBannerMeta() {
    const banner = document.getElementById('banner-meta-extrato');
    if (!banner || !this.metaExtrato) return;

    const parts = [];
    if (this.metaExtrato.banco_codigo) parts.push(`<strong>BANCO:</strong> ${window.EMCUtils.escapeHtml(this.metaExtrato.banco_codigo)}`);
    if (this.metaExtrato.agencia) parts.push(`<strong>AG:</strong> ${window.EMCUtils.escapeHtml(this.metaExtrato.agencia)}`);
    if (this.metaExtrato.conta) parts.push(`<strong>CC:</strong> ${window.EMCUtils.escapeHtml(this.metaExtrato.conta)}`);
    if (this.metaExtrato.data_inicio && this.metaExtrato.data_fim) {
      parts.push(`<strong>PERÍODO:</strong> ${window.EMCUtils.formatarDataPtBr(this.metaExtrato.data_inicio)} a ${window.EMCUtils.formatarDataPtBr(this.metaExtrato.data_fim)}`);
    }
    if (this.metaExtrato.saldo_final !== undefined && this.metaExtrato.saldo_final !== null) {
      parts.push(`<strong>SALDO NO EXTRATO:</strong> ${window.EMCUtils.formatarMoeda(this.metaExtrato.saldo_final)}`);
    }

    if (parts.length > 0) {
      banner.innerHTML = `<div class="mono-text" style="color: var(--color-on-surface-variant); display: flex; gap: 16px; flex-wrap: wrap;">${parts.join(' • ')}</div>`;
      banner.style.display = 'block';
    } else {
      banner.style.display = 'none';
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
      const isEntrada = t.tipo === 'ENTRADA' || (parseFloat(t.valor) || 0) > 0;
      const valorAbs = t.valor_absoluto !== undefined ? t.valor_absoluto : Math.abs(parseFloat(t.valor) || 0);

      html += `
        <div class="split-item ${isSelected ? 'selected' : ''}" onclick="window.ConciliacaoView.selectExtratoItem(${idx})">
          <div>
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">
              ${window.EMCUtils.formatarDataPtBr(t.data)} • ID: ${window.EMCUtils.escapeHtml(t.fitid || t.documento || '-')}
            </div>
            <strong>${window.EMCUtils.escapeHtml(t.descricao || t.memo || 'Transação Bancária')}</strong>
          </div>
          <div class="text-right">
            <div class="mono-text" style="font-weight: 700; color: ${isEntrada ? 'var(--color-success)' : 'var(--color-error)'}; font-size: 14px;">
              ${isEntrada ? '+' : '-'} ${window.EMCUtils.formatarMoeda(valorAbs)}
            </div>
            <span class="status-chip ${isEntrada ? 'success' : 'danger'}" style="font-size: 9px; padding: 2px 4px;">
              ${isEntrada ? 'CRÉDITO' : 'DÉBITO'}
            </span>
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

    const podeConfirmar = this.selectedExtratoIndex !== null && this.selectedErpIds.length > 0 && !!this.contaSelecionadaId;
    btn.disabled = !podeConfirmar;
  },

  executarAutoMatch() {
    if (!this.transacoesExtrato.length || !this.lancamentosErp.length) {
      window.EMCUtils.showToast('Importe um extrato bancário para realizar o Auto-Match.', 'warning');
      return;
    }

    let matchesEncontrados = 0;
    this.transacoesExtrato.forEach((t, idx) => {
      const valorAbs = t.valor_absoluto !== undefined ? parseFloat(t.valor_absoluto) : Math.abs(parseFloat(t.valor) || 0);
      const match = this.lancamentosErp.find(l => 
        Math.abs(parseFloat(l.valor) - valorAbs) < 0.01 && 
        !this.selectedErpIds.includes(l.id) &&
        (l.tipo_lancamento === t.tipo || (l.tipo_lancamento === 'ENTRADA' && t.valor > 0))
      );

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

  async abrirModalLancamentoRapido() {
    if (this.selectedExtratoIndex === null) {
      window.EMCUtils.showToast('Selecione primeiro uma linha do extrato bancário para criar o lançamento.', 'warning');
      return;
    }

    if (!this.contaSelecionadaId) {
      window.EMCUtils.showToast('Selecione a conta bancária da conciliação.', 'warning');
      return;
    }

    const t = this.transacoesExtrato[this.selectedExtratoIndex];
    const valorAbs = t.valor_absoluto !== undefined ? parseFloat(t.valor_absoluto) : Math.abs(parseFloat(t.valor) || 0);
    const isEntrada = t.tipo === 'ENTRADA' || (parseFloat(t.valor) || 0) > 0;

    // Busca categorias financeiras para classificação contábil (DRE)
    let categorias = [];
    try {
      const resCat = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS);
      categorias = resCat.results || resCat || [];
    } catch (e) {
      categorias = [];
    }

    let optionsCat = '<option value="">SELECIONE A CATEGORIA CONTÁBIL...</option>';
    categorias.forEach(cat => {
      optionsCat += `<option value="${cat.id}">${window.EMCUtils.escapeHtml(cat.nome)} (${cat.tipo})</option>`;
    });

    window.EMCUtils.openModal({
      title: 'LANÇAMENTO RÁPIDO NO ATO (CONCILIAÇÃO IMEDIATA)',
      size: 'md',
      confirmText: 'CRIAR E CONCILIAR',
      content: `
        <div class="form-group">
          <label class="form-label">Descrição da Movimentação *</label>
          <input type="text" id="lr-desc" class="form-control" value="${window.EMCUtils.escapeHtml(t.descricao || t.memo || 'TARIFA BANCARIA')}" required>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 12px;">
          <div class="form-group">
            <label class="form-label">Valor (R$)</label>
            <input type="text" id="lr-valor" class="form-control mono-text" value="${window.EMCUtils.formatarMoeda(valorAbs)}" readonly>
          </div>
          <div class="form-group">
            <label class="form-label">Natureza</label>
            <input type="text" class="form-control mono-text" value="${isEntrada ? 'ENTRADA (RECEITA)' : 'SAÍDA (DESPESA)'}" readonly>
          </div>
        </div>

        <div class="form-group" style="margin-top: 12px;">
          <label class="form-label">Classificação Contábil (Categoria DRE) *</label>
          <select id="lr-cat" class="form-control" required>
            ${optionsCat}
          </select>
          <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-top: 4px;">Essencial para correta apuração do DRE e relatórios de fluxo de caixa.</span>
        </div>
      `,
      onConfirm: async () => {
        const descricao = document.getElementById('lr-desc')?.value.trim();
        const categoria_id = document.getElementById('lr-cat')?.value;

        if (!descricao || !categoria_id) {
          window.EMCUtils.showToast('Preencha a descrição e selecione a categoria financeira.', 'warning');
          return false;
        }

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.LANCAMENTO_RAPIDO, {
            descricao,
            valor: valorAbs,
            tipo_lancamento: isEntrada ? 'ENTRADA' : 'SAIDA',
            conta_id: this.contaSelecionadaId,
            categoria_id: parseInt(categoria_id, 10),
            data_pagamento: t.data
          });

          window.EMCUtils.showToast('Lançamento criado, liquidado e conciliado no ato com sucesso!', 'success');

          // Remove a transação conciliada da lista
          this.transacoesExtrato.splice(this.selectedExtratoIndex, 1);
          this.selectedExtratoIndex = null;
          this.renderListaExtrato();
          await this.carregarLancamentosErp();
          return true;
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao criar lançamento rápido.', 'error');
          return false;
        }
      }
    });
  },

  async confirmarConciliacao() {
    if (this.selectedExtratoIndex === null || !this.selectedErpIds.length || !this.contaSelecionadaId) {
      window.EMCUtils.showToast('Selecione uma transação do extrato, ao menos um lançamento do ERP e a conta bancária.', 'warning');
      return;
    }

    try {
      await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.CONFIRMAR, {
        lancamento_ids: this.selectedErpIds,
        conta_id: this.contaSelecionadaId
      });

      window.EMCUtils.showToast('Conciliação efetivada e registrada no log perpétuo de auditoria!', 'success');
      
      // Remove do extrato e limpa seleção
      this.transacoesExtrato.splice(this.selectedExtratoIndex, 1);
      this.selectedExtratoIndex = null;
      this.selectedErpIds = [];

      this.renderListaExtrato();
      await this.carregarLancamentosErp();
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao confirmar conciliação.', 'error');
    }
  }
};

