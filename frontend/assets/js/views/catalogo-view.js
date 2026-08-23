/**
 * EMC Soldas - View de Catálogo e Motor BOM (Itens, Produtos e Ficha Técnica)
 */

window.CatalogoView = {
  currentTab: 'itens',

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CATÁLOGO & MOTOR BOM</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">GESTÃO DE INSUMOS, PRODUTOS FABRICADOS E COMPOSIÇÃO DE CUSTOS</p>
        </div>
      </div>

      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'itens' ? 'active' : ''}" id="tab-btn-itens">
          INSUMOS & MATÉRIA-PRIMA
        </button>
        <button class="tab-btn ${this.currentTab === 'produtos' ? 'active' : ''}" id="tab-btn-produtos">
          PRODUTOS & SERVIÇOS (RECEITAS BOM)
        </button>
      </div>

      <div id="catalogo-tab-content"></div>
    `;

    document.getElementById('tab-btn-itens')?.addEventListener('click', () => {
      this.currentTab = 'itens';
      this.render(container);
    });
    document.getElementById('tab-btn-produtos')?.addEventListener('click', () => {
      this.currentTab = 'produtos';
      this.render(container);
    });

    const content = document.getElementById('catalogo-tab-content');
    if (this.currentTab === 'itens') {
      this.renderItens(content);
    } else {
      this.renderProdutos(content);
    }
  },

  // ==========================================================================
  // 1. ITENS (MATÉRIA-PRIMA)
  // ==========================================================================
  async renderItens(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <input type="text" id="filtro-item-busca" class="form-control" placeholder="BUSCAR POR NOME DO INSUMO OU CÓDIGO..." style="max-width: 380px;">
          <button class="btn btn-primary" id="btn-novo-item">+ NOVO INSUMO / ITEM</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>NOME DO INSUMO</th>
              <th>UNIDADE COMPRA</th>
              <th>UNIDADE CONSUMO</th>
              <th>FATOR CONVERSÃO</th>
              <th>ÚLTIMO CUSTO (COMPRA)</th>
              <th>CUSTO CONSUMO</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-itens-tbody">
            <tr><td colspan="8" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-novo-item')?.addEventListener('click', () => this.abrirModalItem());
    document.getElementById('filtro-item-busca')?.addEventListener('input', () => this.carregarListaItens());

    await this.carregarListaItens();
  },

  async carregarListaItens() {
    const tbody = document.getElementById('lista-itens-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-item-busca')?.value.trim() || '';

    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.ITENS}?search=${encodeURIComponent(busca)}`);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum item cadastrado no catálogo.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((item) => {
        const uomCompra = item.unidade_compra_sigla || item.unidade_compra?.sigla || 'UN';
        const uomConsumo = item.unidade_consumo_sigla || item.unidade_consumo?.sigla || uomCompra;
        const fator = parseFloat(item.fator_conversao) || 1;
        const custoCompra = parseFloat(item.ultimo_custo_compra) || 0;
        const custoConsumo = fator > 0 ? (custoCompra / fator) : custoCompra;

        html += `
          <tr>
            <td class="mono-text">#${item.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(item.nome)}</strong></td>
            <td><span class="status-chip info">${window.EMCUtils.escapeHtml(uomCompra)}</span></td>
            <td><span class="status-chip warning">${window.EMCUtils.escapeHtml(uomConsumo)}</span></td>
            <td class="mono-text">${fator.toFixed(4)}</td>
            <td class="mono-text"><strong>${window.EMCUtils.formatarMoeda(custoCompra)}</strong></td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(custoConsumo)}</td>
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" onclick="window.CatalogoView.editarItem(${item.id})">EDITAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="8" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalItem(item = null) {
    const isEdit = !!item;

    // Carrega UOMs para o select
    const uoms = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM).catch(() => []);
    const listaUoms = uoms.results || uoms || [];

    let optionsUom = '';
    listaUoms.forEach((u) => {
      optionsUom += `<option value="${u.id}">${window.EMCUtils.escapeHtml(u.sigla)} - ${window.EMCUtils.escapeHtml(u.descricao)}</option>`;
    });

    window.EMCUtils.openModal({
      title: isEdit ? `EDITAR INSUMO #${item.id}` : 'NOVO INSUMO / ITEM (CATÁLOGO)',
      size: 'md',
      confirmText: isEdit ? 'ATUALIZAR' : 'CADASTRAR',
      content: `
        <form id="form-item">
          <div class="form-group">
            <label class="form-label" for="item-nome">Nome do Insumo *</label>
            <input type="text" id="item-nome" class="form-control" placeholder="EX: CHAPA DE AÇO CARBONO 1/4 POL" value="${item?.nome || ''}" required autofocus>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="item-uom-compra">Unidade de Compra (NF-e) *</label>
              <select id="item-uom-compra" class="form-control">
                ${optionsUom}
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" for="item-uom-consumo">Unidade de Consumo (Oficina) *</label>
              <select id="item-uom-consumo" class="form-control">
                ${optionsUom}
              </select>
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="item-fator">Fator de Conversão (Compra ➔ Consumo)</label>
              <input type="number" step="0.0001" id="item-fator" class="form-control mono-text" placeholder="1.0000" value="${item?.fator_conversao || '1.0000'}" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="item-custo">Último Custo de Compra</label>
              <input type="text" id="item-custo" class="form-control mono-text" data-mask="moeda-atm" value="${item ? window.EMCUtils.formatarMoeda(item.ultimo_custo_compra) : 'R$ 0,00'}">
            </div>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const nome = document.getElementById('item-nome').value.trim();
        const unidade_compra_id = document.getElementById('item-uom-compra').value;
        const unidade_consumo_id = document.getElementById('item-uom-consumo').value;
        const fator_conversao = parseFloat(document.getElementById('item-fator').value) || 1;
        const ultimo_custo_compra = window.EMCUtils.converterMoedaATMParaFloat(document.getElementById('item-custo').value);

        if (!nome || !unidade_compra_id) {
          window.EMCUtils.showToast('Nome e Unidade de Compra são obrigatórios.', 'error');
          return false;
        }

        try {
          const payload = {
            nome,
            unidade_compra_id,
            unidade_consumo_id,
            fator_conversao,
            ultimo_custo_compra
          };

          if (isEdit) {
            await window.api.put(`${window.CONFIG.ENDPOINTS.CATALOGO.ITENS}${item.id}/`, payload);
            window.EMCUtils.showToast('Item atualizado com sucesso!', 'success');
          } else {
            await window.api.post(window.CONFIG.ENDPOINTS.CATALOGO.ITENS, payload);
            window.EMCUtils.showToast('Item cadastrado com sucesso!', 'success');
          }
          this.carregarListaItens();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar item.', 'error');
          return false;
        }
      }
    });

    if (item) {
      if (item.unidade_compra_id) document.getElementById('item-uom-compra').value = item.unidade_compra_id;
      if (item.unidade_consumo_id) document.getElementById('item-uom-consumo').value = item.unidade_consumo_id;
    }
  },

  async editarItem(id) {
    try {
      const item = await window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.ITENS}${id}/`);
      this.abrirModalItem(item);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados do item.', 'error');
    }
  },

  // ==========================================================================
  // 2. PRODUTOS E RECEITAS BOM
  // ==========================================================================
  async renderProdutos(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <input type="text" id="filtro-prod-busca" class="form-control" placeholder="BUSCAR POR NOME DA PEÇA / SERVIÇO COMPOSTO..." style="max-width: 380px;">
          <button class="btn btn-primary" id="btn-novo-produto">+ NOVO PRODUTO / RECEITA BOM</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>PRODUTO / SERVIÇO</th>
              <th>UNIDADE</th>
              <th>MÃO DE OBRA (HORAS)</th>
              <th>CUSTO APURADO (BOM + M.O.)</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-prod-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-novo-produto')?.addEventListener('click', () => this.abrirModalProduto());
    document.getElementById('filtro-prod-busca')?.addEventListener('input', () => this.carregarListaProdutos());

    await this.carregarListaProdutos();
  },

  async carregarListaProdutos() {
    const tbody = document.getElementById('lista-prod-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-prod-busca')?.value.trim() || '';

    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS}?search=${encodeURIComponent(busca)}`);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum produto composto cadastrado.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((p) => {
        const uom = p.unidade_venda_sigla || p.unidade_venda?.sigla || 'UN';
        const horas = parseFloat(p.tempo_estimado_execucao) || 0;
        const custo = parseFloat(p.preco_custo_apurado) || 0;

        html += `
          <tr>
            <td class="mono-text">#${p.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(p.nome)}</strong></td>
            <td><span class="status-chip info">${window.EMCUtils.escapeHtml(uom)}</span></td>
            <td class="mono-text">${horas.toFixed(2)} h</td>
            <td class="mono-text" style="color: var(--color-success); font-weight: 700; font-size: 15px;">
              ${window.EMCUtils.formatarMoeda(custo)}
            </td>
            <td style="text-align: right;">
              <button class="btn btn-secondary btn-sm" onclick="window.CatalogoView.gerenciarFichaTecnica(${p.id})">FICHA TÉCNICA (BOM)</button>
              <button class="btn btn-ghost btn-sm" onclick="window.CatalogoView.editarProduto(${p.id})">EDITAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalProduto(prod = null) {
    const isEdit = !!prod;

    window.EMCUtils.openModal({
      title: isEdit ? `EDITAR PRODUTO #${prod.id}` : 'NOVO PRODUTO / RECEITA DE SERVIÇO',
      size: 'md',
      confirmText: isEdit ? 'ATUALIZAR' : 'CADASTRAR',
      content: `
        <form id="form-produto">
          <div class="form-group">
            <label class="form-label" for="prod-nome">Nome do Produto / Peça *</label>
            <input type="text" id="prod-nome" class="form-control" placeholder="EX: REFORMA DE CAÇAMBA COM REVESTIMENTO HARDOX" value="${prod?.nome || ''}" required autofocus>
          </div>

          <div class="form-group">
            <label class="form-label" for="prod-descricao">Descrição / Especificação Técnica</label>
            <textarea id="prod-descricao" class="form-control" rows="3" placeholder="DETALHAMENTO DA FABRICAÇÃO...">${prod?.descricao || ''}</textarea>
          </div>

          <div class="form-group">
            <label class="form-label" for="prod-horas">Tempo Estimado de Mão de Obra (Horas) *</label>
            <input type="number" step="0.25" id="prod-horas" class="form-control mono-text" placeholder="EX: 4.50" value="${prod?.tempo_estimado_execucao || '1.00'}" required>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const nome = document.getElementById('prod-nome').value.trim();
        const descricao = document.getElementById('prod-descricao').value.trim();
        const tempo_estimado_execucao = parseFloat(document.getElementById('prod-horas').value) || 0;

        if (!nome) {
          window.EMCUtils.showToast('O nome do produto é obrigatório.', 'error');
          return false;
        }

        try {
          const payload = { nome, descricao, tempo_estimado_execucao };

          if (isEdit) {
            await window.api.put(`${window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS}${prod.id}/`, payload);
            window.EMCUtils.showToast('Produto atualizado!', 'success');
          } else {
            await window.api.post(window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS, payload);
            window.EMCUtils.showToast('Produto cadastrado! Agora monte a Ficha Técnica BOM.', 'success');
          }
          this.carregarListaProdutos();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar produto.', 'error');
          return false;
        }
      }
    });
  },

  async editarProduto(id) {
    try {
      const prod = await window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS}${id}/`);
      this.abrirModalProduto(prod);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados do produto.', 'error');
    }
  },

  async gerenciarFichaTecnica(produtoId) {
    try {
      const [prod, itensCatalogo] = await Promise.all([
        window.api.get(`${window.CONFIG.ENDPOINTS.CATALOGO.PRODUTOS}${produtoId}/`),
        window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.ITENS)
      ]);

      const listaItens = itensCatalogo.results || itensCatalogo || [];
      const ficha = prod.ficha_tecnica || [];

      let optionsItens = '<option value="">SELECIONE UM INSUMO...</option>';
      listaItens.forEach((it) => {
        const uom = it.unidade_consumo_sigla || 'UN';
        optionsItens += `<option value="${it.id}">${window.EMCUtils.escapeHtml(it.nome)} (${uom})</option>`;
      });

      let rowsFicha = '';
      ficha.forEach((f) => {
        const custoUnit = parseFloat(f.custo_unitario_consumo) || 0;
        const subtotal = (parseFloat(f.quantidade_utilizada) || 0) * custoUnit;
        rowsFicha += `
          <tr id="ficha-row-${f.id}">
            <td><strong>${window.EMCUtils.escapeHtml(f.item_nome || 'Insumo')}</strong></td>
            <td class="mono-text">${parseFloat(f.quantidade_utilizada).toFixed(4)} ${f.unidade_sigla || ''}</td>
            <td class="mono-text">${window.EMCUtils.formatarMoeda(custoUnit)}</td>
            <td class="mono-text" style="color: var(--color-rust-orange); font-weight: 700;">${window.EMCUtils.formatarMoeda(subtotal)}</td>
            <td style="text-align: right;">
              <button class="btn btn-danger btn-sm" onclick="window.CatalogoView.removerItemFicha(${produtoId}, ${f.id})">REMOVER</button>
            </td>
          </tr>
        `;
      });

      window.EMCUtils.openModal({
        title: `FICHA TÉCNICA (BOM) - ${prod.nome}`,
        size: 'lg',
        hideFooter: true,
        content: `
          <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
            <h4 style="margin-bottom: 12px;">ADICIONAR INSUMO À RECEITA DO PRODUTO</h4>
            <div style="display: grid; grid-template-columns: 2fr 1fr auto; gap: 12px; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Insumo do Catálogo</label>
                <select id="add-ficha-item-id" class="form-control">${optionsItens}</select>
              </div>
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Quantidade Consumida</label>
                <input type="number" step="0.0001" id="add-ficha-qtd" class="form-control mono-text" placeholder="1.0000">
              </div>
              <button class="btn btn-primary" id="btn-add-item-ficha" style="height: 42px;">+ ADICIONAR</button>
            </div>
          </div>

          <div class="table-container mb-16">
            <table class="table">
              <thead>
                <tr>
                  <th>INSUMO</th>
                  <th>QUANTIDADE</th>
                  <th>CUSTO CONSUMO</th>
                  <th>SUBTOTAL</th>
                  <th style="text-align: right;">AÇÕES</th>
                </tr>
              </thead>
              <tbody id="ficha-tecnica-tbody">
                ${rowsFicha || '<tr><td colspan="5" class="text-center mono-text" style="padding: 16px;">Nenhum insumo adicionado a esta ficha técnica.</td></tr>'}
              </tbody>
            </table>
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; background-color: var(--color-surface-container-low); padding: 16px; border: 1px solid var(--color-steel-gray);">
            <div>
              <span class="mono-text" style="font-size: 13px;">MÃO DE OBRA: <strong>${parseFloat(prod.tempo_estimado_execucao || 0).toFixed(2)} Horas</strong></span>
            </div>
            <div>
              <span class="mono-text" style="font-size: 16px; color: var(--color-success);">PREÇO DE CUSTO APURADO: <strong>${window.EMCUtils.formatarMoeda(prod.preco_custo_apurado || 0)}</strong></span>
            </div>
          </div>
        `
      });

      document.getElementById('btn-add-item-ficha')?.addEventListener('click', async () => {
        const item_id = document.getElementById('add-ficha-item-id').value;
        const quantidade_utilizada = parseFloat(document.getElementById('add-ficha-qtd').value);

        if (!item_id || !quantidade_utilizada || quantidade_utilizada <= 0) {
          window.EMCUtils.showToast('Selecione um insumo e informe uma quantidade válida.', 'warning');
          return;
        }

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.CATALOGO.FICHAS_TECNICAS, {
            produto_id: produtoId,
            item_id,
            quantidade_utilizada
          });
          window.EMCUtils.showToast('Insumo adicionado à Ficha Técnica!', 'success');
          this.gerenciarFichaTecnica(produtoId);
          this.carregarListaProdutos();
        } catch (e) {
          window.EMCUtils.showToast(e.message || 'Erro ao adicionar insumo na ficha.', 'error');
        }
      });
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar Ficha Técnica.', 'error');
    }
  },

  async removerItemFicha(produtoId, fichaId) {
    try {
      await window.api.delete(`${window.CONFIG.ENDPOINTS.CATALOGO.FICHAS_TECNICAS}${fichaId}/`);
      window.EMCUtils.showToast('Insumo removido da Ficha Técnica.', 'info');
      this.gerenciarFichaTecnica(produtoId);
      this.carregarListaProdutos();
    } catch (e) {
      window.EMCUtils.showToast('Erro ao remover insumo.', 'error');
    }
  }
};
