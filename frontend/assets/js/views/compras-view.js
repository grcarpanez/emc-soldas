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
        const temAnexo = Boolean(nota.caminho_arquivo_anexo);
        const btnDanfe = temAnexo 
          ? `<button class="btn btn-secondary btn-sm" onclick="window.ComprasView.baixarDanfe(${nota.id}, '${window.EMCUtils.escapeHtml(nota.num_nota)}')" title="Baixar DANFE / XML" style="margin-right: 6px; color: var(--color-rust-orange);">📄 DANFE</button>`
          : '';

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
            <td style="text-align: right; white-space: nowrap;">
              ${btnDanfe}
              <button class="btn btn-secondary btn-sm" onclick="window.ComprasView.verDetalhesNota(${nota.id})" title="Ver Itens da Nota" style="margin-right: 4px;">ITENS</button>
              <button class="btn btn-secondary btn-sm" onclick="window.ComprasView.abrirModalCompra(${nota.id})" title="Editar Nota Fiscal" style="margin-right: 4px;">EDITAR</button>
              <button class="btn btn-danger btn-sm" onclick="window.ComprasView.confirmarCancelamentoNota(${nota.id}, '${window.EMCUtils.escapeHtml(nota.num_nota)}', '${window.EMCUtils.escapeHtml(nota.fornecedor_nome || 'Fornecedor')}', '${window.EMCUtils.formatarMoeda(nota.valor_total)}')" title="Cancelar Compra">CANCELAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalCompra(notaId = null) {
    try {
      const isEdit = Boolean(notaId);

      // Carrega fornecedores, catálogo de itens e a nota existente (se for edição)
      const promessas = [
        window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?tipo=FORNECEDOR`),
        window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.ITENS)
      ];
      if (isEdit) {
        promessas.push(window.api.get(`${window.CONFIG.ENDPOINTS.COMPRAS.NOTAS}${notaId}/`));
      }

      const resultados = await Promise.all(promessas);
      const fornecedores = resultados[0];
      const itens = resultados[1];
      const notaExistente = isEdit ? resultados[2] : null;

      const listaForn = fornecedores.results || fornecedores || [];
      const listaItens = itens.results || itens || [];

      const notaFornecedorId = notaExistente ? (notaExistente.fornecedor || notaExistente.fornecedor_id) : '';
      const notaNumero = notaExistente ? (notaExistente.num_nota || '') : '';
      const notaData = notaExistente ? (notaExistente.data_compra || '') : new Date().toISOString().split('T')[0];
      const notaChave = notaExistente && notaExistente.chave_acesso ? window.EMCUtils.formatarChaveAcessoNfe(notaExistente.chave_acesso) : '';
      const temAnexoExistente = Boolean(notaExistente && notaExistente.caminho_arquivo_anexo);

      let optionsForn = '<option value="">SELECIONE O FORNECEDOR...</option>';
      listaForn.forEach((f) => {
        const isSel = String(f.id) === String(notaFornecedorId);
        optionsForn += `<option value="${f.id}" ${isSel ? 'selected' : ''}>${window.EMCUtils.escapeHtml(f.nome_razao)}</option>`;
      });

      let optionsItens = '<option value="">SELECIONE UM INSUMO...</option>';
      listaItens.forEach((it) => {
        const uom = it.unidade_compra_sigla || 'UN';
        optionsItens += `<option value="${it.id}">${window.EMCUtils.escapeHtml(it.nome)} (${uom})</option>`;
      });

      // Inicializa a lista temporária de itens
      if (isEdit && notaExistente && Array.isArray(notaExistente.itens_comprados)) {
        this.itensTemp = notaExistente.itens_comprados.map(it => ({
          item_id: it.item || it.item_id,
          item_nome: it.item_nome || 'Insumo',
          quantidade_comprada: parseFloat(it.quantidade_comprada) || 1,
          valor_unitario: parseFloat(it.valor_unitario) || 0
        }));
      } else {
        this.itensTemp = [];
      }

      window.EMCUtils.openModal({
        title: isEdit ? `EDITAR NOTA FISCAL DE ENTRADA #${notaNumero}` : 'LANÇAR NOTA FISCAL DE ENTRADA (COMPRA)',
        size: 'lg',
        confirmText: isEdit ? 'SALVAR ALTERAÇÕES' : 'REGISTRAR COMPRA',
        content: `
        <form id="form-compra-nota">
          <!-- 1º CAMPO EM DESTAQUE NO TOPO: IMPORTAÇÃO INTELIGENTE DO DOCUMENTO FISCAL -->
          <div class="card mb-16" style="background-color: var(--color-surface-container-high); border-left: 3px solid var(--color-rust-orange);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
              <label class="form-label" for="nota-arquivo-anexo" style="margin-bottom: 0; font-weight: 700;">
                1. ${isEdit ? 'ARQUIVO ANEXO DA NOTA FISCAL (DANFE EM PDF OU XML)' : 'IMPORTAR DOCUMENTO FISCAL (DANFE EM PDF OU XML DA NF-E)'}
              </label>
              <span id="status-analise-doc" class="mono-text" style="font-size: 11px; display: none;"></span>
            </div>
            ${temAnexoExistente ? `
              <div class="mb-8 p-8" style="background: var(--color-surface-container-low); border: 1px solid var(--color-steel-gray); display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div style="font-size: 12px;">
                  <strong style="color: var(--color-rust-orange);">📄 ARQUIVO ATUAL:</strong>
                  <span class="mono-text" style="font-size: 11px; margin-left: 4px;">${window.EMCUtils.escapeHtml(notaExistente.caminho_arquivo_anexo.split('/').pop())}</span>
                </div>
                <button type="button" class="btn btn-secondary btn-sm" onclick="window.ComprasView.baixarDanfe(${notaId}, '${window.EMCUtils.escapeHtml(notaNumero)}')">BAIXAR ANEXO</button>
              </div>
              <small class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-bottom: 6px;">
                Para manter o anexo atual, deixe o campo abaixo vazio. Selecione um novo arquivo apenas se desejar substituí-lo.
              </small>
            ` : ''}
            <div style="display: flex; gap: 10px; align-items: center;">
              <input type="file" id="nota-arquivo-anexo" class="form-control" accept=".pdf,.xml,application/pdf,text/xml" style="flex: 1;">
            </div>
            <small class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-top: 4px;">
              Ao selecionar uma DANFE (PDF) ou XML da NF-e, os dados da nota são extraídos e o fornecedor é identificado automaticamente.
            </small>
          </div>

          <!-- DADOS PRINCIPAIS DA NOTA FISCAL -->
          <div style="display: grid; grid-template-columns: minmax(0, 1fr) 180px 160px; gap: 12px; margin-bottom: 12px;">
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; justify-content: space-between; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="nota-fornecedor" style="margin-bottom: 0;">Fornecedor *</label>
                <button type="button" class="btn btn-ghost btn-sm" id="btn-compras-novo-forn" style="padding: 0 6px; font-size: 11px; height: 22px; color: var(--color-rust-orange);" title="Cadastrar Novo Fornecedor">+ NOVO FORNECEDOR</button>
              </div>
              <select id="nota-fornecedor" class="form-control" required>${optionsForn}</select>
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="nota-numero" style="margin-bottom: 0; white-space: nowrap;">Nº Nota (NF-e/Recibo) *</label>
              </div>
              <input type="text" id="nota-numero" class="form-control mono-text" placeholder="EX: 123456" value="${window.EMCUtils.escapeHtml(notaNumero)}" required style="width: 100%;">
            </div>
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="nota-data" style="margin-bottom: 0; white-space: nowrap;">Data Emissão *</label>
              </div>
              <input type="date" id="nota-data" class="form-control mono-text" value="${notaData}" required style="width: 100%; box-sizing: border-box;">
            </div>
          </div>

          <div style="margin-bottom: 16px;">
            <div class="form-group" style="margin-bottom: 0;">
              <div style="display: flex; align-items: center; min-height: 22px; margin-bottom: 4px;">
                <label class="form-label" for="nota-chave" style="margin-bottom: 0;">Chave de Acesso (NF-e 44 Dígitos / NFS-e 50 Dígitos - Opcional)</label>
              </div>
              <input type="text" id="nota-chave" class="form-control mono-text" data-mask="chave-nfe" placeholder="0000 0000 0000 0000 0000 0000 0000 0000 0000 0000" value="${notaChave}" style="width: 100%;">
            </div>
          </div>

          <!-- Sub-Grid de Itens Comprados -->
          <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <h4 style="margin-bottom: 0;">ITENS COMPRADOS (RETROALIMENTAÇÃO DE CUSTOS)</h4>
              <button type="button" class="btn btn-ghost btn-sm" id="btn-compras-novo-item" style="padding: 0 6px; font-size: 11px; height: 22px; color: var(--color-rust-orange);" title="Cadastrar Novo Insumo">+ NOVO INSUMO</button>
            </div>
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
        const inputArquivo = document.getElementById('nota-arquivo-anexo');
        const arquivoAnexo = inputArquivo && inputArquivo.files && inputArquivo.files[0] ? inputArquivo.files[0] : null;

        // 1. Limpar bordas vermelhas anteriores
        const fornecedorSelect = document.getElementById('nota-fornecedor');
        const numNotaInput = document.getElementById('nota-numero');
        const dataInput = document.getElementById('nota-data');
        
        [fornecedorSelect, numNotaInput, dataInput].forEach(el => {
          if(el) el.style.border = '';
        });
        
        // Tratar borda do combobox se houver
        const fornecedorWrapper = fornecedorSelect ? fornecedorSelect.closest('.emc-combobox-wrapper') : null;
        const fornecedorTrigger = fornecedorWrapper ? fornecedorWrapper.querySelector('.emc-combobox-trigger') : null;
        if (fornecedorTrigger) fornecedorTrigger.style.border = '';

        let hasError = false;
        let firstErrorEl = null;

        // 2. Validar cada campo e aplicar borda vermelha se vazio
        if (!fornecedor_id) {
          hasError = true;
          if (fornecedorTrigger) {
            fornecedorTrigger.style.setProperty('border', '2px solid var(--color-error)', 'important');
            if (!firstErrorEl) firstErrorEl = fornecedorTrigger;
          } else if (fornecedorSelect) {
            fornecedorSelect.style.setProperty('border', '2px solid var(--color-error)', 'important');
            if (!firstErrorEl) firstErrorEl = fornecedorSelect;
          }
        }
        
        if (!num_nota) {
          hasError = true;
          if(numNotaInput) numNotaInput.style.setProperty('border', '2px solid var(--color-error)', 'important');
          if (!firstErrorEl) firstErrorEl = numNotaInput;
        }

        if (!data_compra) {
          hasError = true;
          if(dataInput) dataInput.style.setProperty('border', '2px solid var(--color-error)', 'important');
          if (!firstErrorEl) firstErrorEl = dataInput;
        }

        // 3. Foco no primeiro elemento com erro
        if (hasError) {
          window.EMCUtils.showToast('Por favor, preencha os campos destacados em vermelho.', 'error');
          if (firstErrorEl && typeof firstErrorEl.focus === 'function') {
            firstErrorEl.focus();
          }
          return false;
        }

        // 4. Auto-inclusão de item esquecido nos campos do sub-grid
        const subItemId = document.getElementById('sub-item-id') ? document.getElementById('sub-item-id').value : null;
        const subItemQtd = document.getElementById('sub-item-qtd') ? parseFloat(document.getElementById('sub-item-qtd').value) : 0;
        const subItemUnitText = document.getElementById('sub-item-unit') ? document.getElementById('sub-item-unit').value : 'R$ 0,00';
        const subItemUnit = window.EMCUtils.converterMoedaATMParaFloat(subItemUnitText);
        const btnAddItem = document.getElementById('btn-add-item-nota');
        
        if (subItemId && subItemQtd > 0 && subItemUnit > 0) {
          if (btnAddItem) {
            btnAddItem.click(); // Dispara o evento de adicionar item existente
          }
        }

        if (!this.itensTemp || !this.itensTemp.length) {
          window.EMCUtils.showToast('Adicione ao menos um item comprado na nota.', 'warning');
          return false;
        }

        // Validação prévia de tamanho no client-side para resposta instantânea
        if (arquivoAnexo && arquivoAnexo.size > 20 * 1024 * 1024) {
          window.EMCUtils.showToast('O arquivo da DANFE excede o limite máximo de 20MB.', 'error');
          return false;
        }

        try {
          const valorTotalCalculado = this.itensTemp.reduce((acc, it) => acc + (it.quantidade_comprada * it.valor_unitario), 0);

          const payload = {
            fornecedor_id,
            num_nota,
            data_compra,
            chave_acesso: chave_acesso || null,
            valor_total: valorTotalCalculado.toFixed(2),
            itens_comprados: this.itensTemp.map(it => ({
              item_id: it.item_id,
              quantidade_comprada: it.quantidade_comprada,
              valor_unitario: it.valor_unitario
            }))
          };

          let notaSalva = null;
          if (isEdit) {
            notaSalva = await window.api.put(`${window.CONFIG.ENDPOINTS.COMPRAS.NOTAS}${notaId}/`, payload);
          } else {
            notaSalva = await window.api.post(window.CONFIG.ENDPOINTS.COMPRAS.NOTAS, payload);
          }

          const targetId = isEdit ? notaId : (notaSalva ? notaSalva.id : null);

          // Se o usuário selecionou arquivo da DANFE / XML, realiza o upload seguro
          if (arquivoAnexo && targetId) {
            try {
              const formData = new FormData();
              formData.append('arquivo', arquivoAnexo);
              const endpointAnexo = window.CONFIG.ENDPOINTS.COMPRAS.ANEXAR_ARQUIVO.replace('{id}', targetId);
              await window.api.post(endpointAnexo, formData);
              window.EMCUtils.showToast(isEdit ? 'Nota fiscal e novo anexo atualizados com sucesso!' : 'Nota registrada e arquivo da DANFE anexado com sucesso!', 'success');
            } catch (errAnexo) {
              console.warn('Nota salva, mas erro ao enviar anexo:', errAnexo);
              window.EMCUtils.showToast('Nota salva, porém houve erro ao anexar a DANFE: ' + (errAnexo.message || 'formato ou cabeçalho inválido'), 'warning');
            }
          } else {
            window.EMCUtils.showToast(isEdit ? 'Nota fiscal atualizada e custos dos insumos recalculados com sucesso!' : 'Nota registrada e custos dos insumos atualizados com sucesso!', 'success');
          }

          this.carregarListaCompras();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || (isEdit ? 'Erro ao atualizar nota fiscal.' : 'Erro ao registrar nota fiscal.'), 'error');
          return false;
        }
      }
    });

    const selForn = document.getElementById('nota-fornecedor');
    const selItem = document.getElementById('sub-item-id');

    const dispararCadastroNovoFornecedor = (dadosPreenchimento = {}) => {
      window.CadastrosView.abrirModalCadastroCompleto(null, {
        tipoPredefinido: 'FORNECEDOR',
        dadosIniciais: dadosPreenchimento,
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

            // Re-aplica os dados da nota extraídos após salvar o fornecedor
            if (this.dadosExtraidosTemp) {
              aplicarDadosExtraidosNaNota(this.dadosExtraidosTemp);
            }

            window.EMCUtils.showToast(`Fornecedor "${novoForn.nome_razao}" selecionado automaticamente e dados da nota aplicados!`, 'success');
          } catch (e) {
            console.error('Erro ao atualizar fornecedores:', e);
          }
        }
      });
    };

    // Função utilitária para aplicar os dados extraídos nos campos da nota
    const aplicarDadosExtraidosNaNota = (dados) => {
      if (!dados) return;
      const inputNumero = document.getElementById('nota-numero');
      const inputData = document.getElementById('nota-data');
      const inputChave = document.getElementById('nota-chave');

      if (dados.num_nota && inputNumero) {
        inputNumero.value = dados.num_nota;
        inputNumero.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (dados.data_compra && inputData) {
        inputData.value = dados.data_compra;
        inputData.dispatchEvent(new Event('input', { bubbles: true }));
      }
      if (dados.chave_acesso && inputChave) {
        inputChave.value = window.EMCUtils.formatarChaveAcessoNfe ? window.EMCUtils.formatarChaveAcessoNfe(dados.chave_acesso) : dados.chave_acesso;
        inputChave.dispatchEvent(new Event('input', { bubbles: true }));
      }
    };

    // Função para selecionar um fornecedor na combobox (ou recarregar caso tenha acabado de habilitar)
    const selecionarFornecedorNaCombobox = async (fornecedorId) => {
      if (!selForn || !fornecedorId) return;

      // Recarrega opções para garantir que o parceiro apareça como fornecedor
      try {
        const fornecedoresAtualizados = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?tipo=FORNECEDOR`);
        const listaFornAtualizada = fornecedoresAtualizados.results || fornecedoresAtualizados || [];
        listaFornAtualizada.sort((a, b) => (a.nome_razao || '').localeCompare(b.nome_razao || ''));

        let novasOptions = '<option value="">SELECIONE O FORNECEDOR...</option>';
        listaFornAtualizada.forEach((f) => {
          novasOptions += `<option value="${f.id}" ${f.id == fornecedorId ? 'selected' : ''}>${window.EMCUtils.escapeHtml(f.nome_razao)}</option>`;
        });

        if (selForn._emcCombobox) {
          selForn._emcCombobox.updateOptions(novasOptions, fornecedorId);
        } else {
          selForn.innerHTML = novasOptions;
          selForn.value = fornecedorId;
        }
      } catch (err) {
        console.error('Erro ao selecionar fornecedor:', err);
      }
    };

    // Listener do campo de arquivo para análise prévia e cruzamento cadastral
    const inputArquivo = document.getElementById('nota-arquivo-anexo');
    const statusAnalise = document.getElementById('status-analise-doc');

    inputArquivo?.addEventListener('change', async (e) => {
      const arquivo = e.target.files && e.target.files[0];
      if (!arquivo) return;

      const ext = arquivo.name.split('.').pop().toLowerCase();
      if (ext !== 'pdf' && ext !== 'xml') {
        window.EMCUtils.showToast('Selecione um arquivo PDF (DANFE) ou XML da NF-e.', 'warning');
        return;
      }

      if (arquivo.size > 20 * 1024 * 1024) {
        window.EMCUtils.showToast('O arquivo excede o limite máximo de 20MB.', 'error');
        return;
      }

      if (statusAnalise) {
        statusAnalise.style.display = 'inline';
        statusAnalise.style.color = 'var(--color-rust-orange)';
        statusAnalise.textContent = 'ANALISANDO DOCUMENTO...';
      }

      try {
        const formData = new FormData();
        formData.append('arquivo', arquivo);

        const res = await window.api.post(window.CONFIG.ENDPOINTS.COMPRAS.ANALISAR_DOCUMENTO, formData);

        // Bloqueio de Documentos Não Fiscais (ex.: Boletos Bancários)
        if (res.is_documento_fiscal === false) {
          if (statusAnalise) {
            statusAnalise.style.color = 'var(--color-error)';
            statusAnalise.textContent = res.tipo_documento === 'BOLETO' ? 'BOLETO BANCÁRIO DETECTADO' : 'DOCUMENTO NÃO FISCAL';
          }
          inputArquivo.value = '';

          window.EMCUtils.openModal({
            title: res.tipo_documento === 'BOLETO' ? 'BOLETO BANCÁRIO DETECTADO (NÃO FISCAL)' : 'DOCUMENTO NÃO FISCAL DETECTADO',
            size: 'md',
            confirmText: 'ENTENDI',
            showCancel: false,
            content: `
              <div class="alert-banner alert-danger" style="margin-bottom: 16px;">
                <strong>DOCUMENTO DE COBRANÇA BANCÁRIA NÃO FISCAL</strong>
              </div>
              <p style="font-size: 14px; margin-bottom: 12px; line-height: 1.5; color: var(--color-on-surface);">
                ${window.EMCUtils.escapeHtml(res.message || 'O arquivo selecionado é um boleto de cobrança ou ficha de compensação bancária e não possui validade de nota fiscal para registro de entrada de insumos.')}
              </p>
              <div class="p-12" style="background: var(--color-surface-container-low); border: 1px solid var(--color-steel-gray); font-size: 12px; line-height: 1.6;">
                <strong style="color: var(--color-rust-orange);">COMO PROCEDER NO SISTEMA:</strong><br>
                • Para registrar este pagamento, utilize o módulo <strong>Financeiro (Contas a Pagar)</strong>.<br>
                • Para dar entrada fiscal e atualizar custos dos itens no estoque, anexe a respectiva <strong>Nota Fiscal (DANFE ou NFS-e)</strong> emitida pelo fornecedor.
              </div>
            `
          });
          return;
        }

        const dados = res.dados_extraidos || {};
        const parceiro = res.parceiro_existente;
        this.dadosExtraidosTemp = dados;

        if (statusAnalise) {
          statusAnalise.style.color = 'var(--color-success)';
          statusAnalise.textContent = 'DADOS EXTRAÍDOS COM SUCESSO';
        }

        // Caso 1: O parceiro já existe no banco de dados
        if (parceiro) {
          const parceiroTipoUpper = (parceiro.tipo || '').toUpperCase();

          if (parceiroTipoUpper === 'FORNECEDOR' || parceiroTipoUpper === 'AMBOS') {
            // Já é Fornecedor: auto-seleciona e preenche
            await selecionarFornecedorNaCombobox(parceiro.id);
            aplicarDadosExtraidosNaNota(dados);
            window.EMCUtils.showToast(`Fornecedor "${parceiro.nome_razao}" identificado e dados da nota preenchidos!`, 'success');
          } else {
            // É apenas Cliente: perguntar se deseja habilitar como Fornecedor
            window.EMCUtils.openModal({
              title: 'HABILITAR PARCEIRO COMO FORNECEDOR',
              size: 'md',
              confirmText: 'SIM, HABILITAR',
              cancelText: 'NÃO, CONTINUAR',
              content: `
                <p style="font-size: 14px; margin-bottom: 12px;">
                  O CNPJ <strong>${window.EMCUtils.formatarCpfCnpjDinamico(parceiro.cnpj_cpf)}</strong> pertence a <strong>${window.EMCUtils.escapeHtml(parceiro.nome_razao)}</strong>, atualmente cadastrado apenas como <strong>CLIENTE</strong>.
                </p>
                <div class="alert-banner alert-info" style="font-size: 12px; margin-bottom: 0;">
                  Deseja habilitar este parceiro também como <strong>FORNECEDOR</strong> (tipo: <em>Ambos</em>) para associá-lo a esta nota fiscal?
                </div>
              `,
              onConfirm: async () => {
                try {
                  const urlHabilitar = window.CONFIG.ENDPOINTS.CADASTROS.HABILITAR_FORNECEDOR.replace('{id}', parceiro.id);
                  await window.api.post(urlHabilitar);
                  await selecionarFornecedorNaCombobox(parceiro.id);
                  aplicarDadosExtraidosNaNota(dados);
                  window.EMCUtils.showToast(`"${parceiro.nome_razao}" agora é Cliente/Fornecedor e foi selecionado!`, 'success');
                  return true;
                } catch (errHab) {
                  window.EMCUtils.showToast(errHab.message || 'Erro ao habilitar fornecedor.', 'error');
                  return false;
                }
              },
              onCancel: () => {
                aplicarDadosExtraidosNaNota(dados);
                window.EMCUtils.showToast('Arquivo mantido. Selecione o fornecedor manualmente ou continue a edição.', 'info');
              }
            });
          }
        } else {
          // Caso 2: CNPJ não cadastrado no sistema
          const cnpjFormatado = dados.cnpj_emitente ? window.EMCUtils.formatarCpfCnpjDinamico(dados.cnpj_emitente) : 'não identificado';
          const razaoSocial = dados.razao_social_emitente || 'RAZÃO SOCIAL NÃO IDENTIFICADA';
          const nomeFantasia = dados.nome_fantasia_emitente || '';
          const localidade = dados.cidade_uf || '';

          window.EMCUtils.openModal({
            title: 'FORNECEDOR NÃO ENCONTRADO',
            size: 'md',
            confirmText: 'CADASTRAR FORNECEDOR',
            cancelText: 'DEIXAR PARA DEPOIS',
            content: `
              <p style="font-size: 13px; margin-bottom: 12px; color: var(--color-on-surface);">
                O documento fiscal foi identificado com sucesso, porém o fornecedor emissor ainda não está cadastrado na base de parceiros:
              </p>
              
              <div class="fornecedor-preview-card mb-16" style="background: var(--color-surface-container-high); border: 1px solid var(--color-steel-gray); border-left: 4px solid var(--color-rust-orange); padding: 14px 16px;">
                <div class="mono-text" style="font-size: 11px; color: var(--color-brushed-metal); letter-spacing: 0.05em; margin-bottom: 6px;">
                  DADOS DO FORNECEDOR IDENTIFICADO:
                </div>
                <div style="font-size: 15px; font-weight: 700; color: var(--color-on-surface); margin-bottom: 4px;">
                  ${window.EMCUtils.escapeHtml(razaoSocial)}
                </div>
                ${nomeFantasia ? `
                  <div style="font-size: 12px; color: var(--color-rust-orange); margin-bottom: 6px;">
                    Nome Fantasia: <strong>${window.EMCUtils.escapeHtml(nomeFantasia)}</strong>
                  </div>
                ` : ''}
                <div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 12px; margin-top: 6px; color: var(--color-on-surface-variant);" class="mono-text">
                  <span>CNPJ: <strong>${cnpjFormatado}</strong></span>
                  ${localidade ? `<span>Localidade: <strong>${window.EMCUtils.escapeHtml(localidade)}</strong></span>` : ''}
                </div>
              </div>

              <div class="alert-banner alert-warning" style="font-size: 12px; margin-bottom: 0;">
                Deseja abrir o cadastro rápido agora? O formulário será pré-preenchido com os dados obtidos da Receita Federal para sua conferência e confirmação.
              </div>
            `,
            onConfirm: () => {
              aplicarDadosExtraidosNaNota(dados);
              dispararCadastroNovoFornecedor({
                cnpj_cpf: dados.cnpj_emitente || '',
                nome_razao: razaoSocial,
                nome_fantasia: nomeFantasia,
                tipo_pessoa: 'PJ',
                tipo: 'Fornecedor'
              });
              return true;
            },
            onCancel: () => {
              aplicarDadosExtraidosNaNota(dados);
              window.EMCUtils.showToast('Arquivo mantido. Você pode prosseguir com o lançamento manual.', 'info');
            }
          });
        }
      } catch (errAnalise) {
        console.warn('Erro ao analisar documento fiscal:', errAnalise);
        if (statusAnalise) {
          statusAnalise.style.color = 'var(--color-error)';
          statusAnalise.textContent = 'ERRO NA ANÁLISE';
        }
        window.EMCUtils.showToast(errAnalise.message || 'Não foi possível extrair dados automaticamente deste arquivo. Preencha os campos manualmente.', 'warning');
      }
    });

    if (selForn) {
      window.EMCUtils.initSearchableSelect(selForn, {
        placeholder: 'SELECIONE OU PESQUISE O FORNECEDOR...',
        action: {
          label: '+ CADASTRAR NOVO FORNECEDOR',
          onClick: () => dispararCadastroNovoFornecedor()
        }
      });
    }

    const dispararCadastroNovoInsumo = async () => {
      try {
        const uomEndpoint = (window.CONFIG.ENDPOINTS.CATALOGO && window.CONFIG.ENDPOINTS.CATALOGO.UOM) ||
                            (window.CONFIG.ENDPOINTS.CADASTROS && window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM) ||
                            '/dicionario-uom/';
        const resUom = await window.api.get(uomEndpoint).catch(() => []);
        let uoms = resUom.results || resUom || [];
        if (!Array.isArray(uoms) || !uoms.length) {
          uoms = [
            { id: 1, sigla: 'UN', descricao: 'UNIDADE' },
            { id: 2, sigla: 'KG', descricao: 'QUILOGRAMA' },
            { id: 3, sigla: 'M', descricao: 'METRO' },
            { id: 4, sigla: 'M2', descricao: 'METRO QUADRADO' },
            { id: 5, sigla: 'BARRA', descricao: 'BARRA DE 6 METROS' }
          ];
        }
        uoms.sort((a, b) => (a.sigla || '').localeCompare(b.sigla || ''));

        let optionsUom = '';
        uoms.forEach((u) => {
          const isUn = (u.sigla || '').toUpperCase() === 'UN';
          optionsUom += `<option value="${u.id}" ${isUn ? 'selected' : ''}>${window.EMCUtils.escapeHtml(u.sigla)} - ${window.EMCUtils.escapeHtml(u.descricao)}</option>`;
        });

        window.EMCUtils.openModal({
          title: 'NOVO INSUMO / ITEM (CADASTRO RÁPIDO)',
          size: 'md',
          confirmText: 'CADASTRAR E SELECIONAR',
          content: `
            <form id="form-novo-insumo-rapido">
              <div class="form-group mb-12">
                <label class="form-label" for="novo-item-nome">Nome do Insumo *</label>
                <input type="text" id="novo-item-nome" class="form-control" placeholder="EX: ARAME DE SOLDA TUBULAR 1.2MM" required autofocus>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label" for="novo-item-uom-compra">Unidade de Compra (NF-e) *</label>
                  <select id="novo-item-uom-compra" class="form-control">${optionsUom}</select>
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label" for="novo-item-uom-consumo">Unidade de Consumo (Oficina) *</label>
                  <select id="novo-item-uom-consumo" class="form-control">${optionsUom}</select>
                </div>
              </div>

              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px;">
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label" for="novo-item-fator">Fator de Conversão</label>
                  <input type="text" id="novo-item-fator" class="form-control mono-text" value="1,0000" placeholder="1,0000">
                </div>
                <div class="form-group" style="margin-bottom: 0;">
                  <label class="form-label" for="novo-item-tipo-uso">Tipo de Uso *</label>
                  <select id="novo-item-tipo-uso" class="form-control">
                    <option value="INSUMO_PRODUTIVO" selected>INSUMO PRODUTIVO</option>
                    <option value="MATERIAL_CONSUMO">MATERIAL DE CONSUMO</option>
                    <option value="EPI">EPI</option>
                    <option value="FERRAMENTAL">FERRAMENTAL</option>
                  </select>
                </div>
              </div>
            </form>
          `,
          onConfirm: async () => {
            const nome = document.getElementById('novo-item-nome')?.value.trim();
            const uomCompra = parseInt(document.getElementById('novo-item-uom-compra')?.value) || null;
            const uomConsumo = parseInt(document.getElementById('novo-item-uom-consumo')?.value) || uomCompra;
            const fatorStr = document.getElementById('novo-item-fator')?.value.replace(',', '.').trim() || '1.0';
            const fator = parseFloat(fatorStr) || 1.0;
            const tipoUso = document.getElementById('novo-item-tipo-uso')?.value || 'INSUMO_PRODUTIVO';

            if (!nome) {
              window.EMCUtils.showToast('Informe o nome do insumo.', 'warning');
              return false;
            }

            if (!uomCompra) {
              window.EMCUtils.showToast('Selecione a unidade de medida.', 'warning');
              return false;
            }

            try {
              const payloadItem = {
                nome: window.EMCUtils.sanitizarTextoEmTempoReal(nome),
                unidade_compra: uomCompra,
                unidade_consumo: uomConsumo,
                fator_conversao: fator,
                tipo_uso: tipoUso,
                ultimo_custo_compra: '0.00'
              };

              const novoItem = await window.api.post(window.CONFIG.ENDPOINTS.CATALOGO.ITENS, payloadItem);

              // Recarrega itens do catálogo
              const itensAtualizados = await window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.ITENS);
              const listaItensAtualizada = itensAtualizados.results || itensAtualizados || [];
              listaItensAtualizada.sort((a, b) => (a.nome || '').localeCompare(b.nome || ''));

              let novasOptionsItens = '<option value="">SELECIONE UM INSUMO...</option>';
              listaItensAtualizada.forEach((it) => {
                const uom = it.unidade_compra_sigla || 'UN';
                novasOptionsItens += `<option value="${it.id}" ${it.id === novoItem.id ? 'selected' : ''}>${window.EMCUtils.escapeHtml(it.nome)} (${uom})</option>`;
              });

              if (selItem) {
                if (selItem._emcCombobox) {
                  selItem._emcCombobox.updateOptions(novasOptionsItens, novoItem.id);
                } else {
                  selItem.innerHTML = novasOptionsItens;
                  selItem.value = novoItem.id;
                }
              }

              // Posiciona o foco no campo de quantidade para agilizar o lançamento
              setTimeout(() => {
                const qtdInput = document.getElementById('sub-item-qtd');
                if (qtdInput) {
                  qtdInput.focus();
                  qtdInput.select();
                }
              }, 100);

              window.EMCUtils.showToast(`Insumo "${novoItem.nome}" cadastrado e selecionado!`, 'success');
              return true;
            } catch (errItem) {
              window.EMCUtils.showToast(errItem.message || 'Erro ao cadastrar insumo.', 'error');
              return false;
            }
          }
        });
      } catch (err) {
        console.error('Erro ao abrir modal de cadastro de insumo:', err);
        window.EMCUtils.showToast('Erro ao carregar unidades de medida.', 'error');
      }
    };

    if (selItem) {
      window.EMCUtils.initSearchableSelect(selItem, {
        placeholder: 'PESQUISE UM INSUMO...',
        action: {
          label: '+ CADASTRAR NOVO INSUMO',
          onClick: () => dispararCadastroNovoInsumo()
        }
      });
    }

    document.getElementById('btn-compras-novo-forn')?.addEventListener('click', (e) => {
      e.preventDefault();
      dispararCadastroNovoFornecedor();
    });

    document.getElementById('btn-compras-novo-item')?.addEventListener('click', (e) => {
      e.preventDefault();
      dispararCadastroNovoInsumo();
    });

    // Atualiza a grid de itens com itens existentes (no caso de edição) ou vazia
    this.atualizarGridItensNota();
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
    } catch (err) {
      console.error('Erro ao abrir modal de compras:', err);
      window.EMCUtils.showToast(err.message || 'Erro ao carregar dados do formulário de compras.', 'error');
    }
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

          <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
              ${nota.caminho_arquivo_anexo 
                ? `<button type="button" class="btn btn-secondary btn-sm" onclick="window.ComprasView.baixarDanfe(${nota.id}, '${window.EMCUtils.escapeHtml(nota.num_nota)}')">📄 BAIXAR ANEXO (DANFE / XML)</button>` 
                : '<span class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">Nenhum anexo importado.</span>'}
              <button type="button" class="btn btn-secondary btn-sm" onclick="window.EMCUtils.closeModal(); window.ComprasView.abrirModalCompra(${nota.id});">EDITAR NOTA</button>
              <button type="button" class="btn btn-danger btn-sm" onclick="window.EMCUtils.closeModal(); window.ComprasView.confirmarCancelamentoNota(${nota.id}, '${window.EMCUtils.escapeHtml(nota.num_nota)}', '${window.EMCUtils.escapeHtml(nota.fornecedor_nome || 'Fornecedor')}', '${window.EMCUtils.formatarMoeda(nota.valor_total)}');">CANCELAR NOTA</button>
            </div>
            <div class="text-right">
              <span class="mono-text" style="font-size: 16px; color: var(--color-rust-orange); font-weight: 700;">
                TOTAL: ${window.EMCUtils.formatarMoeda(nota.valor_total)}
              </span>
            </div>
          </div>
        `
      });
    } catch (e) {
      window.EMCUtils.showToast('Erro ao carregar detalhes da nota.', 'error');
    }
  },

  async baixarDanfe(notaId, numNota) {
    try {
      window.EMCUtils.showToast('Iniciando download seguro do anexo...', 'info');
      const endpoint = window.CONFIG.ENDPOINTS.COMPRAS.DOWNLOAD_ANEXO.replace('{id}', notaId);
      const filenamePadrao = `DANFE_NF_${numNota || notaId}.pdf`;
      await window.api.downloadFile(endpoint, filenamePadrao);
    } catch (err) {
      console.error('Erro ao baixar anexo:', err);
      window.EMCUtils.showToast(err.message || 'Erro ao realizar download do anexo da compra.', 'error');
    }
  },

  confirmarCancelamentoNota(notaId, numNota, fornecedorNome, valorTotal) {
    window.EMCUtils.openModal({
      title: 'CANCELAR NOTA FISCAL DE ENTRADA',
      size: 'md',
      confirmText: 'SIM, CANCELAR COMPRA',
      cancelText: 'VOLTAR',
      content: `
        <div class="alert-banner alert-danger mb-16">
          <strong>CONFIRMAÇÃO DE CANCELAMENTO (SOFT DELETE)</strong>
        </div>
        <p style="font-size: 14px; margin-bottom: 12px; line-height: 1.5; color: var(--color-on-surface);">
          Deseja realmente cancelar a <strong>Nota Fiscal #${window.EMCUtils.escapeHtml(numNota)}</strong> do fornecedor <strong>${window.EMCUtils.escapeHtml(fornecedorNome)}</strong> no valor de <strong>${valorTotal}</strong>?
        </p>
        <div class="p-12 mb-16" style="background: var(--color-surface-container-low); border: 1px solid var(--color-steel-gray); font-size: 12px; line-height: 1.6;">
          <strong style="color: var(--color-rust-orange);">IMPACTO DO CANCELAMENTO:</strong><br>
          • A nota fiscal será inativada e poderá ser auditada ou restaurada na Lixeira.<br>
          • O custo de compra de todos os insumos desta nota será <strong>recalculado automaticamente</strong> no Catálogo para a compra ativa anterior válida.
        </div>
      `,
      onConfirm: async () => {
        try {
          await window.api.delete(`${window.CONFIG.ENDPOINTS.COMPRAS.NOTAS}${notaId}/`);
          window.EMCUtils.showToast(`Nota Fiscal #${numNota} cancelada e custos recalculados!`, 'success');
          this.carregarListaCompras();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao cancelar nota fiscal.', 'error');
          return false;
        }
      }
    });
  }
};
