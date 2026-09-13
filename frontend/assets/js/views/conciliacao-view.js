/**
 * EMC Soldas - View de Conciliação Bancária Inteligente Split-Screen com Linhas Bézier
 * Suporte a Modo Dual:
 * 1. MODO CONFERÊNCIA & MATCH (Lançamentos Existentes no ERP)
 * 2. MODO IMPORTAÇÃO & GERAÇÃO EM LOTE (Triagem Direta do Extrato com Linhas de Conexão)
 */

window.ConciliacaoView = {
  modoAtual: 'conferencia', // 'conferencia' | 'importacao'
  transacoesExtrato: [],
  lancamentosErp: [],
  preLancamentosImportacao: [],
  conexoesMatch: [], // [{ extratoIndex, erpId, preIndex, tipo: 'CONFIRMADO'|'SUGESTAO' }]
  contasBancarias: [],
  categoriasFinanceiras: [],
  contaSelecionadaId: null,
  selectedExtratoIndex: null,
  selectedErpIds: [],
  metaExtrato: null,
  resizeObserver: null,

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CONCILIAÇÃO BANCÁRIA SPLIT-SCREEN</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CRUZAMENTO VISUAL ENTRE EXTRATO BANCÁRIO E O ERP COM LINHAS DE MATCH</p>
        </div>

        <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
          <input type="file" id="input-upload-extrato" accept=".ofx,.csv,.txt" style="display: none;">
          <button class="btn btn-primary" id="btn-trigger-upload-extrato">+ IMPORTAR EXTRATO (OFX / CSV)</button>
        </div>
      </div>

      <!-- Barra de Controle: Seletor de Conta e Chave de Modos -->
      <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <!-- Seletor de Conta Bancária -->
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); font-weight: 600;">CONTA:</span>
            <select id="select-conciliacao-conta" class="form-control" style="min-width: 200px; max-width: 280px;">
              <option value="">CARREGANDO CONTAS...</option>
            </select>
          </div>

          <!-- Alternador de Modos -->
          <div style="display: flex; border: 1px solid var(--color-steel-gray); background-color: var(--color-surface);">
            <button class="btn btn-sm ${this.modoAtual === 'conferencia' ? 'btn-primary' : 'btn-secondary'}" id="btn-modo-conferencia" style="border: none;">
              MODO 1: CONFERÊNCIA & MATCH
            </button>
            <button class="btn btn-sm ${this.modoAtual === 'importacao' ? 'btn-primary' : 'btn-secondary'}" id="btn-modo-importacao" style="border: none;">
              MODO 2: IMPORTAÇÃO EM LOTE
            </button>
          </div>

          <!-- Ações Contextuais do Modo Atual -->
          <div id="barra-acoes-contextuais" style="display: flex; gap: 8px; align-items: center;">
            <!-- Preenchido dinamicamente -->
          </div>
        </div>

        <!-- Banner de Metadados do Extrato Importado -->
        <div id="banner-meta-extrato" style="display: none; margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-outline-variant); font-size: 12px;"></div>
      </div>

      <!-- Container Split-Screen com Canvas SVG para as Linhas de Match -->
      <div class="split-screen-wrapper" id="conciliacao-wrapper">
        <svg class="conciliacao-svg-overlay" id="conciliacao-svg-overlay"></svg>

        <div class="split-screen-container with-connectors">
          <!-- Coluna Esquerda: Extrato Bancário Importado -->
          <div class="split-column" id="coluna-extrato-container">
            <div class="split-column-header">
              <h4>EXTRATO BANCÁRIO (OFX / CSV)</h4>
              <span class="mono-text" id="contador-extrato" style="font-size: 12px; color: var(--color-on-surface-variant);">0 TRANSAÇÕES</span>
            </div>
            <div class="split-column-body" id="coluna-extrato-body">
              <p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">
                Nenhum extrato importado no momento.<br>
                Selecione a <strong>Conta Bancária</strong> e clique em <strong>+ IMPORTAR EXTRATO</strong> acima.
              </p>
            </div>
          </div>

          <!-- Coluna Direita: Lançamentos do ERP ou Grade de Pré-Lançamentos -->
          <div class="split-column" id="coluna-erp-container">
            <div class="split-column-header">
              <h4 id="coluna-erp-titulo">LANÇAMENTOS NO ERP</h4>
              <span class="mono-text" id="contador-erp" style="font-size: 12px; color: var(--color-on-surface-variant);">0 ITENS</span>
            </div>
            <div class="split-column-body" id="coluna-erp-body">
              <div class="text-center" style="padding: 40px 0;"><div class="loader-spinner"></div></div>
            </div>
          </div>
        </div>
      </div>
    `;

    this.bindEventosGerais();
    await this.carregarCategoriasFinanceiras();
    await this.carregarContasBancarias();
    await this.atualizarInterfacePorModo();
    this.iniciarMonitorConexoes();
  },

  bindEventosGerais() {
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
      this.atualizarInterfacePorModo();
    });

    document.getElementById('btn-modo-conferencia')?.addEventListener('click', () => {
      this.modoAtual = 'conferencia';
      this.render(document.getElementById('app-root'));
    });

    document.getElementById('btn-modo-importacao')?.addEventListener('click', () => {
      this.modoAtual = 'importacao';
      this.render(document.getElementById('app-root'));
    });
  },

  async carregarCategoriasFinanceiras() {
    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CATEGORIAS);
      this.categoriasFinanceiras = res.results || res || [];
    } catch (e) {
      this.categoriasFinanceiras = [];
    }
  },

  async carregarContasBancarias() {
    const select = document.getElementById('select-conciliacao-conta');
    if (!select) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.CONTAS_BANCARIAS);
      this.contasBancarias = res.results || res || [];

      if (!this.contasBancarias.length) {
        select.innerHTML = '<option value="">NENHUMA CONTA CADASTRADA</option>';
        window.EMCUtils.showToast('Nenhuma conta bancária encontrada. Acesse "Tesouraria & Caixa" > "Contas Bancárias" para cadastrar.', 'info');
        return;
      }

      let options = '<option value="">SELECIONE A CONTA...</option>';
      this.contasBancarias.forEach(c => {
        options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome)} (Saldo: ${window.EMCUtils.formatarMoeda(c.saldo)})</option>`;
      });
      select.innerHTML = options;

      if (!this.contaSelecionadaId && this.contasBancarias.length > 0) {
        this.contaSelecionadaId = this.contasBancarias[0].id;
        select.value = String(this.contaSelecionadaId);
      } else if (this.contaSelecionadaId) {
        select.value = String(this.contaSelecionadaId);
      }
    } catch (err) {
      select.innerHTML = '<option value="">ERRO AO CARREGAR CONTAS</option>';
    }
  },

  async atualizarInterfacePorModo() {
    const barraAcoes = document.getElementById('barra-acoes-contextuais');
    const tituloErp = document.getElementById('coluna-erp-titulo');
    if (!barraAcoes) return;

    if (this.modoAtual === 'conferencia') {
      if (tituloErp) tituloErp.textContent = 'LANÇAMENTOS NO ERP (EXISTENTES)';
      barraAcoes.innerHTML = `
        <button class="btn btn-secondary btn-sm" id="btn-auto-match">⚡ AUTO-MATCH (±3 DIAS)</button>
        <button class="btn btn-secondary btn-sm" id="btn-lancamento-rapido">+ LANÇAMENTO RÁPIDO</button>
        <button class="btn btn-primary btn-sm" id="btn-confirmar-conciliacao" disabled>CONFIRMAR CONCILIAÇÃO</button>
      `;

      document.getElementById('btn-auto-match')?.addEventListener('click', () => this.executarAutoMatch());
      document.getElementById('btn-lancamento-rapido')?.addEventListener('click', () => this.abrirModalLancamentoRapido());
      document.getElementById('btn-confirmar-conciliacao')?.addEventListener('click', () => this.confirmarConciliacao());

      await this.carregarLancamentosErp();
    } else {
      if (tituloErp) tituloErp.textContent = 'MESA DE TRIAGEM & PRÉ-LANÇAMENTOS';
      barraAcoes.innerHTML = `
        <button class="btn btn-primary btn-sm" id="btn-gerar-lote" disabled>
          ⚡ GERAR E CONCILIAR EM LOTE (0)
        </button>
      `;

      document.getElementById('btn-gerar-lote')?.addEventListener('click', () => this.executarImportacaoLote());

      this.prepararPreLancamentosImportacao();
    }

    this.renderListaExtrato();
    setTimeout(() => this.desenharLinhasConexao(), 150);
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
        body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">Nenhum lançamento pendente no ERP para esta conta.</p>';
        return;
      }

      this.renderListaErpConferencia();
    } catch (err) {
      body.innerHTML = `<p style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</p>`;
    }
  },

  prepararPreLancamentosImportacao() {
    // Para cada transação do extrato que ainda não é conciliada, cria um pré-lançamento
    this.preLancamentosImportacao = this.transacoesExtrato.map((t, idx) => {
      const isEntrada = t.tipo === 'ENTRADA' || (parseFloat(t.valor) || 0) > 0;
      const catsFiltradas = this.categoriasFinanceiras.filter(c => c.tipo === (isEntrada ? 'RECEITA' : 'DESPESA'));
      const catPadrao = catsFiltradas.length > 0 ? catsFiltradas[0].id : (this.categoriasFinanceiras[0]?.id || 1);

      return {
        id_temp: idx,
        fitid: t.fitid || '',
        data: t.data,
        valor: t.valor_absoluto !== undefined ? parseFloat(t.valor_absoluto) : Math.abs(parseFloat(t.valor) || 0),
        tipo_lancamento: isEntrada ? 'ENTRADA' : 'SAIDA',
        descricao: t.descricao || t.memo || 'MOVIMENTAÇÃO BANCÁRIA',
        documento: t.documento || '',
        categoria_id: catPadrao,
        descartado: false
      };
    });

    // No modo importação, traçamos as conexões 1:1 entre cada item do extrato e sua proposta
    this.conexoesMatch = this.preLancamentosImportacao.map((p, idx) => ({
      extratoIndex: idx,
      preIndex: idx,
      tipo: 'CONFIRMADO'
    }));

    this.renderListaPreLancamentos();
    this.atualizarBotaoGerarLote();
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
      window.EMCUtils.showToast('Processando extrato bancário com motor universal...', 'info');
      const res = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.UPLOAD_EXTRATO, formData);
      
      this.transacoesExtrato = res.extrato || res.transacoes || [];
      this.metaExtrato = res.meta || {};

      if (res.erp && res.erp.length > 0 && this.modoAtual === 'conferencia') {
        this.lancamentosErp = res.erp;
      }

      const contador = document.getElementById('contador-extrato');
      if (contador) contador.textContent = `${this.transacoesExtrato.length} TRANSAÇÕES`;

      this.renderBannerMeta();
      await this.atualizarInterfacePorModo();

      window.EMCUtils.showToast(`Extrato importado com sucesso! ${this.transacoesExtrato.length} transações prontas.`, 'success');
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Falha ao processar arquivo de extrato.', 'error');
    } finally {
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

      // Verifica se possui conexão de match
      const conexao = this.conexoesMatch.find(c => c.extratoIndex === idx);
      const isMatched = !!conexao;
      const isConfirmado = conexao && conexao.tipo === 'CONFIRMADO';

      html += `
        <div class="split-item ${isSelected ? 'selected' : ''} ${isMatched ? 'matched' : ''}" 
             data-extrato-index="${idx}" 
             onclick="window.ConciliacaoView.selectExtratoItem(${idx})"
             onmouseenter="window.ConciliacaoView.destacarConexao(${idx})"
             onmouseleave="window.ConciliacaoView.limparDestaqueConexao()">
          
          <div class="anchor-node right ${isMatched ? (isConfirmado ? 'matched' : 'suggested') : ''}"></div>

          <div style="flex: 1; padding-right: 12px;">
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">
              ${window.EMCUtils.formatarDataPtBr(t.data)} • ID: ${window.EMCUtils.escapeHtml(t.fitid || t.documento || '-')}
            </div>
            <strong>${window.EMCUtils.escapeHtml(t.descricao || t.memo || 'Transação')}</strong>
          </div>

          <div class="text-right">
            <div class="mono-text" style="font-weight: 700; color: ${isEntrada ? 'var(--color-success)' : 'var(--color-error)'}; font-size: 14px;">
              ${isEntrada ? '+' : '-'} ${window.EMCUtils.formatarMoeda(valorAbs)}
            </div>
            <div style="display: flex; gap: 4px; justify-content: flex-end; margin-top: 4px;">
              <span class="status-chip ${isEntrada ? 'success' : 'danger'}" style="font-size: 9px; padding: 2px 4px;">
                ${isEntrada ? 'CRÉDITO' : 'DÉBITO'}
              </span>
              ${isMatched ? `
                <span class="status-chip ${isConfirmado ? 'success' : 'warning'}" style="font-size: 9px; padding: 2px 4px;">
                  ${isConfirmado ? 'MATCH 100%' : 'SUGESTÃO'}
                </span>
              ` : `
                <span class="status-chip secondary" style="font-size: 9px; padding: 2px 4px;">PENDENTE</span>
              `}
            </div>
          </div>
        </div>
      `;
    });

    body.innerHTML = html;
    this.atualizarBotaoConfirmar();
  },

  renderListaErpConferencia() {
    const body = document.getElementById('coluna-erp-body');
    if (!body) return;

    if (!this.lancamentosErp.length) {
      body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">Nenhum lançamento no ERP.</p>';
      return;
    }

    let html = '';
    this.lancamentosErp.forEach((l) => {
      const isSelected = this.selectedErpIds.includes(l.id);
      const isEntrada = l.tipo_lancamento === 'ENTRADA';

      // Conexão associada
      const conexao = this.conexoesMatch.find(c => c.erpId === l.id);
      const isMatched = !!conexao;
      const isConfirmado = conexao && conexao.tipo === 'CONFIRMADO';

      html += `
        <div class="split-item ${isSelected ? 'selected' : ''} ${isMatched ? 'matched' : ''}" 
             data-erp-id="${l.id}" 
             onclick="window.ConciliacaoView.toggleSelectErp(${l.id})">
          
          <div class="anchor-node left ${isMatched ? (isConfirmado ? 'matched' : 'suggested') : ''}"></div>

          <div style="flex: 1; padding-left: 12px; padding-right: 12px;">
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">
              #${l.id} • ${window.EMCUtils.formatarDataPtBr(l.data_vencimento || l.data_pagamento)} • ${l.categoria?.nome || 'CATEGORIA GERAL'}
            </div>
            <strong>${window.EMCUtils.escapeHtml(l.descricao || 'Lançamento ERP')}</strong>
          </div>

          <div class="text-right">
            <div class="mono-text" style="font-weight: 700; color: ${isEntrada ? 'var(--color-success)' : 'var(--color-error)'}; font-size: 14px;">
              ${isEntrada ? '+' : '-'} ${window.EMCUtils.formatarMoeda(l.valor)}
            </div>
            <div style="display: flex; gap: 4px; justify-content: flex-end; margin-top: 4px;">
              <span class="status-chip ${isEntrada ? 'success' : 'danger'}" style="font-size: 9px; padding: 2px 4px;">
                ${l.tipo_lancamento}
              </span>
              ${isMatched && !isConfirmado ? `
                <button class="btn btn-warning btn-sm" style="font-size: 9px; padding: 2px 6px;" onclick="event.stopPropagation(); window.ConciliacaoView.aceitarSugestaoMatch(${l.id})">
                  ACEITAR MATCH
                </button>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    });

    body.innerHTML = html;
    this.atualizarBotaoConfirmar();
  },

  renderListaPreLancamentos() {
    const body = document.getElementById('coluna-erp-body');
    const contador = document.getElementById('contador-erp');
    if (!body) return;

    const ativos = this.preLancamentosImportacao.filter(p => !p.descartado);
    if (contador) contador.textContent = `${ativos.length} A IMPORTAR`;

    if (!this.preLancamentosImportacao.length) {
      body.innerHTML = '<p class="mono-text text-center" style="padding: 40px 16px; color: var(--color-on-surface-variant);">Importe um extrato bancário para gerar a mesa de triagem.</p>';
      return;
    }

    let html = '';
    this.preLancamentosImportacao.forEach((p, idx) => {
      const isEntrada = p.tipo_lancamento === 'ENTRADA';
      const isDescartado = p.descartado;

      // Monta opções de categorias
      let optionsCat = '';
      this.categoriasFinanceiras.forEach(cat => {
        optionsCat += `<option value="${cat.id}" ${cat.id === p.categoria_id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(cat.nome)}</option>`;
      });

      html += `
        <div class="pre-lancamento-card ${isDescartado ? 'discarded' : ''}" data-pre-index="${idx}">
          <div class="anchor-node left ${!isDescartado ? 'matched' : ''}"></div>

          <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">
              PRÉ-LANÇAMENTO #${idx + 1} • ${window.EMCUtils.formatarDataPtBr(p.data)}
            </div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="mono-text font-bold" style="color: ${isEntrada ? 'var(--color-success)' : 'var(--color-error)'}; font-size: 13px;">
                ${isEntrada ? '+' : '-'} ${window.EMCUtils.formatarMoeda(p.valor)}
              </span>
              ${!isDescartado ? `
                <button class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 11px;" title="Descartar este lançamento" onclick="window.ConciliacaoView.descartarPreLancamento(${idx})">
                  ✕
                </button>
              ` : `
                <button class="btn btn-secondary btn-sm" style="padding: 2px 6px; font-size: 11px;" title="Restaurar este lançamento" onclick="window.ConciliacaoView.restaurarPreLancamento(${idx})">
                  ↩
                </button>
              `}
            </div>
          </div>

          <!-- Campos inline de Edição do Pré-Lançamento -->
          <div style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 8px;">
            <div>
              <input type="text" class="form-control" style="font-size: 12px; padding: 4px 8px;" 
                     value="${window.EMCUtils.escapeHtml(p.descricao)}" 
                     onchange="window.ConciliacaoView.atualizarDescricaoPreLancamento(${idx}, this.value)">
            </div>
            <div>
              <select class="form-control" style="font-size: 12px; padding: 4px 8px;"
                      onchange="window.ConciliacaoView.atualizarCategoriaPreLancamento(${idx}, this.value)">
                ${optionsCat}
              </select>
            </div>
          </div>
        </div>
      `;
    });

    body.innerHTML = html;
  },

  descartarPreLancamento(idx) {
    if (this.preLancamentosImportacao[idx]) {
      this.preLancamentosImportacao[idx].descartado = true;
      // Remove conexão SVG
      this.conexoesMatch = this.conexoesMatch.filter(c => c.preIndex !== idx);
      this.renderListaExtrato();
      this.renderListaPreLancamentos();
      this.atualizarBotaoGerarLote();
      this.desenharLinhasConexao();
    }
  },

  restaurarPreLancamento(idx) {
    if (this.preLancamentosImportacao[idx]) {
      this.preLancamentosImportacao[idx].descartado = false;
      this.conexoesMatch.push({
        extratoIndex: idx,
        preIndex: idx,
        tipo: 'CONFIRMADO'
      });
      this.renderListaExtrato();
      this.renderListaPreLancamentos();
      this.atualizarBotaoGerarLote();
      this.desenharLinhasConexao();
    }
  },

  atualizarDescricaoPreLancamento(idx, valor) {
    if (this.preLancamentosImportacao[idx]) {
      this.preLancamentosImportacao[idx].descricao = valor.trim();
    }
  },

  atualizarCategoriaPreLancamento(idx, catId) {
    if (this.preLancamentosImportacao[idx]) {
      this.preLancamentosImportacao[idx].categoria_id = parseInt(catId, 10);
    }
  },

  atualizarBotaoGerarLote() {
    const btn = document.getElementById('btn-gerar-lote');
    if (!btn) return;

    const ativos = this.preLancamentosImportacao.filter(p => !p.descartado);
    btn.disabled = ativos.length === 0 || !this.contaSelecionadaId;
    btn.textContent = `⚡ GERAR E CONCILIAR EM LOTE (${ativos.length})`;
  },

  async executarImportacaoLote() {
    const ativos = this.preLancamentosImportacao.filter(p => !p.descartado);
    if (!ativos.length || !this.contaSelecionadaId) return;

    window.EMCUtils.openModal({
      title: 'CONFIRMAÇÃO DE IMPORTAÇÃO EM LOTE',
      size: 'sm',
      confirmText: 'GERAR E CONCILIAR AGORA',
      content: `
        <p>Confirmar a criação de <strong>${ativos.length} lançamentos financeiros</strong> no ERP?</p>
        <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-top: 8px;">
          Todos os lançamentos serão criados, liquidados como PAGO e já carimbados como CONCILIADOS na conta bancária selecionada, atualizando o saldo real.
        </p>
      `,
      onConfirm: async () => {
        try {
          const payload = {
            conta_id: this.contaSelecionadaId,
            lancamentos: ativos.map(p => ({
              descricao: p.descricao,
              valor: p.valor,
              tipo_lancamento: p.tipo_lancamento,
              categoria_id: p.categoria_id,
              data_pagamento: p.data,
              documento: p.documento,
              fitid: p.fitid
            }))
          };

          const res = await window.api.post(window.CONFIG.ENDPOINTS.CONCILIACAO.IMPORTACAO_LOTE, payload);
          window.EMCUtils.showToast(res.mensagem || 'Lançamentos gerados e conciliados em lote com sucesso!', 'success');

          // Limpa a mesa de triagem e atualiza contas
          this.transacoesExtrato = [];
          this.preLancamentosImportacao = [];
          this.conexoesMatch = [];
          this.renderListaExtrato();
          this.renderListaPreLancamentos();
          this.desenharLinhasConexao();
          await this.carregarContasBancarias();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Falha ao processar importação em lote.', 'error');
          return false;
        }
      }
    });
  },

  // ==========================================================================
  // MOTOR VISUAL DE LINHAS CONECTIVAS SVG (BÉZIER)
  // ==========================================================================
  iniciarMonitorConexoes() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }

    const wrapper = document.getElementById('conciliacao-wrapper');
    if (wrapper) {
      this.resizeObserver = new ResizeObserver(() => this.desenharLinhasConexao());
      this.resizeObserver.observe(wrapper);
    }

    window.addEventListener('resize', () => this.desenharLinhasConexao());

    const bodyExtrato = document.getElementById('coluna-extrato-body');
    const bodyErp = document.getElementById('coluna-erp-body');

    bodyExtrato?.addEventListener('scroll', () => this.desenharLinhasConexao());
    bodyErp?.addEventListener('scroll', () => this.desenharLinhasConexao());
  },

  desenharLinhasConexao() {
    const svg = document.getElementById('conciliacao-svg-overlay');
    const wrapper = document.getElementById('conciliacao-wrapper');
    if (!svg || !wrapper) return;

    // Em telas pequenas (mobile/tablet empilhado), oculta as linhas para não poluir
    if (window.innerWidth <= 900) {
      svg.innerHTML = '';
      return;
    }

    const wrapperRect = wrapper.getBoundingClientRect();
    svg.setAttribute('width', wrapperRect.width);
    svg.setAttribute('height', wrapperRect.height);

    let pathsHtml = '';

    this.conexoesMatch.forEach((conexao, cIdx) => {
      const elExtrato = wrapper.querySelector(`[data-extrato-index="${conexao.extratoIndex}"] .anchor-node.right`);
      let elDireito = null;

      if (this.modoAtual === 'conferencia') {
        elDireito = wrapper.querySelector(`[data-erp-id="${conexao.erpId}"] .anchor-node.left`);
      } else {
        elDireito = wrapper.querySelector(`[data-pre-index="${conexao.preIndex}"] .anchor-node.left`);
      }

      if (!elExtrato || !elDireito) return;

      const r1 = elExtrato.getBoundingClientRect();
      const r2 = elDireito.getBoundingClientRect();

      // Checa se os cards estão visíveis dentro da área de rolagem
      const container1 = elExtrato.closest('.split-column-body');
      const container2 = elDireito.closest('.split-column-body');
      if (container1 && container2) {
        const c1Rect = container1.getBoundingClientRect();
        const c2Rect = container2.getBoundingClientRect();
        if (r1.bottom < c1Rect.top || r1.top > c1Rect.bottom || r2.bottom < c2Rect.top || r2.top > c2Rect.bottom) {
          return;
        }
      }

      const x1 = r1.left + r1.width / 2 - wrapperRect.left;
      const y1 = r1.top + r1.height / 2 - wrapperRect.top;
      const x2 = r2.left + r2.width / 2 - wrapperRect.left;
      const y2 = r2.top + r2.height / 2 - wrapperRect.top;

      // Curva Bézier cúbica fluida
      const dx = Math.max(36, (x2 - x1) * 0.45);
      const isConfirmado = conexao.tipo === 'CONFIRMADO';
      const classe = isConfirmado ? 'svg-path-match' : 'svg-path-suggestion';

      pathsHtml += `
        <path d="M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}" 
              class="${classe}" 
              data-conexao-index="${cIdx}"
              data-extrato-index="${conexao.extratoIndex}" />
      `;
    });

    svg.innerHTML = pathsHtml;
  },

  destacarConexao(extratoIndex) {
    const svg = document.getElementById('conciliacao-svg-overlay');
    const wrapper = document.getElementById('conciliacao-wrapper');
    if (!svg || !wrapper) return;

    const path = svg.querySelector(`path[data-extrato-index="${extratoIndex}"]`);
    if (path) path.classList.add('highlight');

    const cardExtrato = wrapper.querySelector(`[data-extrato-index="${extratoIndex}"]`);
    if (cardExtrato) cardExtrato.classList.add('highlight-match');

    const conexao = this.conexoesMatch.find(c => c.extratoIndex === extratoIndex);
    if (conexao) {
      const cardErp = conexao.erpId 
        ? wrapper.querySelector(`[data-erp-id="${conexao.erpId}"]`)
        : wrapper.querySelector(`[data-pre-index="${conexao.preIndex}"]`);
      if (cardErp) cardErp.classList.add('highlight-match');
    }
  },

  limparDestaqueConexao() {
    const svg = document.getElementById('conciliacao-svg-overlay');
    const wrapper = document.getElementById('conciliacao-wrapper');
    if (!svg || !wrapper) return;

    svg.querySelectorAll('path.highlight').forEach(p => p.classList.remove('highlight'));
    wrapper.querySelectorAll('.highlight-match').forEach(c => c.classList.remove('highlight-match'));
  },

  // ==========================================================================
  // AÇÕES DO MODO CONFERÊNCIA & MATCH
  // ==========================================================================
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
    this.renderListaErpConferencia();
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
    this.conexoesMatch = [];

    this.transacoesExtrato.forEach((t, idx) => {
      const valorAbs = t.valor_absoluto !== undefined ? parseFloat(t.valor_absoluto) : Math.abs(parseFloat(t.valor) || 0);
      const match = this.lancamentosErp.find(l => 
        Math.abs(parseFloat(l.valor) - valorAbs) < 0.01 && 
        !this.conexoesMatch.some(c => c.erpId === l.id) &&
        (l.tipo_lancamento === t.tipo || (l.tipo_lancamento === 'ENTRADA' && t.valor > 0))
      );

      if (match) {
        matchesEncontrados++;
        this.conexoesMatch.push({
          extratoIndex: idx,
          erpId: match.id,
          tipo: 'CONFIRMADO'
        });
      }
    });

    this.renderListaExtrato();
    this.renderListaErpConferencia();
    this.desenharLinhasConexao();

    if (matchesEncontrados > 0) {
      window.EMCUtils.showToast(`Auto-Match conectou ${matchesEncontrados} correspondência(s) com sucesso!`, 'success');
    } else {
      window.EMCUtils.showToast('Nenhum match automático 1:1 com valor idêntico encontrado.', 'info');
    }
  },

  aceitarSugestaoMatch(erpId) {
    const conexao = this.conexoesMatch.find(c => c.erpId === erpId);
    if (conexao) {
      conexao.tipo = 'CONFIRMADO';
      this.renderListaExtrato();
      this.renderListaErpConferencia();
      this.desenharLinhasConexao();
      window.EMCUtils.showToast('Sugestão aceita! Par vinculado como confirmado.', 'success');
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

    let optionsCat = '<option value="">SELECIONE A CATEGORIA CONTÁBIL...</option>';
    this.categoriasFinanceiras.forEach(cat => {
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
          this.transacoesExtrato.splice(this.selectedExtratoIndex, 1);
          this.selectedExtratoIndex = null;
          this.renderListaExtrato();
          await this.carregarLancamentosErp();
          this.desenharLinhasConexao();
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
      
      this.transacoesExtrato.splice(this.selectedExtratoIndex, 1);
      this.selectedExtratoIndex = null;
      this.selectedErpIds = [];

      this.renderListaExtrato();
      await this.carregarLancamentosErp();
      this.desenharLinhasConexao();
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao confirmar conciliação.', 'error');
    }
  }
};

