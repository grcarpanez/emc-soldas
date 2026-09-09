/**
 * EMC Soldas - View de Compras (Notas Fiscais de Entrada e Retroalimentação de Custos)
 */

window.ComprasView = {
  async render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">COMPRAS & NOTAS DE ENTRADA</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">REGISTRO DE NOTAS FISCAIS E RETROALIMENTAÇÃO DO MOTOR DE CUSTOS (BOM)</p>
        </div>
      </div>

      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-compra-busca" class="form-control" placeholder="BUSCAR POR NÚMERO DA NOTA, CHAVE OU FORNECEDOR..." style="flex: 1; min-width: 240px;">
          <div style="width: 260px; min-width: 220px; flex-shrink: 0;" id="wrapper-filtro-fornecedor">
            <select id="filtro-compra-fornecedor" class="form-control">
              <option value="">TODOS OS FORNECEDORES</option>
            </select>
          </div>
          <span id="total-compras-badge" class="status-chip secondary mono-text" style="padding: 7px 12px; flex-shrink: 0;">0 NOTAS</span>
          <button class="btn btn-primary" id="btn-nova-compra" style="white-space: nowrap; flex-shrink: 0;">+ LANÇAR NOTA DE COMPRA</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>NÚMERO DA NOTA</th>
              <th>FORNECEDOR</th>
              <th>DATA DA COMPRA</th>
              <th>VALOR TOTAL</th>
              <th>CHAVE DE ACESSO (44 DÍGITOS)</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-compras-tbody">
            <tr><td colspan="7" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-nova-compra')?.addEventListener('click', () => this.abrirModalCompra());
    document.getElementById('filtro-compra-busca')?.addEventListener('input', () => this.carregarListaCompras());
    document.getElementById('filtro-compra-fornecedor')?.addEventListener('change', () => this.carregarListaCompras());

    await this.carregarSelectFornecedoresFiltro();
    await this.carregarListaCompras();
  },

  async carregarSelectFornecedoresFiltro() {
    const select = document.getElementById('filtro-compra-fornecedor');
    if (!select) return;

    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?tipo=FORNECEDOR`);
      const fornecedores = res.results || res || [];
      fornecedores.sort((a, b) => (a.nome_razao || '').localeCompare(b.nome_razao || ''));

      select.innerHTML = '<option value="">TODOS OS FORNECEDORES</option>';
      fornecedores.forEach((f) => {
        const opt = document.createElement('option');
        opt.value = f.id;
        opt.textContent = f.nome_razao;
        select.appendChild(opt);
      });

      window.EMCUtils.initSearchableSelect(select, {
        placeholder: 'TODOS OS FORNECEDORES'
      });
    } catch (e) {
      console.warn('Erro ao carregar fornecedores para filtro de compras:', e);
      window.EMCUtils.initSearchableSelect(select, {
        placeholder: 'TODOS OS FORNECEDORES'
      });
    }
  },

  async carregarListaCompras() {
    const tbody = document.getElementById('lista-compras-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-compra-busca')?.value.trim() || '';
    const fornecedor = document.getElementById('filtro-compra-fornecedor')?.value || '';

    try {
      let url = `${window.CONFIG.ENDPOINTS.COMPRAS.NOTAS}?search=${encodeURIComponent(busca)}`;
      if (fornecedor) {
        url += `&fornecedor_id=${fornecedor}`;
      }
      const res = await window.api.get(url);
      const lista = res.results || res || [];

      const badge = document.getElementById('total-compras-badge');
      if (badge) {
        const count = lista.length;
        badge.textContent = `${count} ${count === 1 ? 'NOTA' : 'NOTAS'}`;
      }

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhuma nota de compra lançada.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((nota) => {
        const chaveFmt = nota.chave_acesso ? window.EMCUtils.formatarChaveAcessoNfe(nota.chave_acesso) : '-';
        html += `
          <tr>
            <td class="mono-text">#${nota.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(nota.num_nota)}</strong></td>
            <td>${window.EMCUtils.escapeHtml(nota.fornecedor_nome || 'Fornecedor')}</td>
            <td class="mono-text">${window.EMCUtils.formatarDataPtBr(nota.data_compra)}</td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">
              ${window.EMCUtils.formatarMoeda(nota.valor_total)}
            </td>
            <td class="mono-text" style="font-size: 11px; max-width: 220px; word-break: break-all;">${chaveFmt}</td>
            <td style="text-align: right;">
              <button class="btn btn-secondary btn-sm" onclick="window.ComprasView.verDetalhesNota(${nota.id})">ITENS</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalCompra() {
    // Carrega fornecedores e itens para o formulário
    const [fornecedores, itens] = await Promise.all([
      window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?tipo=FORNECEDOR`),
      window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.ITENS)
    ]);

    const listaForn = fornecedores.results || fornecedores || [];
    const listaItens = itens.results || itens || [];

    let optionsForn = '<option value="">SELECIONE O FORNECEDOR...</option>';
    listaForn.forEach((f) => {
      optionsForn += `<option value="${f.id}">${window.EMCUtils.escapeHtml(f.nome_razao)}</option>`;
    });

    let optionsItens = '<option value="">SELECIONE UM INSUMO...</option>';
    listaItens.forEach((it) => {
      const uom = it.unidade_compra_sigla || 'UN';
      optionsItens += `<option value="${it.id}">${window.EMCUtils.escapeHtml(it.nome)} (${uom})</option>`;
    });

    window.EMCUtils.openModal({
      title: 'LANÇAR NOTA FISCAL DE ENTRADA (COMPRA)',
      size: 'lg',
      confirmText: 'REGISTRAR COMPRA',
      content: `
        <form id="form-compra-nota">
          <div style="display: grid; grid-template-columns: 1fr 1fr 140px; gap: 12px;">
            <div class="form-group">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <label class="form-label" for="nota-fornecedor" style="margin-bottom: 0;">Fornecedor *</label>
                <button type="button" class="btn btn-ghost btn-sm" id="btn-compras-novo-forn" style="padding: 0 6px; font-size: 11px; height: 22px; color: var(--color-rust-orange);" title="Cadastrar Novo Fornecedor">+ NOVO FORNECEDOR</button>
              </div>
              <select id="nota-fornecedor" class="form-control" required>${optionsForn}</select>
            </div>
            <div class="form-group">
              <label class="form-label" for="nota-numero">Número da Nota (NF-e / Recibo) *</label>
              <input type="text" id="nota-numero" class="form-control mono-text" placeholder="EX: 000.123.456" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="nota-data">Data de Emissão *</label>
              <input type="date" id="nota-data" class="form-control mono-text" value="${new Date().toISOString().split('T')[0]}" required>
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="nota-chave">Chave de Acesso NFe (44 Dígitos - Opcional)</label>
            <input type="text" id="nota-chave" class="form-control mono-text" data-mask="chave-nfe" placeholder="0000 0000 0000 0000 0000 0000 0000 0000 0000 0000 0000">
          </div>

          <!-- Sub-Grid de Itens Comprados -->
          <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
            <h4 style="margin-bottom: 12px;">ITENS COMPRADOS (RETROALIMENTAÇÃO DE CUSTOS)</h4>
            <div style="display: grid; grid-template-columns: 2fr 1fr 1fr auto; gap: 8px; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Insumo</label>
                <select id="sub-item-id" class="form-control">${optionsItens}</select>
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Quantidade Comprada</label>
                <input type="number" step="0.0001" id="sub-item-qtd" class="form-control mono-text" placeholder="1.0000">
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Valor Unitário</label>
                <input type="text" id="sub-item-unit" class="form-control mono-text" data-mask="moeda-atm" value="R$ 0,00">
              </div>
              <button type="button" class="btn btn-secondary" id="btn-add-item-nota" style="height: 42px;">+ ADICIONAR</button>
            </div>
          </div>

          <div class="table-container mb-16">
            <table class="table">
              <thead>
                <tr>
                  <th>INSUMO</th>
                  <th>QUANTIDADE</th>
                  <th>VALOR UNITÁRIO</th>
                  <th>SUBTOTAL</th>
                  <th style="text-align: right;">AÇÃO</th>
                </tr>
              </thead>
              <tbody id="itens-nota-grid-tbody">
                <tr><td colspan="5" class="text-center mono-text" style="padding: 12px;">Nenhum item adicionado ainda.</td></tr>
              </tbody>
            </table>
          </div>

          <div style="display: flex; justify-content: flex-end; align-items: center; gap: 12px;">
            <span class="mono-text" style="font-size: 14px;">VALOR TOTAL DA NOTA:</span>
            <span class="mono-text" id="nota-total-display" style="font-size: 20px; font-weight: 700; color: var(--color-rust-orange);">R$ 0,00</span>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const fornecedor_id = document.getElementById('nota-fornecedor').value;
        const num_nota = document.getElementById('nota-numero').value.trim();
        const data_compra = document.getElementById('nota-data').value;
        const chave_acesso = window.EMCUtils.extrairApenasDigitos(document.getElementById('nota-chave').value);

        if (!fornecedor_id || !num_nota || !data_compra) {
          window.EMCUtils.showToast('Preencha os campos obrigatórios da nota.', 'error');
          return false;
        }

        if (!this.itensTemp || !this.itensTemp.length) {
          window.EMCUtils.showToast('Adicione ao menos um item comprado na nota.', 'warning');
          return false;
        }

        try {
          const payload = {
            fornecedor_id,
            num_nota,
            data_compra,
            chave_acesso,
            itens_comprados: this.itensTemp.map(it => ({
              item_id: it.item_id,
              quantidade_comprada: it.quantidade_comprada,
              valor_unitario: it.valor_unitario
            }))
          };

          await window.api.post(window.CONFIG.ENDPOINTS.COMPRAS.NOTAS, payload);
          window.EMCUtils.showToast('Nota registrada e custos dos insumos atualizados com sucesso!', 'success');
          this.carregarListaCompras();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao registrar nota fiscal.', 'error');
          return false;
        }
      }
    });

    const selForn = document.getElementById('nota-fornecedor');
    const selItem = document.getElementById('sub-item-id');

    const dispararCadastroNovoFornecedor = () => {
      window.CadastrosView.abrirModalCadastroCompleto(null, {
        tipoPredefinido: 'FORNECEDOR',
        onSuccess: async (novoForn) => {
          if (!novoForn || !novoForn.id) return;
          try {
            // Recarrega a lista de fornecedores do servidor
            const fornecedoresAtualizados = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?tipo=FORNECEDOR`);
            const listaFornAtualizada = fornecedoresAtualizados.results || fornecedoresAtualizados || [];
            listaFornAtualizada.sort((a, b) => (a.nome_razao || '').localeCompare(b.nome_razao || ''));

            let novasOptions = '<option value="">SELECIONE O FORNECEDOR...</option>';
            listaFornAtualizada.forEach((f) => {
              novasOptions += `<option value="${f.id}" ${f.id === novoForn.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(f.nome_razao)}</option>`;
            });

            if (selForn) {
              if (selForn._emcCombobox) {
                selForn._emcCombobox.updateOptions(novasOptions, novoForn.id);
              } else {
                selForn.innerHTML = novasOptions;
                selForn.value = novoForn.id;
              }
            }
            window.EMCUtils.showToast(`Fornecedor "${novoForn.nome_razao}" selecionado automaticamente!`, 'success');
          } catch (e) {
            console.error('Erro ao atualizar fornecedores:', e);
          }
        }
      });
    };

    if (selForn) {
      window.EMCUtils.initSearchableSelect(selForn, {
        placeholder: 'SELECIONE OU PESQUISE O FORNECEDOR...',
        action: {
          label: '+ CADASTRAR NOVO FORNECEDOR',
          onClick: () => dispararCadastroNovoFornecedor()
        }
      });
    }

    if (selItem) {
      window.EMCUtils.initSearchableSelect(selItem, {
        placeholder: 'PESQUISE UM INSUMO...'
      });
    }

    document.getElementById('btn-compras-novo-forn')?.addEventListener('click', (e) => {
      e.preventDefault();
      dispararCadastroNovoFornecedor();
    });

    this.itensTemp = [];
    const btnAdd = document.getElementById('btn-add-item-nota');
    btnAdd?.addEventListener('click', () => {
      const selectItem = document.getElementById('sub-item-id');
      const item_id = selectItem.value;
      const item_nome = selectItem.options[selectItem.selectedIndex]?.text || 'Insumo';
      const quantidade_comprada = parseFloat(document.getElementById('sub-item-qtd').value);
      const valor_unitario = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('sub-item-unit').value);

      if (!item_id || !quantidade_comprada || quantidade_comprada <= 0 || valor_unitario <= 0) {
        window.EMCUtils.showToast('Informe um insumo, quantidade e valor unitário válidos.', 'warning');
        return;
      }

      this.itensTemp.push({ item_id, item_nome, quantidade_comprada, valor_unitario });
      this.atualizarGridItensNota();

      // Limpa campos
      if (selectItem._emcCombobox) {
        selectItem._emcCombobox.setValue('');
      } else {
        selectItem.value = '';
      }
      document.getElementById('sub-item-qtd').value = '';
      document.getElementById('sub-item-unit').value = 'R$ 0,00';
    });
  },

  atualizarGridItensNota() {
    const tbody = document.getElementById('itens-nota-grid-tbody');
    const totalEl = document.getElementById('nota-total-display');
    if (!tbody) return;

    if (!this.itensTemp.length) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center mono-text" style="padding: 12px;">Nenhum item adicionado ainda.</td></tr>';
      if (totalEl) totalEl.textContent = 'R$ 0,00';
      return;
    }

    let total = 0;
    let html = '';
    this.itensTemp.forEach((it, idx) => {
      const subtotal = it.quantidade_comprada * it.valor_unitario;
      total += subtotal;
      html += `
        <tr>
          <td><strong>${window.EMCUtils.escapeHtml(it.item_nome)}</strong></td>
          <td class="mono-text">${it.quantidade_comprada.toFixed(4)}</td>
          <td class="mono-text">${window.EMCUtils.formatarMoeda(it.valor_unitario)}</td>
          <td class="mono-text">${window.EMCUtils.formatarMoeda(subtotal)}</td>
          <td style="text-align: right;">
            <button type="button" class="btn btn-danger btn-sm" onclick="window.ComprasView.removerItemTemp(${idx})">X</button>
          </td>
        </tr>
      `;
    });

    tbody.innerHTML = html;
    if (totalEl) totalEl.textContent = window.EMCUtils.formatarMoeda(total);
  },

  removerItemTemp(index) {
    if (this.itensTemp && this.itensTemp[index]) {
      this.itensTemp.splice(index, 1);
      this.atualizarGridItensNota();
    }
  },

  async verDetalhesNota(notaId) {
    try {
      const nota = await window.api.get(`${window.CONFIG.ENDPOINTS.COMPRAS.NOTAS}${notaId}/`);
      const itens = nota.itens_comprados || [];

      let rows = '';
      itens.forEach((it) => {
        const sub = (parseFloat(it.quantidade_comprada) || 0) * (parseFloat(it.valor_unitario) || 0);
        rows += `
          <tr>
            <td><strong>${window.EMCUtils.escapeHtml(it.item_nome || 'Insumo')}</strong></td>
            <td class="mono-text">${parseFloat(it.quantidade_comprada).toFixed(4)}</td>
            <td class="mono-text">${window.EMCUtils.formatarMoeda(it.valor_unitario)}</td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(sub)}</td>
          </tr>
        `;
      });

      window.EMCUtils.openModal({
        title: `DETALHES DA NOTA FISCAL #${nota.num_nota}`,
        size: 'md',
        hideFooter: true,
        content: `
          <div style="margin-bottom: 16px; font-size: 13px;">
            • <strong>Fornecedor:</strong> ${window.EMCUtils.escapeHtml(nota.fornecedor_nome)}<br>
            • <strong>Data:</strong> ${window.EMCUtils.formatarDataPtBr(nota.data_compra)}<br>
            • <strong>Chave NFe:</strong> <span class="mono-text" style="font-size: 11px;">${window.EMCUtils.formatarChaveAcessoNfe(nota.chave_acesso || '') || '-'}</span>
          </div>

          <div class="table-container mb-16">
            <table class="table">
              <thead>
                <tr>
                  <th>INSUMO</th>
                  <th>QUANTIDADE</th>
                  <th>VALOR UNITÁRIO</th>
                  <th>SUBTOTAL</th>
                </tr>
              </thead>
              <tbody>${rows}</tbody>
            </table>
          </div>

          <div class="text-right">
            <span class="mono-text" style="font-size: 16px; color: var(--color-rust-orange); font-weight: 700;">
              TOTAL: ${window.EMCUtils.formatarMoeda(nota.valor_total)}
            </span>
          </div>
        `
      });
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar detalhes da nota.', 'error');
    }
  }
};
