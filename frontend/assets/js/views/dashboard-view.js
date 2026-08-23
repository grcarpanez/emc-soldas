/**
 * EMC Soldas - View do Dashboard Operacional
 * 5 Flip Cards 3D interativos, gráficos de evolução e feed de atividades.
 */

window.DashboardView = {
  currentPeriodo: 'mes',

  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700; letter-spacing: -0.01em;">DASHBOARD OPERACIONAL & FINANCEIRO</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">VISÃO INTEGRADA EM TEMPO REAL DA OFICINA</p>
        </div>

        <div style="display: flex; gap: 4px; background-color: var(--color-surface-container-low); padding: 4px; border: 1px solid var(--color-steel-gray);">
          <button class="btn btn-ghost btn-sm ${this.currentPeriodo === 'hoje' ? 'btn-primary' : ''}" id="btn-periodo-hoje" style="padding: 6px 12px;">HOJE</button>
          <button class="btn btn-ghost btn-sm ${this.currentPeriodo === 'mes' ? 'btn-primary' : ''}" id="btn-periodo-mes" style="padding: 6px 12px;">MÊS ATUAL</button>
          <button class="btn btn-ghost btn-sm ${this.currentPeriodo === 'ano' ? 'btn-primary' : ''}" id="btn-periodo-ano" style="padding: 6px 12px;">ANO</button>
        </div>
      </div>

      <!-- Container dos 5 Flip Cards -->
      <div id="flip-cards-container" class="flip-card-grid">
        <div style="grid-column: 1 / -1; padding: 40px; text-align: center;">
          <div class="loader-spinner"></div>
          <p class="mono-text mt-16" style="color: var(--color-on-surface-variant);">CARREGANDO MÉTRICAS OPERACIONAIS...</p>
        </div>
      </div>

      <!-- Seção Inferior: Gráfico Comparativo e Feed de Atividades -->
      <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;" id="dashboard-lower-grid">
        <!-- Gráfico / Comparativo Mensal -->
        <div class="card">
          <div class="card-header">
            <h3>RECEITAS X DESPESAS (ÚLTIMOS 6 MESES)</h3>
            <span class="status-chip info">REGIME DE CAIXA</span>
          </div>
          <div id="dashboard-chart-container" style="min-height: 240px; display: flex; align-items: center; justify-content: center;">
            <div class="loader-spinner"></div>
          </div>
        </div>

        <!-- Feed de Atividades Recentes -->
        <div class="card">
          <div class="card-header">
            <h3>ATIVIDADES RECENTES</h3>
            <span class="status-chip warning">LOG EM TEMPO REAL</span>
          </div>
          <div id="dashboard-feed-container" style="max-height: 320px; overflow-y: auto;">
            <div class="loader-spinner"></div>
          </div>
        </div>
      </div>
    `;

    // Listeners dos botões de período
    document.getElementById('btn-periodo-hoje')?.addEventListener('click', () => {
      this.currentPeriodo = 'hoje';
      this.render(container);
    });
    document.getElementById('btn-periodo-mes')?.addEventListener('click', () => {
      this.currentPeriodo = 'mes';
      this.render(container);
    });
    document.getElementById('btn-periodo-ano')?.addEventListener('click', () => {
      this.currentPeriodo = 'ano';
      this.render(container);
    });

    await this.carregarDados();
  },

  async carregarDados() {
    await Promise.all([
      this.carregarFlipCards(),
      this.carregarGrafico(),
      this.carregarFeed()
    ]);
  },

  async carregarFlipCards() {
    const container = document.getElementById('flip-cards-container');
    if (!container) return;

    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.RELATORIOS.DASHBOARD_FLIP_CARDS}?periodo=${this.currentPeriodo}`);
      const cards = res.cards || {};

      const op = cards.operacao || {};
      const fat = cards.faturamento || {};
      const rec = cards.receita || {};
      const cxa = cards.caixa || {};
      const alt = cards.alertas || {};

      container.innerHTML = `
        <!-- Card 1: Operação -->
        <div class="flip-card-wrapper" id="card-operacao">
          <div class="flip-card-inner">
            <div class="flip-card-front">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-operacao')">
                <div class="flip-card-title">
                  <span>OPERAÇÃO DE OFICINA</span>
                  <span class="mono-text" style="color: var(--color-rust-orange); font-size: 10px;">GIRE ↻</span>
                </div>
                <div class="flip-card-value">${op.total_orcamentos || 0}</div>
                <div class="flip-card-sub">Orçamentos gerados no período</div>
              </div>
              <div class="flip-card-footer">
                <span class="mono-text" style="font-size: 11px; color: var(--color-success);">${op.aprovados || 0} Aprovados</span>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/orcamentos'">Ver detalhes ➔</button>
              </div>
            </div>
            <div class="flip-card-back">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-operacao')">
                <div class="flip-card-title">DETALHAMENTO OPERACIONAL</div>
                <div style="font-size: 13px; line-height: 1.8;">
                  • <strong>Aprovados:</strong> ${op.aprovados || 0}<br>
                  • <strong>Em Execução:</strong> ${op.em_execucao || 0}<br>
                  • <strong>Concluídos:</strong> ${op.concluidos || 0}<br>
                  • <strong>Cancelados:</strong> ${op.cancelados || 0}
                </div>
              </div>
              <div class="flip-card-footer">
                <button class="btn btn-ghost btn-sm" onclick="window.DashboardView.toggleFlip('card-operacao')">Voltar</button>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/orcamentos'">Orçamentos ➔</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 2: Faturamento -->
        <div class="flip-card-wrapper" id="card-faturamento">
          <div class="flip-card-inner">
            <div class="flip-card-front">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-faturamento')">
                <div class="flip-card-title">
                  <span>FATURAMENTO</span>
                  <span class="mono-text" style="color: var(--color-rust-orange); font-size: 10px;">GIRE ↻</span>
                </div>
                <div class="flip-card-value">${fat.total_faturas || 0}</div>
                <div class="flip-card-sub">Faturas emitidas / consolidadas</div>
              </div>
              <div class="flip-card-footer">
                <span class="mono-text" style="font-size: 11px; color: #8ac8f0;">${fat.faturadas || 0} Faturadas</span>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/faturamento'">Ver detalhes ➔</button>
              </div>
            </div>
            <div class="flip-card-back">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-faturamento')">
                <div class="flip-card-title">STATUS DE FATURAS</div>
                <div style="font-size: 13px; line-height: 1.8;">
                  • <strong>Pré-Faturas (Rascunho):</strong> ${fat.rascunhos || 0}<br>
                  • <strong>Faturadas em Aberto:</strong> ${fat.faturadas || 0}<br>
                  • <strong>Quitadas 100%:</strong> ${fat.pagas || 0}<br>
                  • <strong>Canceladas:</strong> ${fat.canceladas || 0}
                </div>
              </div>
              <div class="flip-card-footer">
                <button class="btn btn-ghost btn-sm" onclick="window.DashboardView.toggleFlip('card-faturamento')">Voltar</button>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/faturamento'">Faturas ➔</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 3: Receita -->
        <div class="flip-card-wrapper" id="card-receita">
          <div class="flip-card-inner">
            <div class="flip-card-front">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-receita')">
                <div class="flip-card-title">
                  <span>RECEITA TOTAL</span>
                  <span class="mono-text" style="color: var(--color-rust-orange); font-size: 10px;">GIRE ↻</span>
                </div>
                <div class="flip-card-value">${window.EMCUtils.formatarMoeda(rec.faturamento_real || 0)}</div>
                <div class="flip-card-sub">Efetivamente liquidado no caixa</div>
              </div>
              <div class="flip-card-footer">
                <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">Projetado: ${window.EMCUtils.formatarMoeda(rec.faturamento_projetado || 0)}</span>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/tesouraria'">Ver detalhes ➔</button>
              </div>
            </div>
            <div class="flip-card-back">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-receita')">
                <div class="flip-card-title">COMPETÊNCIA X CAIXA</div>
                <div style="font-size: 13px; line-height: 1.8;">
                  • <strong>Caixa Real (Recebido):</strong> ${window.EMCUtils.formatarMoeda(rec.faturamento_real || 0)}<br>
                  • <strong>A Receber (Previsão):</strong> ${window.EMCUtils.formatarMoeda(rec.a_receber_pendente || 0)}<br>
                  • <strong>Total Faturado:</strong> ${window.EMCUtils.formatarMoeda(rec.faturamento_projetado || 0)}
                </div>
              </div>
              <div class="flip-card-footer">
                <button class="btn btn-ghost btn-sm" onclick="window.DashboardView.toggleFlip('card-receita')">Voltar</button>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/relatorios'">Relatórios ➔</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 4: Caixa -->
        <div class="flip-card-wrapper" id="card-caixa">
          <div class="flip-card-inner">
            <div class="flip-card-front">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-caixa')">
                <div class="flip-card-title">
                  <span>SALDO EM CONTAS</span>
                  <span class="mono-text" style="color: var(--color-rust-orange); font-size: 10px;">GIRE ↻</span>
                </div>
                <div class="flip-card-value">${window.EMCUtils.formatarMoeda(cxa.saldo_bancario_real || 0)}</div>
                <div class="flip-card-sub">Disponível em bancos e caixa físico</div>
              </div>
              <div class="flip-card-footer">
                <span class="mono-text" style="font-size: 11px; color: var(--color-warning);">Projetado: ${window.EMCUtils.formatarMoeda(cxa.saldo_projetado || 0)}</span>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/tesouraria'">Ver contas ➔</button>
              </div>
            </div>
            <div class="flip-card-back">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-caixa')">
                <div class="flip-card-title">GAVETAS BANCÁRIAS</div>
                <div style="font-size: 13px; line-height: 1.8;">
                  • <strong>Saldo Real:</strong> ${window.EMCUtils.formatarMoeda(cxa.saldo_bancario_real || 0)}<br>
                  • <strong>Contas a Pagar:</strong> -${window.EMCUtils.formatarMoeda(cxa.contas_a_pagar_pendente || 0)}<br>
                  • <strong>Contas a Receber:</strong> +${window.EMCUtils.formatarMoeda(cxa.contas_a_receber_pendente || 0)}
                </div>
              </div>
              <div class="flip-card-footer">
                <button class="btn btn-ghost btn-sm" onclick="window.DashboardView.toggleFlip('card-caixa')">Voltar</button>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/tesouraria'">Tesouraria ➔</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Card 5: Alertas -->
        <div class="flip-card-wrapper" id="card-alertas">
          <div class="flip-card-inner">
            <div class="flip-card-front" style="border-top-color: ${alt.vencidas > 0 ? 'var(--color-error)' : 'var(--color-success)'};">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-alertas')">
                <div class="flip-card-title">
                  <span>ALERTAS & PENDÊNCIAS</span>
                  <span class="mono-text" style="color: var(--color-rust-orange); font-size: 10px;">GIRE ↻</span>
                </div>
                <div class="flip-card-value" style="color: ${alt.vencidas > 0 ? 'var(--color-error)' : 'var(--color-success)'};">
                  ${alt.vencidas || 0}
                </div>
                <div class="flip-card-sub">Contas/Faturas em atraso</div>
              </div>
              <div class="flip-card-footer">
                <span class="mono-text" style="font-size: 11px; color: var(--color-warning);">${alt.vencendo_hoje || 0} Vencendo hoje</span>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/relatorios'">Auditar ➔</button>
              </div>
            </div>
            <div class="flip-card-back">
              <div class="flip-card-body" onclick="window.DashboardView.toggleFlip('card-alertas')">
                <div class="flip-card-title">CRONOGRAMA DE VENCIMENTOS</div>
                <div style="font-size: 13px; line-height: 1.8;">
                  • <strong>Vencidas em atraso:</strong> ${alt.vencidas || 0}<br>
                  • <strong>Vencem Hoje:</strong> ${alt.vencendo_hoje || 0}<br>
                  • <strong>Próximos 7 Dias:</strong> ${alt.proximos_7_dias || 0}
                </div>
              </div>
              <div class="flip-card-footer">
                <button class="btn btn-ghost btn-sm" onclick="window.DashboardView.toggleFlip('card-alertas')">Voltar</button>
                <button class="flip-card-btn-detail" onclick="window.location.hash='#/relatorios'">Inadimplência ➔</button>
              </div>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `
        <div class="alert-banner alert-danger" style="grid-column: 1 / -1;">
          Falha ao carregar Flip Cards: ${window.EMCUtils.escapeHtml(err.message)}
        </div>
      `;
    }
  },

  toggleFlip(cardId) {
    const card = document.getElementById(cardId);
    if (card) {
      card.classList.toggle('flipped');
    }
  },

  async carregarGrafico() {
    const container = document.getElementById('dashboard-chart-container');
    if (!container) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.DASHBOARD_GRAFICOS);
      const meses = res.historico || [];

      if (!meses.length) {
        container.innerHTML = '<p class="mono-text" style="color: var(--color-on-surface-variant);">Sem dados suficientes para exibição do gráfico.</p>';
        return;
      }

      // Renderiza gráfico de barras em HTML/CSS puro
      let html = '<div style="width: 100%; display: flex; justify-content: space-between; align-items: flex-end; height: 180px; gap: 12px; padding-top: 20px;">';
      
      const maxValor = Math.max(...meses.map(m => Math.max(m.receitas || 0, m.despesas || 0)), 100);

      meses.forEach((m) => {
        const altRec = Math.round(((m.receitas || 0) / maxValor) * 140);
        const altDes = Math.round(((m.despesas || 0) / maxValor) * 140);

        html += `
          <div style="flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px; height: 100%; justify-content: flex-end;">
            <div style="display: flex; gap: 4px; align-items: flex-end; width: 100%; justify-content: center;">
              <!-- Barra de Receita -->
              <div style="width: 45%; max-width: 24px; height: ${Math.max(altRec, 4)}px; background-color: var(--color-success); title: 'Receitas: ${window.EMCUtils.formatarMoeda(m.receitas)}';"></div>
              <!-- Barra de Despesa -->
              <div style="width: 45%; max-width: 24px; height: ${Math.max(altDes, 4)}px; background-color: var(--color-error); title: 'Despesas: ${window.EMCUtils.formatarMoeda(m.despesas)}';"></div>
            </div>
            <span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); text-transform: uppercase;">${m.mes_sigla || m.mes}</span>
          </div>
        `;
      });

      html += '</div>';
      html += `
        <div style="display: flex; justify-content: center; gap: 24px; margin-top: 16px; font-size: 12px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 12px; height: 12px; background-color: var(--color-success);"></div>
            <span>Receitas Liquidadas</span>
          </div>
          <div style="display: flex; align-items: center; gap: 6px;">
            <div style="width: 12px; height: 12px; background-color: var(--color-error);"></div>
            <span>Despesas Pagas</span>
          </div>
        </div>
      `;

      container.innerHTML = html;
    } catch (err) {
      container.innerHTML = `<p class="mono-text" style="color: var(--color-error); font-size: 12px;">Erro ao carregar gráfico: ${window.EMCUtils.escapeHtml(err.message)}</p>`;
    }
  },

  async carregarFeed() {
    const container = document.getElementById('dashboard-feed-container');
    if (!container) return;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.DASHBOARD_FEED);
      const items = res.atividades || [];

      if (!items.length) {
        container.innerHTML = '<p class="mono-text" style="color: var(--color-on-surface-variant); font-size: 13px; padding: 16px 0;">Nenhuma atividade recente registrada.</p>';
        return;
      }

      let html = '<div style="display: flex; flex-direction: column; gap: 10px;">';
      items.forEach((item) => {
        html += `
          <div style="border-left: 2px solid var(--color-steel-gray); padding-left: 10px; font-size: 13px;">
            <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">${window.EMCUtils.formatarDataHoraPtBr(item.data_hora)}</div>
            <div><strong>${window.EMCUtils.escapeHtml(item.titulo)}</strong></div>
            <div style="color: var(--color-on-surface-variant); font-size: 12px;">${window.EMCUtils.escapeHtml(item.descricao || '')}</div>
          </div>
        `;
      });
      html += '</div>';

      container.innerHTML = html;
    } catch (err) {
      container.innerHTML = `<p class="mono-text" style="color: var(--color-error); font-size: 12px;">Erro ao carregar feed: ${window.EMCUtils.escapeHtml(err.message)}</p>`;
    }
  }
};
