/**
 * EMC Soldas - View de Central Analítica e Relatórios Estratégicos
 * Inadimplência, Dossiê do Cliente, Curvas ABC, DRE e Exportações PDF/CSV.
 */

window.RelatoriosView = {
  currentTab: 'inadimplencia',

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CENTRAL ANALÍTICA & RELATÓRIOS</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">GESTÃO DE INADIMPLÊNCIA, CURVAS ABC, DRE E EXPORTAÇÕES PROFISSIONAIS</p>
        </div>
      </div>

      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'inadimplencia' ? 'active' : ''}" id="tab-btn-rel-inad">
          INADIMPLÊNCIA
        </button>
        <button class="tab-btn ${this.currentTab === 'dossie' ? 'active' : ''}" id="tab-btn-rel-dossie">
          DOSSIÊ DO CLIENTE
        </button>
        <button class="tab-btn ${this.currentTab === 'curva-clientes' ? 'active' : ''}" id="tab-btn-rel-abc-cli">
          CURVA ABC (CLIENTES)
        </button>
        <button class="tab-btn ${this.currentTab === 'curva-itens' ? 'active' : ''}" id="tab-btn-rel-abc-it">
          CURVA ABC (ITENS)
        </button>
        <button class="tab-btn ${this.currentTab === 'dre' ? 'active' : ''}" id="tab-btn-rel-dre">
          DRE SIMPLIFICADO
        </button>
        <button class="tab-btn ${this.currentTab === 'divergencias' ? 'active' : ''}" id="tab-btn-rel-div">
          DIVERGÊNCIAS CONCILIAÇÃO
        </button>
      </div>

      <div id="relatorios-tab-content"></div>
    `;

    document.getElementById('tab-btn-rel-inad')?.addEventListener('click', () => {
      this.currentTab = 'inadimplencia';
      this.render(container);
    });
    document.getElementById('tab-btn-rel-dossie')?.addEventListener('click', () => {
      this.currentTab = 'dossie';
      this.render(container);
    });
    document.getElementById('tab-btn-rel-abc-cli')?.addEventListener('click', () => {
      this.currentTab = 'curva-clientes';
      this.render(container);
    });
    document.getElementById('tab-btn-rel-abc-it')?.addEventListener('click', () => {
      this.currentTab = 'curva-itens';
      this.render(container);
    });
    document.getElementById('tab-btn-rel-dre')?.addEventListener('click', () => {
      this.currentTab = 'dre';
      this.render(container);
    });
    document.getElementById('tab-btn-rel-div')?.addEventListener('click', () => {
      this.currentTab = 'divergencias';
      this.render(container);
    });

    const content = document.getElementById('relatorios-tab-content');
    if (this.currentTab === 'inadimplencia') {
      this.renderInadimplencia(content);
    } else if (this.currentTab === 'dossie') {
      this.renderDossie(content);
    } else if (this.currentTab === 'curva-clientes') {
      this.renderCurvaClientes(content);
    } else if (this.currentTab === 'curva-itens') {
      this.renderCurvaItens(content);
    } else if (this.currentTab === 'dre') {
      this.renderDre(content);
    } else if (this.currentTab === 'divergencias') {
      this.renderDivergencias(content);
    }
  },

  // ==========================================================================
  // 1. INADIMPLÊNCIA
  // ==========================================================================
  async renderInadimplencia(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">AUDITORIA DE FATURAS VENCIDAS E GESTÃO INTERNA DE COBRANÇA</p>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" id="btn-exp-inad-csv">EXPORTAR CSV</button>
            <button class="btn btn-primary btn-sm" id="btn-exp-inad-pdf">EXPORTAR PDF</button>
          </div>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>FATURA</th>
              <th>CLIENTE</th>
              <th>TELEFONE / CONTATO</th>
              <th>VENCIMENTO</th>
              <th>DIAS EM ATRASO</th>
              <th>VALOR EM ABERTO</th>
            </tr>
          </thead>
          <tbody id="lista-inad-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-exp-inad-csv')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.INADIMPLENCIA}?exportar=csv`, 'Inadimplencia.csv');
    });
    document.getElementById('btn-exp-inad-pdf')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.INADIMPLENCIA}?exportar=pdf`, 'Inadimplencia.pdf');
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.INADIMPLENCIA);
      const lista = res.faturas_vencidas || res.results || res || [];
      const tbody = document.getElementById('lista-inad-tbody');

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-success); padding: 24px;">Parabéns! Não existem faturas em atraso no momento.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((f) => {
        html += `
          <tr>
            <td class="mono-text"><strong>#${f.fatura_id || f.id}</strong></td>
            <td><strong>${window.EMCUtils.escapeHtml(f.cliente_nome)}</strong></td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(f.telefone ? window.EMCUtils.formatarTelefoneDinamico(f.telefone) : '-')}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(f.data_vencimento)}</td>
            <td><span class="status-chip danger">${f.dias_atraso || 0} DIAS</span></td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-error); font-size: 15px;">
              ${window.EMCUtils.formatarMoeda(f.valor_pendente || f.valor)}
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-inad-tbody').innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  // ==========================================================================
  // 2. DOSSIÊ DO CLIENTE
  // ==========================================================================
  async renderDossie(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant); margin-bottom: 12px;">SELECIONE O CLIENTE PARA APURAÇÃO COMPLETA DO HISTÓRICO:</p>
        <div style="display: flex; gap: 12px; align-items: center; flex-wrap: wrap;">
          <select id="sel-dossie-cliente" class="form-control" style="flex: 1; min-width: 280px;">
            <option value="">CARREGANDO CLIENTES...</option>
          </select>
          <button class="btn btn-primary" id="btn-carregar-dossie">GERAR DOSSIÊ</button>
        </div>
      </div>

      <div id="dossie-resultado-container">
        <p class="mono-text text-center" style="padding: 40px; color: var(--color-on-surface-variant);">Selecione um cliente acima para gerar o relatório.</p>
      </div>
    `;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES);
      const clientes = res.results || res || [];
      let options = '<option value="">SELECIONE UM CLIENTE...</option>';
      clientes.forEach((c) => { options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome_razao)}</option>`; });
      const sel = document.getElementById('sel-dossie-cliente');
      if (sel) sel.innerHTML = options;
    } catch (e) {}

    document.getElementById('btn-carregar-dossie')?.addEventListener('click', () => {
      const clienteId = document.getElementById('sel-dossie-cliente')?.value;
      if (clienteId) this.carregarDossieCliente(clienteId);
    });
  },

  async carregarDossieCliente(clienteId) {
    const container = document.getElementById('dossie-resultado-container');
    if (!container) return;

    container.innerHTML = `<div class="text-center" style="padding: 40px;"><div class="loader-spinner"></div></div>`;

    try {
      const endpoint = window.CONFIG.ENDPOINTS.RELATORIOS.DOSSIE_CLIENTE.replace('{id}', clienteId);
      const res = await window.api.get(endpoint);

      container.innerHTML = `
        <div class="card mb-16">
          <div class="card-header">
            <h3>${window.EMCUtils.escapeHtml(res.cliente?.nome_razao || 'Dossiê Comercial')}</h3>
            <span class="status-chip success">CLIENTE ATIVO</span>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 20px;">
            <div style="background-color: var(--color-surface-container-high); padding: 16px; border-left: 3px solid var(--color-rust-orange);">
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">TOTAL ORÇAMENTOS</div>
              <div class="mono-text" style="font-size: 20px; font-weight: 700;">${res.total_orcamentos || 0}</div>
            </div>
            <div style="background-color: var(--color-surface-container-high); padding: 16px; border-left: 3px solid var(--color-success);">
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">TOTAL FATURADO</div>
              <div class="mono-text" style="font-size: 20px; font-weight: 700; color: var(--color-success);">${window.EMCUtils.formatarMoeda(res.total_faturado || 0)}</div>
            </div>
            <div style="background-color: var(--color-surface-container-high); padding: 16px; border-left: 3px solid var(--color-warning);">
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">PRODUTOS (MATERIAIS)</div>
              <div class="mono-text" style="font-size: 20px; font-weight: 700;">${window.EMCUtils.formatarMoeda(res.total_produtos || 0)}</div>
            </div>
            <div style="background-color: var(--color-surface-container-high); padding: 16px; border-left: 3px solid #8ac8f0;">
              <div class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">SERVIÇOS (REFORMAS)</div>
              <div class="mono-text" style="font-size: 20px; font-weight: 700;">${window.EMCUtils.formatarMoeda(res.total_servicos || 0)}</div>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      container.innerHTML = `<div class="alert-banner alert-danger">${window.EMCUtils.escapeHtml(err.message)}</div>`;
    }
  },

  // ==========================================================================
  // 3. CURVA ABC (CLIENTES)
  // ==========================================================================
  async renderCurvaClientes(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CLASSIFICAÇÃO PARETO (CLASSE A: 80% / CLASSE B: 15% / CLASSE C: 5%)</p>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" id="btn-exp-abc-cli-csv">EXPORTAR CSV</button>
            <button class="btn btn-primary btn-sm" id="btn-exp-abc-cli-pdf">EXPORTAR PDF</button>
          </div>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>POSIÇÃO</th>
              <th>CLIENTE</th>
              <th>RECEITA GERADA</th>
              <th>% DO FATURAMENTO</th>
              <th>% ACUMULADA</th>
              <th>CLASSE</th>
            </tr>
          </thead>
          <tbody id="lista-abc-cli-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-exp-abc-cli-csv')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.CURVA_ABC_CLIENTES}?exportar=csv`, 'CurvaABC_Clientes.csv');
    });
    document.getElementById('btn-exp-abc-cli-pdf')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.CURVA_ABC_CLIENTES}?exportar=pdf`, 'CurvaABC_Clientes.pdf');
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.CURVA_ABC_CLIENTES);
      const lista = res.ranking || res.results || res || [];
      const tbody = document.getElementById('lista-abc-cli-tbody');

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Sem dados para cálculo da Curva ABC.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((c, idx) => {
        const badgeClasse = c.classe === 'A' ? 'success' : (c.classe === 'B' ? 'warning' : 'info');
        html += `
          <tr>
            <td class="mono-text"><strong>#${idx + 1}</strong></td>
            <td><strong>${window.EMCUtils.escapeHtml(c.cliente_nome)}</strong></td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${window.EMCUtils.formatarMoeda(c.valor_total)}</td>
            <td class="mono-text">${parseFloat(c.percentual || 0).toFixed(2)} %</td>
            <td class="mono-text">${parseFloat(c.percentual_acumulado || 0).toFixed(2)} %</td>
            <td><span class="status-chip ${badgeClasse}">CLASSE ${c.classe}</span></td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-abc-cli-tbody').innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  // ==========================================================================
  // 4. CURVA ABC (ITENS)
  // ==========================================================================
  async renderCurvaItens(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CONSUMO E VENDAS POR INSUMO (MATRIZ PARETO 80/15/5)</p>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" id="btn-exp-abc-it-csv">EXPORTAR CSV</button>
            <button class="btn btn-primary btn-sm" id="btn-exp-abc-it-pdf">EXPORTAR PDF</button>
          </div>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>POSIÇÃO</th>
              <th>INSUMO / ITEM</th>
              <th>QUANTIDADE CONSUMIDA</th>
              <th>VALOR TOTAL (R$)</th>
              <th>% ACUMULADA</th>
              <th>CLASSE</th>
            </tr>
          </thead>
          <tbody id="lista-abc-it-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-exp-abc-it-csv')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.CURVA_ABC_ITENS}?exportar=csv`, 'CurvaABC_Itens.csv');
    });
    document.getElementById('btn-exp-abc-it-pdf')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.CURVA_ABC_ITENS}?exportar=pdf`, 'CurvaABC_Itens.pdf');
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.CURVA_ABC_ITENS);
      const lista = res.ranking || res.results || res || [];
      const tbody = document.getElementById('lista-abc-it-tbody');

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Sem dados para apuração.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((item, idx) => {
        const badgeClasse = item.classe === 'A' ? 'success' : (item.classe === 'B' ? 'warning' : 'info');
        html += `
          <tr>
            <td class="mono-text"><strong>#${idx + 1}</strong></td>
            <td><strong>${window.EMCUtils.escapeHtml(item.item_nome)}</strong></td>
            <td class="mono-text">${parseFloat(item.quantidade_total || 0).toFixed(2)}</td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${window.EMCUtils.formatarMoeda(item.valor_total)}</td>
            <td class="mono-text">${parseFloat(item.percentual_acumulado || 0).toFixed(2)} %</td>
            <td><span class="status-chip ${badgeClasse}">CLASSE ${item.classe}</span></td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-abc-it-tbody').innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  // ==========================================================================
  // 5. DRE SIMPLIFICADO
  // ==========================================================================
  async renderDre(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">DEMONSTRAÇÃO DO RESULTADO DO EXERCÍCIO (DRE SIMPLIFICADO)</p>
          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary btn-sm" id="btn-exp-dre-csv">EXPORTAR CSV</button>
            <button class="btn btn-primary btn-sm" id="btn-exp-dre-pdf">EXPORTAR PDF</button>
          </div>
        </div>
      </div>

      <div class="card" id="dre-linhas-card" style="padding: 24px;">
        <div class="text-center"><div class="loader-spinner"></div></div>
      </div>
    `;

    document.getElementById('btn-exp-dre-csv')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.DRE}?exportar=csv`, 'DRE_Simplificado.csv');
    });
    document.getElementById('btn-exp-dre-pdf')?.addEventListener('click', () => {
      window.api.downloadFile(`${window.CONFIG.ENDPOINTS.RELATORIOS.DRE}?exportar=pdf`, 'DRE_Simplificado.pdf');
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.DRE);
      const card = document.getElementById('dre-linhas-card');

      const recBruta = parseFloat(res.receita_bruta) || 0;
      const ded = parseFloat(res.deducoes) || 0;
      const recLiq = parseFloat(res.receita_liquida) || (recBruta - ded);
      const custos = parseFloat(res.custos_variaveis) || 0;
      const lucroBruto = recLiq - custos;
      const despOper = parseFloat(res.despesas_operacionais) || 0;
      const resLiq = lucroBruto - despOper;

      card.innerHTML = `
        <div style="font-size: 15px; line-height: 2.2;">
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--color-steel-gray); padding: 6px 0;">
            <span>(+) RECEITA BRUTA OPERACIONAL:</span>
            <strong class="mono-text" style="color: var(--color-success);">${window.EMCUtils.formatarMoeda(recBruta)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--color-steel-gray); padding: 6px 0;">
            <span>(-) DEDUÇÕES E DESCONTOS CONCEDIDOS:</span>
            <strong class="mono-text" style="color: var(--color-error);">${window.EMCUtils.formatarMoeda(ded)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 2px solid var(--color-steel-gray); padding: 8px 0; background-color: var(--color-surface-container-high);">
            <span>(=) RECEITA LÍQUIDA OPERACIONAL:</span>
            <strong class="mono-text" style="font-size: 16px;">${window.EMCUtils.formatarMoeda(recLiq)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--color-steel-gray); padding: 6px 0;">
            <span>(-) CUSTOS VARIÁVEIS / INSUMOS:</span>
            <strong class="mono-text" style="color: var(--color-error);">${window.EMCUtils.formatarMoeda(custos)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 2px solid var(--color-steel-gray); padding: 8px 0; background-color: var(--color-surface-container-high);">
            <span>(=) LUCRO BRUTO:</span>
            <strong class="mono-text" style="font-size: 16px;">${window.EMCUtils.formatarMoeda(lucroBruto)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; border-bottom: 1px solid var(--color-steel-gray); padding: 6px 0;">
            <span>(-) DESPESAS OPERACIONAIS / FIXAS:</span>
            <strong class="mono-text" style="color: var(--color-error);">${window.EMCUtils.formatarMoeda(despOper)}</strong>
          </div>
          <div style="display: flex; justify-content: space-between; padding: 12px 0; background-color: var(--color-surface-container-lowest); border: 2px solid ${resLiq >= 0 ? 'var(--color-success)' : 'var(--color-error)'}; margin-top: 12px; padding: 12px 16px;">
            <span style="font-size: 16px; font-weight: 700;">(=) RESULTADO LÍQUIDO DO EXERCÍCIO:</span>
            <strong class="mono-text" style="font-size: 20px; color: ${resLiq >= 0 ? 'var(--color-success)' : 'var(--color-error)'};">${window.EMCUtils.formatarMoeda(resLiq)}</strong>
          </div>
        </div>
      `;
    } catch (err) {
      document.getElementById('dre-linhas-card').innerHTML = `<div class="alert-banner alert-danger">${window.EMCUtils.escapeHtml(err.message)}</div>`;
    }
  },

  // ==========================================================================
  // 6. DIVERGÊNCIAS DE CONCILIAÇÃO
  // ==========================================================================
  async renderDivergencias(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">AUDITORIA DE TRANSAÇÕES NÃO CONCILIADAS (SOBRAS DO EXTRATO VS SOBRAS DO ERP)</p>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ORIGEM</th>
              <th>DATA</th>
              <th>DESCRIÇÃO</th>
              <th>VALOR</th>
              <th>STATUS DE AUDITORIA</th>
            </tr>
          </thead>
          <tbody id="lista-div-tbody">
            <tr><td colspan="5" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.RELATORIOS.DIVERGENCIAS_CONCILIACAO);
      const lista = res.divergencias || res.results || res || [];
      const tbody = document.getElementById('lista-div-tbody');

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="5" class="text-center mono-text" style="padding: 24px;">Nenhuma divergência bancária em aberto.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((d) => {
        html += `
          <tr>
            <td><span class="status-chip warning">${d.origem || 'ERP'}</span></td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(d.data)}</td>
            <td><strong>${window.EMCUtils.escapeHtml(d.descricao)}</strong></td>
            <td class="mono-text" style="font-weight: 700;">${window.EMCUtils.formatarMoeda(d.valor)}</td>
            <td><span class="status-chip danger">PENDENTE DE MATCH</span></td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-div-tbody').innerHTML = `<tr><td colspan="5" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  }
};
