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
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-fat-busca" class="form-control" placeholder="BUSCAR POR CLIENTE, NÚMERO OU ID..." style="flex: 1; min-width: 200px;">
          <div style="width: 240px; min-width: 200px; flex-shrink: 0;" id="wrapper-fat-status">
            <select id="filtro-fat-status" class="form-control">
              <option value="RASCUNHO">RASCUNHO (PRÉ-FATURA)</option>
              <option value="FATURADA">FATURADA</option>
              <option value="PAGA">PAGA (QUITADA)</option>
              <option value="CANCELADA">CANCELADA</option>
            </select>
          </div>
          <span id="total-fat-badge" class="status-chip secondary mono-text" style="padding: 7px 12px; flex-shrink: 0;">0 FATURAS</span>
          <button class="btn btn-secondary" id="btn-ir-conta-corrente" style="white-space: nowrap; flex-shrink: 0;">VER CONTA CORRENTE (A FATURAR)</button>
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

    const selStatusFat = document.getElementById('filtro-fat-status');
    if (selStatusFat) {
      window.EMCUtils.initMultiSelectCombobox(selStatusFat, {
        placeholder: 'TODOS OS STATUS',
        prefix: 'STATUS',
        onChange: () => this.carregarListaFaturas()
      });
    }

    document.getElementById('filtro-fat-busca')?.addEventListener('input', () => this.carregarListaFaturas());
    document.getElementById('btn-ir-conta-corrente')?.addEventListener('click', () => {
      this.currentTab = 'conta-corrente';
      this.render(document.getElementById('app-root'));
    });

    this.carregarListaFaturas();
  },

  async carregarListaFaturas() {
    const tbody = document.getElementById('lista-fat-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-fat-busca')?.value.trim() || '';
    const selStatus = document.getElementById('filtro-fat-status');
    const status = selStatus?._emcMultiSelect ? selStatus._emcMultiSelect.getValues().join(',') : (selStatus?.value || '');

    try {
      const query = new URLSearchParams();
      if (busca) query.append('search', busca);
      if (status) query.append('status', status);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAS}?${query.toString()}`);
      const lista = res.results || res || [];

      const badge = document.getElementById('total-fat-badge');
      if (badge) {
        const count = lista.length;
        badge.textContent = `${count} ${count === 1 ? 'FATURA' : 'FATURAS'}`;
      }

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
            <td><span class="status-chip ${badgeStatus}">${f.status === 'RASCUNHO' ? 'RASCUNHO (PRÉ-FATURA)' : f.status}</span></td>
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
          SELECIONE O CLIENTE PARA AGRUPAR ORÇAMENTOS APROVADOS OU CONCLUÍDOS E GERAR PRÉ-FATURA (MOMENTO 1):
        </p>
        <div style="display: flex; gap: 12px; align-items: flex-end; flex-wrap: wrap;">
          <div class="form-group" style="margin-bottom: 0; flex: 1; min-width: 320px;">
            <label class="form-label" for="cc-filtro-cliente">Cliente</label>
            <select id="cc-filtro-cliente" class="form-control">
              <option value="">CARREGANDO CLIENTES...</option>
            </select>
          </div>
          <button class="btn btn-primary" id="btn-gerar-pre-fatura" style="height: 42px;">+ CONSOLIDAR EM PRÉ-FATURA</button>
        </div>
      </div>

      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 13px; flex-wrap: wrap; gap: 8px;">
        <span id="cc-resumo-selecao" class="mono-text" style="font-weight: 600; color: var(--color-on-surface-variant);">Nenhum orçamento selecionado</span>
        <span id="cc-total-selecao" class="mono-text" style="font-size: 14px; font-weight: 700; color: var(--color-rust-orange);">Total: R$ 0,00</span>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th style="width: 40px;"><input type="checkbox" id="check-todos-orc" title="Selecionar Todos"></th>
              <th>ORÇAMENTO</th>
              <th>EQUIPAMENTO</th>
              <th>DATA CONCLUSÃO / GERAÇÃO</th>
              <th>STATUS OPERACIONAL</th>
              <th>VALOR LÍQUIDO</th>
            </tr>
          </thead>
          <tbody id="cc-orcamentos-tbody">
            <tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Selecione um cliente acima para visualizar os orçamentos prontos para faturamento.</td></tr>
          </tbody>
        </table>
      </div>
    `;

    // Carrega clientes e dados da conta corrente para mapear pendências
    try {
      const [resClientes, resCC] = await Promise.all([
        window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?page_size=1000`),
        window.api.get(window.CONFIG.ENDPOINTS.FATURAMENTO.CONTA_CORRENTE)
      ]);
      const todosClientes = resClientes.results || resClientes || [];
      const clientes = todosClientes.filter(c => (c.tipo || '').toUpperCase() !== 'FORNECEDOR');
      const orcsCC = resCC.results || resCC || [];

      // Mapeia contagem de orçamentos faturáveis por cliente
      const contagemPorCliente = {};
      orcsCC.forEach(o => {
        const cId = o.cliente_id || (o.cliente && o.cliente.id);
        if (cId) {
          contagemPorCliente[cId] = (contagemPorCliente[cId] || 0) + 1;
        }
      });

      let options = '<option value="">SELECIONE UM CLIENTE...</option>';
      clientes.forEach((c) => {
        const qtd = contagemPorCliente[c.id] || 0;
        const sufixo = qtd > 0 ? ` [${qtd} ${qtd === 1 ? 'orçamento a faturar' : 'orçamentos a faturar'}]` : '';
        options += `<option value="${c.id}">${window.EMCUtils.escapeHtml(c.nome_razao)}${sufixo}</option>`;
      });

      const selectCli = document.getElementById('cc-filtro-cliente');
      if (selectCli) {
        selectCli.innerHTML = options;
        window.EMCUtils.initSearchableSelect(selectCli, {
          placeholder: 'SELECIONE UM CLIENTE...',
          onChange: (val) => this.carregarOrcamentosCliente(val)
        });
      }
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar clientes da conta corrente.', 'error');
    }

    document.getElementById('btn-gerar-pre-fatura')?.addEventListener('click', () => this.abrirModalNovaPreFatura());
  },

  atualizarResumoSelecao() {
    const checks = document.querySelectorAll('.check-orc-item:checked');
    const totalCount = checks.length;
    let soma = 0;
    checks.forEach(c => {
      soma += (parseFloat(c.dataset.valor) || 0);
    });

    const elResumo = document.getElementById('cc-resumo-selecao');
    const elTotal = document.getElementById('cc-total-selecao');
    if (elResumo) {
      elResumo.textContent = totalCount === 0 
        ? 'Nenhum orçamento selecionado.'
        : `${totalCount} ${totalCount === 1 ? 'orçamento selecionado' : 'orçamentos selecionados'}`;
    }
    if (elTotal) {
      elTotal.textContent = `Total: ${window.EMCUtils.formatarMoeda(soma)}`;
    }
  },

  async carregarOrcamentosCliente(clienteId) {
    const tbody = document.getElementById('cc-orcamentos-tbody');
    if (!tbody) return;

    this.atualizarResumoSelecao();

    if (!clienteId) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="padding: 24px;">Selecione um cliente acima para visualizar a conta corrente.</td></tr>';
      return;
    }

    try {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>';
      const endpoint = `${window.CONFIG.ENDPOINTS.FATURAMENTO.CONTA_CORRENTE}?cliente_id=${clienteId}`;
      const res = await window.api.get(endpoint);
      const orcamentos = res.orcamentos || res.results || res || [];

      if (!orcamentos.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum orçamento aprovado ou concluído pendente de faturamento para este cliente.</td></tr>';
        this.atualizarResumoSelecao();
        return;
      }

      let html = '';
      orcamentos.forEach((orc) => {
        const badgeOp = {
          APROVADO: 'success',
          EM_EXECUCAO: 'warning',
          CONCLUIDO: 'success',
          GERADO: 'info',
          ENVIADO: 'info',
          CANCELADO: 'danger'
        }[orc.status_operacional] || 'info';

        const valorLiq = orc.valor_liquido !== undefined ? orc.valor_liquido : ((orc.valor_bruto || orc.valor_total || 0) - (orc.valor_desconto_aplicado || 0));

        html += `
          <tr>
            <td><input type="checkbox" class="check-orc-item" value="${orc.id}" data-valor="${valorLiq}"></td>
            <td class="mono-text"><strong>#${orc.id}</strong></td>
            <td>${window.EMCUtils.escapeHtml(orc.equipamento_descricao || orc.equipamento_placa || 'Oficina Geral')}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(orc.data_conclusao || orc.data_geracao)}</td>
            <td><span class="status-chip ${badgeOp}">${window.EMCUtils.formatarStatus(orc.status_operacional)}</span></td>
            <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${window.EMCUtils.formatarMoeda(valorLiq)}</td>
          </tr>
        `;
      });

      tbody.innerHTML = html;

      // Listener para marcar todos
      const checkTodos = document.getElementById('check-todos-orc');
      if (checkTodos) {
        checkTodos.checked = false;
        checkTodos.addEventListener('change', (e) => {
          document.querySelectorAll('.check-orc-item').forEach((chk) => { chk.checked = e.target.checked; });
          this.atualizarResumoSelecao();
        });
      }

      // Listeners individuais
      document.querySelectorAll('.check-orc-item').forEach((chk) => {
        chk.addEventListener('change', () => {
          this.atualizarResumoSelecao();
          const all = document.querySelectorAll('.check-orc-item');
          const checked = document.querySelectorAll('.check-orc-item:checked');
          if (checkTodos) checkTodos.checked = all.length > 0 && checked.length === all.length;
        });
      });

      this.atualizarResumoSelecao();
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
      this.atualizarResumoSelecao();
    }
  },

  // ==========================================================================
  // MOMENTO 1: ABERTURA DO MODAL PARA GERAR PRÉ-FATURA (RASCUNHO COM OPÇÕES)
  // ==========================================================================
  async abrirModalNovaPreFatura() {
    const selectCli = document.getElementById('cc-filtro-cliente');
    const clienteId = selectCli?.value;
    const clienteNome = selectCli?.selectedOptions[0]?.text?.split('[')[0]?.trim() || 'Cliente';

    const checks = Array.from(document.querySelectorAll('.check-orc-item:checked'));
    const selecionados = checks.map(chk => parseInt(chk.value, 10));

    if (!clienteId || !selecionados.length) {
      window.EMCUtils.showToast('Selecione um cliente e ao menos um orçamento para consolidar em pré-fatura.', 'warning');
      return;
    }

    // Calcula valor bruto total dos selecionados
    let totalBruto = 0;
    checks.forEach(chk => {
      const val = parseFloat(chk.dataset.valor) || 0;
      totalBruto += val;
    });

    try {
      // Busca regras de pagamento ativas para ofertar opções ao cliente
      const resRegras = await window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.REGRAS_PAGAMENTO);
      const regras = (resRegras.results || resRegras || []).filter(r => r.ativo !== false);

      let htmlRegras = '';
      regras.forEach((r) => {
        const parcTxt = r.numero_parcelas > 1 ? `${r.numero_parcelas}x` : 'À vista';
        htmlRegras += `
          <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-bottom: 1px solid var(--color-border); font-size: 13px;">
            <label style="display: flex; align-items: center; gap: 8px; cursor: pointer; margin-bottom: 0;">
              <input type="checkbox" class="check-regra-proposta" value="${r.id}" checked>
              <strong>${window.EMCUtils.escapeHtml(r.nome)}</strong>
              <span class="mono-text" style="color: var(--color-on-surface-variant); font-size: 11px;">(${r.meio_pagamento_nome || 'Meio'} - ${parcTxt})</span>
            </label>
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">Desconto:</span>
              <input type="number" step="0.01" min="0" max="100" class="form-control mono-text input-desc-proposta" data-regra-id="${r.id}" value="${r.desconto_concedido_padrao || 0}" style="width: 75px; height: 28px; padding: 2px 6px; font-size: 12px; text-align: right;">
              <span class="mono-text" style="font-size: 12px;">%</span>
            </div>
          </div>
        `;
      });

      window.EMCUtils.openModal({
        title: `GERAR PRÉ-FATURA (RASCUNHO) - ${clienteNome}`,
        size: 'lg',
        confirmText: 'GERAR PRÉ-FATURA (RASCUNHO)',
        cancelText: 'CANCELAR',
        content: `
          <div class="card mb-16" style="background-color: var(--color-surface-container-high); padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
              <div>
                <strong>${selecionados.length} ${selecionados.length === 1 ? 'Orçamento Selecionado' : 'Orçamentos Selecionados'}</strong>
                <div class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">
                  IDs: #${selecionados.join(', #')}
                </div>
              </div>
              <div style="text-align: right;">
                <span style="font-size: 12px; color: var(--color-on-surface-variant);">Valor Bruto Consolidado:</span><br>
                <span class="mono-text" style="font-size: 16px; font-weight: 700; color: var(--color-rust-orange);" id="modal-prefat-bruto">${window.EMCUtils.formatarMoeda(totalBruto)}</span>
              </div>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px;">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="prefat-desconto-global">Desconto da Pré-Fatura / Negociação Inicial (R$)</label>
              <input type="text" id="prefat-desconto-global" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label">Total Previsto da Pré-Fatura</label>
              <div class="form-control mono-text" id="prefat-total-previsto" style="background-color: var(--color-surface-container); font-weight: 700; color: var(--color-rust-orange); display: flex; align-items: center;">
                ${window.EMCUtils.formatarMoeda(totalBruto)}
              </div>
            </div>
          </div>

          <div style="margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
              <label class="form-label" style="margin-bottom: 0;">
                OPÇÕES DE PAGAMENTO A OFERTAR AO CLIENTE NO PDF ESPELHO *
              </label>
              <div style="display: flex; gap: 6px;">
                <button type="button" class="btn btn-ghost btn-sm" id="btn-marcar-todas-regras" style="font-size: 11px; padding: 2px 8px;">SELECIONAR TODAS</button>
                <button type="button" class="btn btn-ghost btn-sm" id="btn-desmarcar-todas-regras" style="font-size: 11px; padding: 2px 8px;">LIMPAR</button>
              </div>
            </div>
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-bottom: 8px;">
              Marque as condições de pagamento que você deseja sugerir no PDF espelho para que o cliente escolha:
            </p>
            <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--color-border); background-color: var(--color-surface);">
              ${htmlRegras || '<div class="p-16 text-center mono-text">Nenhuma regra de pagamento ativa encontrada.</div>'}
            </div>
          </div>

          <div class="card" style="background-color: var(--color-surface-container); border-left: 4px solid var(--color-steel-gray); padding: 10px 14px; font-size: 12px;">
            <strong style="color: var(--color-on-surface);">ℹ Momento 1 - Negociação e Espelho:</strong>
            <p style="margin: 4px 0 0; color: var(--color-on-surface-variant);">
              Esta Pré-Fatura será gerada em Rascunho. O sistema não lançará nenhum título no Contas a Receber neste momento. Você poderá baixar o PDF com as opções simuladas e enviar ao cliente. Quando o cliente responder com a opção escolhida, você fará o fechamento definitivo na lista de faturas.
            </p>
          </div>
        `,
        onConfirm: async () => {
          const descStr = document.getElementById('prefat-desconto-global')?.value || 'R$ 0,00';
          const desconto_global = window.EMCUtils.converterMoedaATMParaFloat(descStr);

          // Coleta regras marcadas
          const regrasMarcadas = Array.from(document.querySelectorAll('.check-regra-proposta:checked'));
          if (!regrasMarcadas.length) {
            window.EMCUtils.showToast('Selecione pelo menos uma opção de pagamento para ofertar ao cliente.', 'warning');
            return false;
          }

          const propostas_pagamento = regrasMarcadas.map(chk => {
            const rId = parseInt(chk.value, 10);
            const inputDesc = document.querySelector(`.input-desc-proposta[data-regra-id="${rId}"]`);
            const descVal = inputDesc ? parseFloat(inputDesc.value) || 0 : 0;
            return {
              regra_pagamento: rId,
              desconto_personalizado: descVal
            };
          });

          try {
            const payload = {
              cliente: parseInt(clienteId, 10),
              orcamento_ids: selecionados,
              desconto_global: desconto_global,
              propostas_pagamento: propostas_pagamento
            };

            const res = await window.api.post(window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAS, payload);
            window.EMCUtils.showToast(`Pré-Fatura #${res.id} gerada em rascunho com sucesso!`, 'success');
            
            // Alterna para aba de faturas e abre o detalhe da pré-fatura recém-criada
            this.currentTab = 'faturas';
            this.render(document.getElementById('app-root'));
            this.verDetalhesFatura(res.id);
            return true;
          } catch (err) {
            window.EMCUtils.showToast(err.message || 'Erro ao gerar pré-fatura.', 'error');
            return false;
          }
        }
      });

      // Listeners dentro do modal
      const inputDesc = document.getElementById('prefat-desconto-global');
      const divPrevisto = document.getElementById('prefat-total-previsto');
      if (inputDesc && divPrevisto) {
        inputDesc.addEventListener('input', () => {
          const desc = window.EMCUtils.converterMoedaATMParaFloat(inputDesc.value);
          const finalPrevisto = Math.max(0, totalBruto - desc);
          divPrevisto.textContent = window.EMCUtils.formatarMoeda(finalPrevisto);
        });
      }

      document.getElementById('btn-marcar-todas-regras')?.addEventListener('click', () => {
        document.querySelectorAll('.check-regra-proposta').forEach(c => { c.checked = true; });
      });
      document.getElementById('btn-desmarcar-todas-regras')?.addEventListener('click', () => {
        document.querySelectorAll('.check-regra-proposta').forEach(c => { c.checked = false; });
      });

    } catch (e) {
      window.EMCUtils.showToast('Erro ao preparar geração da pré-fatura.', 'error');
    }
  },

  // ==========================================================================
  // MOMENTO 2: DETALHES, VISUALIZAÇÃO E FECHAMENTO DEFINITIVO DA FATURA
  // ==========================================================================
  async verDetalhesFatura(faturaId) {
    try {
      const [fatura, regras] = await Promise.all([
        window.api.get(`${window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAS}${faturaId}/`),
        window.api.get(window.CONFIG.ENDPOINTS.FINANCEIRO.REGRAS_PAGAMENTO)
      ]);

      const listaRegras = regras.results || regras || [];
      let optionsRegras = '<option value="">SELECIONE A FORMA DE PAGAMENTO DEFINITIVA...</option>';
      listaRegras.forEach((r) => {
        optionsRegras += `<option value="${r.id}" ${fatura.regra_pagamento_id === r.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(r.nome)}</option>`;
      });

      const orcamentos = fatura.orcamentos_agrupados || fatura.orcamentos || [];
      let rowsOrc = '';
      orcamentos.forEach((o) => {
        rowsOrc += `
          <tr>
            <td class="mono-text"><strong>#${o.id}</strong></td>
            <td>${window.EMCUtils.escapeHtml(o.equipamento_descricao || o.equipamento_placa || '-')}</td>
            <td><span class="status-chip success">${window.EMCUtils.formatarStatus(o.status_operacional)}</span></td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(o.valor_liquido || o.valor_total || o.valor_bruto)}</td>
          </tr>
        `;
      });

      // Propostas de pagamento simuladas na pré-fatura
      const propostas = fatura.propostas_simuladas || fatura.propostas_pagamento || [];
      let htmlPropostas = '';
      if (propostas.length) {
        let rowsProp = '';
        propostas.forEach((p) => {
          const descTxt = p.desconto_percentual ? `${p.desconto_percentual}%` : (p.desconto_personalizado ? `${p.desconto_personalizado}%` : 'Sem desc.');
          const parcTxt = p.numero_parcelas > 1 ? `${p.numero_parcelas}x de ${window.EMCUtils.formatarMoeda(p.valor_parcela)}` : 'À vista';
          rowsProp += `
            <tr>
              <td><strong>${window.EMCUtils.escapeHtml(p.regra_nome || p.regra_pagamento_nome || 'Opção')}</strong></td>
              <td>${window.EMCUtils.escapeHtml(p.meio_pagamento_nome || '-')}</td>
              <td>${parcTxt}</td>
              <td class="mono-text">${descTxt}</td>
              <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${p.valor_final ? window.EMCUtils.formatarMoeda(p.valor_final) : '-'}</td>
            </tr>
          `;
        });

        htmlPropostas = `
          <h4 style="margin-bottom: 8px;">OPÇÕES DE PAGAMENTO OFERTADAS NO ESPELHO DA PRÉ-FATURA</h4>
          <div class="table-container mb-16">
            <table class="table">
              <thead><tr><th>REGRA DE PAGAMENTO</th><th>MEIO</th><th>PARCELAMENTO</th><th>DESCONTO</th><th>VALOR SIMULADO</th></tr></thead>
              <tbody>${rowsProp}</tbody>
            </table>
          </div>
        `;
      }

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
            <td><span class="status-chip ${badge}">${window.EMCUtils.formatarStatus(p.status_pagamento)}</span></td>
          </tr>
        `;
      });

      const badgeStatus = {
        RASCUNHO: 'warning',
        FATURADA: 'info',
        PAGA: 'success',
        CANCELADA: 'danger'
      }[fatura.status] || 'info';

      const tituloModal = fatura.status === 'RASCUNHO' 
        ? `PRÉ-FATURA #${fatura.id} - ${fatura.cliente_nome} [RASCUNHO]`
        : `FATURA #${fatura.id} - ${fatura.cliente_nome} [${fatura.status}]`;

      window.EMCUtils.openModal({
        title: tituloModal,
        size: 'lg',
        hideFooter: true,
        content: `
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 16px; font-size: 13px;">
            <div>
              • <strong>Cliente:</strong> ${window.EMCUtils.escapeHtml(fatura.cliente_nome)}<br>
              • <strong>Data de Emissão:</strong> ${window.EMCUtils.formatarDataPtBr(fatura.data_emissao)}<br>
              • <strong>Status da Fatura:</strong> <span class="status-chip ${badgeStatus}">${fatura.status === 'RASCUNHO' ? 'RASCUNHO (PRÉ-FATURA)' : fatura.status}</span>
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

          ${htmlPropostas}

          ${fatura.status === 'RASCUNHO' ? `
            <div class="card mb-16" style="background-color: var(--color-surface-container-high); border-left: 4px solid var(--color-rust-orange);">
              <h4 style="margin-bottom: 8px;">MOMENTO 2: FECHAMENTO DE FATURA FINAL (GERAR CONTAS A RECEBER)</h4>
              <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-bottom: 12px;">
                Após o cliente confirmar a condição de pagamento desejada, selecione a regra escolhida, ajuste o desconto final acordado e conclua o faturamento definitivo para gerar as parcelas no Contas a Receber.
              </p>
              <div style="display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 12px; align-items: flex-end;">
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Regra de Pagamento Escolhida pelo Cliente *</label>
                  <select id="fechar-fat-regra" class="form-control">${optionsRegras}</select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Desconto Final (R$)</label>
                  <input type="text" id="fechar-fat-desconto" class="form-control mono-text" data-mask="moeda-atm" value="${window.EMCUtils.formatarMoeda(fatura.desconto_global || 0)}">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label">Nº NF-e (Opcional)</label>
                  <input type="text" id="fechar-fat-nfe" class="form-control mono-text" placeholder="EX: 1042">
                </div>
                <button class="btn btn-primary" id="btn-confirmar-faturamento" style="height: 42px; white-space: nowrap;">✔ FATURAR DEFINITIVO</button>
              </div>
            </div>
          ` : ''}

          ${parcelas.length ? `
            <h4 style="margin-bottom: 8px;">PARCELAS GERADAS NO CONTAS A RECEBER</h4>
            <div class="table-container mb-16">
              <table class="table">
                <thead><tr><th>ID</th><th>DESCRIÇÃO</th><th>VENCIMENTO</th><th>VALOR</th><th>STATUS</th></tr></thead>
                <tbody>${rowsParc}</tbody>
              </table>
            </div>
          ` : ''}

          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 16px;">
            <div style="display: flex; gap: 8px; flex-wrap: wrap;">
              <button class="btn btn-primary" onclick="window.FaturamentoView.baixarPdfFatura(${fatura.id})">
                ${fatura.status === 'RASCUNHO' ? 'BAIXAR PDF ESPELHO (ENVIAR AO CLIENTE)' : 'BAIXAR PDF (FATURA OFICIAL)'}
              </button>
              ${fatura.status === 'FATURADA' ? `
                <button class="btn btn-secondary" onclick="window.FaturamentoView.abrirModalRecebimento(${fatura.id})">REGISTRAR RECEBIMENTO</button>
                <button class="btn btn-ghost" onclick="window.FaturamentoView.quitarCortesia(${fatura.id})">CORTESIA (100%)</button>
              ` : ''}
            </div>

            ${fatura.status !== 'CANCELADA' && fatura.status !== 'PAGA' ? `
              <button class="btn btn-danger" onclick="window.FaturamentoView.abrirModalCancelarFatura(${fatura.id})">
                ${fatura.status === 'RASCUNHO' ? 'CANCELAR PRÉ-FATURA' : 'CANCELAR FATURA'}
              </button>
            ` : ''}
          </div>
        `
      });

      document.getElementById('btn-confirmar-faturamento')?.addEventListener('click', async () => {
        const regra_pagamento_id = document.getElementById('fechar-fat-regra').value;
        const desconto_global = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('fechar-fat-desconto').value);
        const numero_nfe_venda = document.getElementById('fechar-fat-nfe')?.value.trim() || null;

        if (!regra_pagamento_id) {
          window.EMCUtils.showToast('Selecione uma regra de pagamento para faturar.', 'warning');
          return;
        }

        try {
          const endpoint = window.CONFIG.ENDPOINTS.FATURAMENTO.FATURAR.replace('{id}', faturaId);
          await window.api.post(endpoint, { regra_pagamento_id, desconto_global, numero_nfe_venda });
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
