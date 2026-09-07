/**
 * EMC Soldas - View de Cadastros Básicos (Clientes, Fornecedores, Equipamentos, UOM, Atributos)
 */

window.CadastrosView = {
  currentTab: 'clientes',

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CLIENTES & EQUIPAMENTOS</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">GESTÃO OPERACIONAL DE CLIENTES, FORNECEDORES, VEÍCULOS E FROTAS</p>
        </div>
      </div>

      <!-- Navegação por Abas -->
      <div class="tabs-nav">
        <button class="tab-btn ${this.currentTab === 'clientes' ? 'active' : ''}" id="tab-btn-clientes">
          CLIENTES & FORNECEDORES
        </button>
        <button class="tab-btn ${this.currentTab === 'equipamentos' ? 'active' : ''}" id="tab-btn-equipamentos">
          EQUIPAMENTOS & VEÍCULOS
        </button>
      </div>

      <!-- Container do Conteúdo da Aba Ativa -->
      <div id="cadastros-tab-content"></div>
    `;

    document.getElementById('tab-btn-clientes')?.addEventListener('click', () => {
      this.currentTab = 'clientes';
      this.render(container);
    });
    document.getElementById('tab-btn-equipamentos')?.addEventListener('click', () => {
      this.currentTab = 'equipamentos';
      this.render(container);
    });

    const content = document.getElementById('cadastros-tab-content');
    if (this.currentTab === 'clientes') {
      this.renderClientes(content);
    } else if (this.currentTab === 'equipamentos') {
      this.renderEquipamentos(content);
    }
  },

  // ==========================================================================
  // 1. CLIENTES E FORNECEDORES
  // ==========================================================================
  async renderClientes(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; gap: 10px; align-items: center; flex-wrap: wrap; width: 100%;">
          <input type="text" id="filtro-cliente-busca" class="form-control" placeholder="BUSCAR POR NOME, CNPJ/CPF OU CIDADE..." style="flex: 1; min-width: 200px;">
          <select id="filtro-cliente-tipo" class="form-control" style="width: 175px; min-width: 175px; flex-shrink: 0;">
            <option value="">TODOS</option>
            <option value="CLIENTE">CLIENTES</option>
            <option value="FORNECEDOR">FORNECEDORES</option>
          </select>
          <div style="display: flex; gap: 10px; flex-shrink: 0;">
            <button class="btn btn-secondary" id="btn-novo-cliente-rapido" style="white-space: nowrap;">+ CADASTRO RÁPIDO</button>
            <button class="btn btn-primary" id="btn-novo-cliente-completo" style="white-space: nowrap;">+ NOVO CADASTRO</button>
          </div>
        </div>
      </div>

      <div class="table-container">
        <table class="table" id="tabela-clientes">
          <thead>
            <tr>
              <th>ID</th>
              <th>TIPO</th>
              <th>NOME / RAZÃO SOCIAL</th>
              <th>CPF / CNPJ</th>
              <th>TELEFONE</th>
              <th>CIDADE / UF</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-clientes-tbody">
            <tr><td colspan="7" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-novo-cliente-rapido')?.addEventListener('click', () => this.abrirModalCadastroRapido());
    document.getElementById('btn-novo-cliente-completo')?.addEventListener('click', () => this.abrirModalCadastroCompleto());
    document.getElementById('filtro-cliente-busca')?.addEventListener('input', () => this.carregarListaClientes());
    document.getElementById('filtro-cliente-tipo')?.addEventListener('change', () => this.carregarListaClientes());

    await this.carregarListaClientes();
  },

  async carregarListaClientes() {
    const tbody = document.getElementById('lista-clientes-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-cliente-busca')?.value.trim() || '';
    const tipo = document.getElementById('filtro-cliente-tipo')?.value || '';

    try {
      const query = new URLSearchParams();
      if (busca) query.append('search', busca);
      if (tipo) query.append('tipo', tipo);

      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?${query.toString()}`);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum registro encontrado.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((item) => {
        const itemTipoUpper = (item.tipo || '').toUpperCase();
        const badgeTipo = itemTipoUpper === 'CLIENTE' ? 'info' : (itemTipoUpper === 'FORNECEDOR' ? 'warning' : 'success');
        
        let telDisplay = '-';
        if (item.contatos && item.contatos.length > 0) {
          const c1 = item.contatos[0];
          const wa = c1.is_whatsapp ? ' <span class="status-chip success" style="font-size: 10px; padding: 2px 4px; font-weight: 700;">WHATSAPP</span>' : '';
          const extra = item.contatos.length > 1 ? ` <span class="mono-text" style="font-size: 11px; color: var(--color-rust-orange); font-weight: 700;">(+${item.contatos.length - 1})</span>` : '';
          telDisplay = `<div class="mono-text" style="font-size: 12px;"><span>${window.EMCUtils.escapeHtml(c1.nome_contato)}:</span> <strong>${window.EMCUtils.formatarTelefoneDinamico(c1.telefone)}</strong>${wa}${extra}</div>`;
        } else if (item.telefone) {
          telDisplay = window.EMCUtils.formatarTelefoneDinamico(item.telefone);
        }

        const qtdEquip = item.quantidade_equipamentos_ativos || 0;
        const btnFrota = itemTipoUpper !== 'FORNECEDOR' 
          ? `<button class="btn btn-secondary btn-sm" onclick="window.CadastrosView.abrirModalFrotaCliente(${item.id})">FROTA (${qtdEquip})</button>` 
          : '';

        html += `
          <tr>
            <td class="mono-text">#${item.id}</td>
            <td><span class="status-chip ${badgeTipo}">${item.tipo}</span></td>
            <td><strong>${window.EMCUtils.escapeHtml(item.nome_razao)}</strong></td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(item.cnpj_cpf ? window.EMCUtils.formatarCpfCnpjDinamico(item.cnpj_cpf) : '-')}</td>
            <td>${telDisplay}</td>
            <td>${window.EMCUtils.escapeHtml(item.cidade || '-')}${item.uf ? ' / ' + item.uf : ''}</td>
            <td style="text-align: right; white-space: nowrap;">
              ${btnFrota}
              <button class="btn btn-ghost btn-sm" onclick="window.CadastrosView.editarCliente(${item.id})">EDITAR</button>
              <button class="btn btn-ghost btn-sm" style="color: var(--color-error);" onclick="window.CadastrosView.excluirCliente(${item.id}, '${window.EMCUtils.escapeHtml(item.nome_razao)}')">EXCLUIR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalFrotaCliente(clienteId) {
    try {
      const cliente = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}${clienteId}/`);
      const vinculosRes = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTE_EQUIPAMENTOS}?cliente=${clienteId}&is_ativo=true`);
      const vinculos = vinculosRes.results || vinculosRes || [];

      let linhasHtml = '';
      if (!vinculos.length) {
        linhasHtml = '<tr><td colspan="4" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 18px;">Nenhum equipamento ou veículo vinculado a este cliente.</td></tr>';
      } else {
        vinculos.forEach((v) => {
          const eq = v.equipamento_detalhes || {};
          linhasHtml += `
            <tr>
              <td class="mono-text"><strong>${window.EMCUtils.escapeHtml(eq.placa ? window.EMCUtils.formatarPlacaVeiculo(eq.placa) : '-')}</strong></td>
              <td class="mono-text">${window.EMCUtils.escapeHtml(eq.identificacao || '-')}</td>
              <td>${window.EMCUtils.escapeHtml(eq.descricao || '-')}</td>
              <td style="text-align: right; white-space: nowrap;">
                <button type="button" class="btn btn-secondary btn-sm" onclick="window.CadastrosView.abrirModalHistoricoEquipamento(${eq.id})">HISTÓRICO</button>
                <button type="button" class="btn btn-ghost btn-sm" onclick="window.CadastrosView.desvincularEquipamento(${v.id}, ${clienteId})">DESVINCULAR</button>
              </td>
            </tr>
          `;
        });
      }

      window.EMCUtils.openModal({
        title: `FROTA DE VEÍCULOS / EQUIPAMENTOS - ${cliente.nome_razao}`,
        size: 'lg',
        showCancel: false,
        confirmText: 'FECHAR',
        content: `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; flex-wrap: wrap; gap: 8px;">
            <div>
              <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">
                Total de equipamentos ativos vinculados: <strong>${vinculos.length}</strong>
              </p>
            </div>
            <button type="button" class="btn btn-primary btn-sm" id="btn-novo-equip-cliente">+ VINCULAR / CADASTRAR EQUIPAMENTO</button>
          </div>

          <div class="table-container" style="margin-bottom: 0;">
            <table class="table" style="font-size: 13px;">
              <thead>
                <tr>
                  <th>PLACA</th>
                  <th>IDENTIFICAÇÃO</th>
                  <th>DESCRIÇÃO DO EQUIPAMENTO</th>
                  <th style="text-align: right;">AÇÃO</th>
                </tr>
              </thead>
              <tbody>
                ${linhasHtml}
              </tbody>
            </table>
          </div>
        `
      });

      document.getElementById('btn-novo-equip-cliente')?.addEventListener('click', () => {
        this.abrirModalVincularOuCriarEquipamentoFrota(clienteId);
      });
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar frota do cliente.', 'error');
    }
  },

  async abrirModalVincularOuCriarEquipamentoFrota(clienteId) {
    try {
      const cliente = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}${clienteId}/`);
      const equipsRes = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}?page_size=1000`);
      const todosEquips = equipsRes.results || equipsRes || [];

      let optionsEquip = '<option value="__NOVO__">+ CADASTRAR NOVO EQUIPAMENTO PARA ESTE CLIENTE</option>';
      todosEquips.forEach((e) => {
        const placa = e.placa ? ` [${window.EMCUtils.formatarPlacaVeiculo(e.placa)}]` : '';
        const ident = e.identificacao ? ` - ${e.identificacao}` : '';
        const dono = e.cliente_atual_nome ? ` (Vinculado a: ${e.cliente_atual_nome})` : ' (Sem dono / Disponível)';
        optionsEquip += `<option value="${e.id}">${window.EMCUtils.escapeHtml(e.descricao)}${placa}${ident}${dono}</option>`;
      });

      window.EMCUtils.openModal({
        title: `VINCULAR OU CADASTRAR EQUIPAMENTO - ${cliente.nome_razao}`,
        size: 'md',
        confirmText: 'VINCULAR / SALVAR',
        content: `
          <form id="form-frota-equip">
            <div class="form-group">
              <label class="form-label" for="frota-sel-equip-busca">Pesquisar Equipamento Existente ou Criar Novo</label>
              <select id="frota-sel-equip-busca" class="form-control">
                ${optionsEquip}
              </select>
              <small class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-top: 4px;">
                Selecione um equipamento existente para vincular/transferir ou escolha cadastrar um novo.
              </small>
            </div>

            <div id="frota-aviso-transferencia" class="alert-banner alert-warning mb-16" style="display: none;"></div>

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
              <div class="form-group">
                <label class="form-label" for="frota-equip-placa">Placa (Antiga / Mercosul)</label>
                <input type="text" id="frota-equip-placa" class="form-control mono-text" data-mask="placa" placeholder="ABC-1234 ou ABC-1D23">
              </div>
              <div class="form-group">
                <label class="form-label" for="frota-equip-identificacao">Identificação / Chassi / Frota</label>
                <input type="text" id="frota-equip-identificacao" class="form-control mono-text" placeholder="EX: TRATOR 04">
              </div>
            </div>

            <div class="form-group">
              <label class="form-label" for="frota-equip-descricao">Descrição Completa *</label>
              <input type="text" id="frota-equip-descricao" class="form-control" placeholder="EX: ESCAVADEIRA HIDRÁULICA CAT 320D" required>
            </div>
          </form>
        `,
        onConfirm: async () => {
          const selVal = document.getElementById('frota-sel-equip-busca').value;
          const placa = document.getElementById('frota-equip-placa').value.trim();
          const identificacao = document.getElementById('frota-equip-identificacao').value.trim();
          const descricao = document.getElementById('frota-equip-descricao').value.trim();

          if (selVal === '__NOVO__') {
            if (!descricao) {
              window.EMCUtils.showToast('A descrição do equipamento é obrigatória.', 'error');
              return false;
            }

            if (placa && !window.EMCUtils.validarPlacaVeiculo(placa)) {
              window.EMCUtils.showToast('Placa inválida. O formato deve ser Padrão Antigo (ex: ABC-1234) ou Mercosul (ex: ABC-1D23).', 'error');
              return false;
            }

            try {
              await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS, {
                placa: window.EMCUtils.sanitizarTextoEmTempoReal(placa),
                identificacao: window.EMCUtils.sanitizarTextoEmTempoReal(identificacao),
                descricao,
                cliente_id: clienteId
              });
              window.EMCUtils.showToast('Equipamento criado e vinculado com sucesso!', 'success');
              this.abrirModalFrotaCliente(clienteId);
              this.carregarListaClientes();
              return true;
            } catch (err) {
              window.EMCUtils.showToast(err.message || 'Erro ao criar equipamento.', 'error');
              return false;
            }
          } else {
            // Equipamento existente selecionado
            const equipId = parseInt(selVal, 10);
            const equipObj = todosEquips.find(e => e.id === equipId);

            if (equipObj && equipObj.cliente_atual && equipObj.cliente_atual.id === clienteId) {
              window.EMCUtils.showToast('Este equipamento já está vinculado a este cliente.', 'info');
              return true;
            }

            if (equipObj && equipObj.cliente_atual && equipObj.cliente_atual.id !== clienteId) {
              const donoAntigo = equipObj.cliente_atual_nome || 'outro cliente';
              const confirma = confirm(`Este equipamento pertence atualmente a '${donoAntigo}'. Deseja transferir a titularidade e vinculá-lo a '${cliente.nome_razao}'?`);
              if (!confirma) return false;

              try {
                await window.api.post(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${equipId}/transferir/`, {
                  novo_cliente_id: clienteId
                });
                window.EMCUtils.showToast('Titularidade do equipamento transferida com sucesso!', 'success');
                this.abrirModalFrotaCliente(clienteId);
                this.carregarListaClientes();
                return true;
              } catch (err) {
                window.EMCUtils.showToast(err.message || 'Erro ao transferir equipamento.', 'error');
                return false;
              }
            } else {
              // Equipamento sem dono
              try {
                await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.CLIENTE_EQUIPAMENTOS, {
                  cliente: clienteId,
                  equipamento: equipId,
                  is_ativo: true
                });
                window.EMCUtils.showToast('Equipamento vinculado com sucesso!', 'success');
                this.abrirModalFrotaCliente(clienteId);
                this.carregarListaClientes();
                return true;
              } catch (err) {
                window.EMCUtils.showToast(err.message || 'Erro ao vincular equipamento.', 'error');
                return false;
              }
            }
          }
        }
      });

      // Inicializa combobox pesquisável e listeners de autopreenchimento
      setTimeout(() => {
        const selEquip = document.getElementById('frota-sel-equip-busca');
        const inputPlaca = document.getElementById('frota-equip-placa');
        const inputIdent = document.getElementById('frota-equip-identificacao');
        const inputDesc = document.getElementById('frota-equip-descricao');
        const avisoTransf = document.getElementById('frota-aviso-transferencia');

        if (selEquip) {
          window.EMCUtils.initSearchableSelect(selEquip, {
            placeholder: 'DIGITE PLACA, IDENTIFICAÇÃO OU DESCRIÇÃO...'
          });

          selEquip.addEventListener('change', (e) => {
            const val = e.target.value;
            if (val === '__NOVO__') {
              if (inputPlaca) { inputPlaca.value = ''; inputPlaca.readOnly = false; }
              if (inputIdent) { inputIdent.value = ''; inputIdent.readOnly = false; }
              if (inputDesc) { inputDesc.value = ''; inputDesc.readOnly = false; }
              if (avisoTransf) avisoTransf.style.display = 'none';
            } else {
              const eq = todosEquips.find(x => x.id === parseInt(val, 10));
              if (eq) {
                if (inputPlaca) { inputPlaca.value = eq.placa ? window.EMCUtils.formatarPlacaVeiculo(eq.placa) : ''; inputPlaca.readOnly = true; }
                if (inputIdent) { inputIdent.value = eq.identificacao || ''; inputIdent.readOnly = true; }
                if (inputDesc) { inputDesc.value = eq.descricao || ''; inputDesc.readOnly = true; }

                if (eq.cliente_atual && eq.cliente_atual.id !== clienteId && avisoTransf) {
                  avisoTransf.style.display = 'block';
                  avisoTransf.innerHTML = `<strong>[AVISO DE TRANSFERÊNCIA]</strong> Este equipamento está atualmente vinculado a <strong>${window.EMCUtils.escapeHtml(eq.cliente_atual_nome)}</strong>. Ao salvar, a titularidade será transferida para este cliente com registro de data/hora no histórico.`;
                } else if (avisoTransf) {
                  avisoTransf.style.display = 'none';
                }
              }
            }
          });
        }
      }, 50);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados para vinculação.', 'error');
    }
  },

  async abrirModalHistoricoEquipamento(equipId) {
    try {
      const equip = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${equipId}/`);
      const historicoRes = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${equipId}/historico-proprietarios/`);
      const historico = historicoRes.results || historicoRes || [];

      let linhasHtml = '';
      if (!historico.length) {
        linhasHtml = '<tr><td colspan="5" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 18px;">Nenhum registro de titularidade encontrado no histórico.</td></tr>';
      } else {
        historico.forEach((h) => {
          const statusBadge = h.is_ativo 
            ? '<span class="status-chip success">PROPRIETÁRIO ATUAL</span>' 
            : '<span class="status-chip neutral">PROPRIETÁRIO ANTERIOR</span>';

          const doc = h.cnpj_cpf ? ` (${window.EMCUtils.formatarCpfCnpjDinamico(h.cnpj_cpf)})` : '';
          const tel = h.telefone ? window.EMCUtils.formatarTelefoneDinamico(h.telefone) : '-';
          const dataFormatada = window.EMCUtils.formatarDataHoraPtBr(h.data_vinculo);

          linhasHtml += `
            <tr>
              <td>${statusBadge}</td>
              <td><strong>${window.EMCUtils.escapeHtml(h.nome_razao)}</strong>${doc}</td>
              <td class="mono-text">${tel}</td>
              <td class="mono-text" style="font-weight: 700; color: var(--color-rust-orange);">${dataFormatada}</td>
              <td class="mono-text">#${h.vinculo_id}</td>
            </tr>
          `;
        });
      }

      const placaTexto = equip.placa ? ` [${window.EMCUtils.formatarPlacaVeiculo(equip.placa)}]` : '';

      window.EMCUtils.openModal({
        title: `HISTÓRICO DE TITULARIDADE E VÍNCULOS - #${equip.id} ${equip.descricao}${placaTexto}`,
        size: 'lg',
        showCancel: false,
        confirmText: 'FECHAR',
        content: `
          <div style="margin-bottom: 14px;">
            <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant);">
              Rastreabilidade cronológica de todas as transferências de propriedade com data e hora de registro.
            </p>
          </div>

          <div class="table-container" style="margin-bottom: 0;">
            <table class="table" style="font-size: 13px;">
              <thead>
                <tr>
                  <th>STATUS</th>
                  <th>CLIENTE / PROPRIETÁRIO</th>
                  <th>TELEFONE</th>
                  <th>DATA E HORA DO VÍNCULO (TIMESTAMP)</th>
                  <th>ID VÍNCULO</th>
                </tr>
              </thead>
              <tbody>
                ${linhasHtml}
              </tbody>
            </table>
          </div>
        `
      });
    } catch (err) {
      console.error('Erro ao carregar histórico de proprietários:', err);
      window.EMCUtils.showToast(err.message || 'Erro ao carregar histórico de proprietários.', 'error');
    }
  },

  async desvincularEquipamento(vinculoId, clienteId) {
    if (!confirm('Deseja realmente desvincular este equipamento do cliente?')) return;

    try {
      await window.api.delete(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTE_EQUIPAMENTOS}${vinculoId}/`);
      window.EMCUtils.showToast('Equipamento desvinculado com sucesso!', 'success');
      this.abrirModalFrotaCliente(clienteId);
      this.carregarListaClientes();
    } catch (err) {
      window.EMCUtils.showToast(err.message || 'Erro ao desvincular equipamento.', 'error');
    }
  },

  abrirModalCadastroRapido() {
    window.EMCUtils.openModal({
      title: 'CADASTRO RÁPIDO DE CLIENTE (ÁGIL)',
      size: 'sm',
      confirmText: 'SALVAR CLIENTE',
      content: `
        <form id="form-cliente-rapido">
          <p class="mono-text" style="font-size: 12px; color: var(--color-on-surface-variant); margin-bottom: 16px;">
            Preencha apenas o essencial para emitir orçamentos imediatos.
          </p>
          <div class="form-group">
            <label class="form-label" for="rapido-nome">Nome / Razão Social *</label>
            <input type="text" id="rapido-nome" class="form-control" placeholder="NOME DO CLIENTE" required autofocus>
          </div>
          <div class="form-group">
            <label class="form-label" for="rapido-telefone">Telefone / WhatsApp *</label>
            <input type="text" id="rapido-telefone" class="form-control mono-text" data-mask="telefone" placeholder="(00) 00000-0000" required>
          </div>
          <div class="form-group">
            <label class="form-label" for="rapido-tipo">Tipo</label>
            <select id="rapido-tipo" class="form-control">
              <option value="CLIENTE" selected>CLIENTE</option>
              <option value="FORNECEDOR">FORNECEDOR</option>
              <option value="AMBOS">AMBOS</option>
            </select>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const nome = document.getElementById('rapido-nome').value.trim();
        const telefone = document.getElementById('rapido-telefone').value.trim();
        const tipo = document.getElementById('rapido-tipo').value;

        if (!nome || !telefone) {
          window.EMCUtils.showToast('Preencha o Nome e o Telefone.', 'error');
          return false;
        }

        try {
          await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES, {
            nome_razao: nome,
            telefone: window.EMCUtils.extrairApenasDigitos(telefone),
            tipo: tipo,
            tipo_pessoa: 'PF'
          });
          window.EMCUtils.showToast('Cliente cadastrado com sucesso!', 'success');
          this.carregarListaClientes();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao cadastrar cliente.', 'error');
          return false;
        }
      }
    });
  },

  abrirModalCadastroCompleto(cliente = null) {
    const isEdit = !!cliente;
    const title = isEdit ? `EDITAR CADASTRO #${cliente.id}` : 'NOVO CADASTRO COMPLETO (PF/PJ)';

    // Determina se inicia como PJ (se o cliente tem mais de 11 dígitos ou tipo_pessoa === 'PJ')
    const docInicial = window.EMCUtils.extrairApenasDigitos(cliente?.cnpj_cpf || '');
    const isPJInicial = docInicial.length > 11 || cliente?.tipo_pessoa === 'PJ';
    const tipoAtual = (cliente?.tipo || 'CLIENTE').toUpperCase();

    window.EMCUtils.openModal({
      title: title,
      size: 'lg',
      confirmText: isEdit ? 'ATUALIZAR' : 'CADASTRAR',
      content: `
        <form id="form-cliente-completo">
          <!-- Topo: Campo Único de Documento com Máscara Adaptável e Auto-Consulta na Saída -->
          <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
            <div class="form-group" style="margin-bottom: 0;">
              <label class="form-label" for="comp-documento">CPF / CNPJ (Identificação Fiscal)</label>
              <div style="position: relative;">
                <input type="text" id="comp-documento" class="form-control mono-text" data-mask="cpf-cnpj" placeholder="Digite CPF ou CNPJ..." value="${cliente?.cnpj_cpf ? window.EMCUtils.formatarCpfCnpjDinamico(cliente.cnpj_cpf) : ''}" autofocus>
                <div id="doc-spinner" class="loader-spinner" style="position: absolute; right: 12px; top: 12px; display: none; width: 18px; height: 18px;"></div>
              </div>
              <small class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); margin-top: 4px; display: block;">
                Ao digitar um CNPJ (14 dígitos) e sair do campo, os dados cadastrais e endereço são preenchidos automaticamente via Receita Federal.
              </small>
            </div>
          </div>

          <div id="container-nome-fantasia" style="display: grid; grid-template-columns: ${isPJInicial ? '2fr 1fr' : '1fr'}; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-nome" id="lbl-comp-nome">${isPJInicial ? 'Razão Social *' : 'Nome Completo *'}</label>
              <input type="text" id="comp-nome" class="form-control" value="${cliente?.nome_razao || ''}" required>
            </div>
            <div class="form-group" id="group-comp-fantasia" style="${isPJInicial ? '' : 'display: none;'}">
              <label class="form-label" for="comp-fantasia">Nome Fantasia</label>
              <input type="text" id="comp-fantasia" class="form-control" value="${cliente?.nome_fantasia || ''}">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-tipo">Tipo de Cadastro</label>
              <select id="comp-tipo" class="form-control">
                <option value="CLIENTE" ${tipoAtual === 'CLIENTE' ? 'selected' : ''}>CLIENTE</option>
                <option value="FORNECEDOR" ${tipoAtual === 'FORNECEDOR' ? 'selected' : ''}>FORNECEDOR</option>
                <option value="AMBOS" ${tipoAtual === 'AMBOS' ? 'selected' : ''}>AMBOS</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-email">E-mail Corporativo / Cobrança</label>
              <input type="email" id="comp-email" class="form-control" data-no-transform="true" placeholder="exemplo@empresa.com.br" value="${cliente?.email || ''}">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 140px 1fr 100px; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-cep">CEP</label>
              <input type="text" id="comp-cep" class="form-control mono-text" data-mask="cep" value="${cliente?.cep ? window.EMCUtils.formatarCep(cliente.cep) : ''}">
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-logradouro">Logradouro / Endereço</label>
              <input type="text" id="comp-logradouro" class="form-control" value="${cliente?.logradouro || ''}">
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-numero">Número</label>
              <input type="text" id="comp-numero" class="form-control" value="${cliente?.numero || ''}">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr 80px; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-bairro">Bairro</label>
              <input type="text" id="comp-bairro" class="form-control" value="${cliente?.bairro || ''}">
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-cidade">Cidade</label>
              <input type="text" id="comp-cidade" class="form-control" value="${cliente?.cidade || ''}">
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-uf">UF</label>
              <input type="text" id="comp-uf" class="form-control text-center" maxlength="2" value="${cliente?.uf || ''}">
            </div>
          </div>

          <!-- Seção de Contatos e Telefones (1:N com Nome, Telefone e Flag WhatsApp) -->
          <div class="card mt-16" style="background-color: var(--color-surface-container-high);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
              <div>
                <h4 style="font-size: 13px; font-weight: 700; color: var(--color-rust-orange);">CONTATOS & TELEFONES</h4>
                <p class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant);">Informe quem procurar e os telefones de contato</p>
              </div>
              <button type="button" class="btn btn-secondary btn-sm" id="btn-add-contato-linha">+ ADICIONAR CONTATO</button>
            </div>

            <div class="table-container" style="margin-bottom: 0;">
              <table class="table" style="font-size: 13px;">
                <thead>
                  <tr>
                    <th style="width: 45%;">NOME DO CONTATO / QUEM PROCURAR *</th>
                    <th style="width: 35%;">TELEFONE / CELULAR *</th>
                    <th style="width: 10%; text-align: center;">WHATSAPP</th>
                    <th style="width: 10%; text-align: right;">AÇÃO</th>
                  </tr>
                </thead>
                <tbody id="lista-contatos-modal-tbody">
                  <!-- Inserido dinamicamente via JS -->
                </tbody>
              </table>
            </div>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const docLimpo = window.EMCUtils.extrairApenasDigitos(document.getElementById('comp-documento').value);
        const isPJ = docLimpo.length > 11;
        const tipoPessoa = isPJ ? 'PJ' : 'PF';

        // Coleta os contatos da tabela dinâmica
        const rows = document.querySelectorAll('#lista-contatos-modal-tbody tr');
        const contatosPayload = [];

        rows.forEach((row) => {
          const nome_contato = row.querySelector('.contato-nome')?.value.trim();
          const telRaw = row.querySelector('.contato-telefone')?.value.trim();
          const telefone = window.EMCUtils.extrairApenasDigitos(telRaw);
          const is_whatsapp = !!row.querySelector('.contato-whatsapp')?.checked;

          if (nome_contato && telefone) {
            contatosPayload.push({
              nome_contato,
              telefone,
              is_whatsapp
            });
          }
        });

        const nomeRazaoVal = document.getElementById('comp-nome').value.trim();
        if (!nomeRazaoVal) {
          const msg = isPJ ? 'A Razão Social é obrigatória.' : 'O Nome Completo é obrigatório.';
          window.EMCUtils.showToast(msg, 'error');
          return false;
        }

        if (contatosPayload.length === 0) {
          window.EMCUtils.showToast('Preencha ao menos um contato telefônico com o nome do responsável.', 'error');
          return false;
        }

        const payload = {
          nome_razao: nomeRazaoVal,
          nome_fantasia: isPJ ? document.getElementById('comp-fantasia').value.trim() : '',
          tipo: document.getElementById('comp-tipo').value,
          tipo_pessoa: tipoPessoa,
          cnpj_cpf: docLimpo,
          telefone: contatosPayload[0]?.telefone || '',
          email: document.getElementById('comp-email').value.trim().toLowerCase(),
          cep: window.EMCUtils.extrairApenasDigitos(document.getElementById('comp-cep').value),
          logradouro: document.getElementById('comp-logradouro').value.trim(),
          numero: document.getElementById('comp-numero').value.trim(),
          bairro: document.getElementById('comp-bairro').value.trim(),
          cidade: document.getElementById('comp-cidade').value.trim(),
          uf: document.getElementById('comp-uf').value.trim().toUpperCase(),
          contatos: contatosPayload
        };

        try {
          if (isEdit) {
            await window.api.put(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}${cliente.id}/`, payload);
            window.EMCUtils.showToast('Cadastro atualizado com sucesso!', 'success');
          } else {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES, payload);
            window.EMCUtils.showToast('Cadastro criado com sucesso!', 'success');
          }
          this.carregarListaClientes();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar cadastro.', 'error');
          return false;
        }
      }
    });

    // Listener de alternância dinâmica entre modo CPF (Pessoa Física) e CNPJ (Pessoa Jurídica)
    const docInput = document.getElementById('comp-documento');
    const lblCompNome = document.getElementById('lbl-comp-nome');
    const groupCompFantasia = document.getElementById('group-comp-fantasia');
    const containerNomeFantasia = document.getElementById('container-nome-fantasia');

    const atualizarModoDocumento = () => {
      const digitos = window.EMCUtils.extrairApenasDigitos(docInput?.value || '');
      const modoPJ = digitos.length > 11;

      if (lblCompNome) {
        lblCompNome.textContent = modoPJ ? 'Razão Social *' : 'Nome Completo *';
      }
      if (groupCompFantasia) {
        groupCompFantasia.style.display = modoPJ ? '' : 'none';
      }
      if (containerNomeFantasia) {
        containerNomeFantasia.style.gridTemplateColumns = modoPJ ? '2fr 1fr' : '1fr';
      }
    };

    docInput?.addEventListener('input', atualizarModoDocumento);
    docInput?.addEventListener('paste', () => setTimeout(atualizarModoDocumento, 0));

    // Função para adicionar linha de contato dinamicamente
    const adicionarLinhaContato = (nome = '', telefone = '', isWhatsapp = false) => {
      const tbody = document.getElementById('lista-contatos-modal-tbody');
      if (!tbody) return;

      const rowId = 'contato-row-' + Math.random().toString(36).substr(2, 9);
      const tr = document.createElement('tr');
      tr.id = rowId;
      tr.innerHTML = `
        <td>
          <input type="text" class="form-control contato-nome" placeholder="Ex: JOÃO (COMPRAS)" value="${window.EMCUtils.escapeHtml(nome)}" required>
        </td>
        <td>
          <input type="text" class="form-control mono-text contato-telefone" data-mask="telefone" placeholder="(00) 00000-0000" value="${window.EMCUtils.formatarTelefoneDinamico(telefone)}" required>
        </td>
        <td style="text-align: center; vertical-align: middle;">
          <label style="cursor: pointer; display: inline-flex; align-items: center; justify-content: center; width: 100%;">
            <input type="checkbox" class="contato-whatsapp" ${isWhatsapp ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: var(--color-success);">
          </label>
        </td>
        <td style="text-align: right; vertical-align: middle;">
          <button type="button" class="btn btn-ghost btn-sm" onclick="document.getElementById('${rowId}')?.remove()">✕</button>
        </td>
      `;
      tbody.appendChild(tr);
    };

    document.getElementById('btn-add-contato-linha')?.addEventListener('click', () => {
      adicionarLinhaContato('', '', false);
    });

    // Popula contatos iniciais
    if (cliente?.contatos && cliente.contatos.length > 0) {
      cliente.contatos.forEach((c) => {
        adicionarLinhaContato(c.nome_contato, c.telefone, c.is_whatsapp);
      });
    } else if (cliente?.telefone) {
      adicionarLinhaContato('CONTATO PRINCIPAL', cliente.telefone, false);
    } else {
      adicionarLinhaContato('', '', false);
    }

    // Auto-consulta da Receita Federal e validação ao sair do campo (blur / exit)
    const docSpinner = document.getElementById('doc-spinner');
    let ultimoDocConsultado = '';

    const handleAutoConsultaDocumento = async () => {
      const doc = window.EMCUtils.extrairApenasDigitos(docInput.value);
      if (!doc) return;

      // Se for CNPJ (14 dígitos)
      if (doc.length === 14) {
        if (doc === ultimoDocConsultado) return;
        ultimoDocConsultado = doc;

        if (docSpinner) docSpinner.style.display = 'block';

        try {
          const endpoint = window.CONFIG.ENDPOINTS.CADASTROS.CONSULTA_CNPJ.replace('{cnpj}', doc);
          const res = await window.api.get(endpoint);
          const data = res?.data || res;

          if (data && (data.nome_razao || data.razao_social || data.nome)) {
            const razaoSocial = data.nome_razao || data.razao_social || data.nome || '';
            const nomeFantasia = data.nome_fantasia || data.fantasia || '';
            const logradouro = data.logradouro || '';
            const numero = data.numero || '';
            const bairro = data.bairro || '';
            const cidade = data.cidade || data.municipio || '';
            const uf = data.uf || '';
            const cep = data.cep || '';
            const telefone = data.telefone || data.ddd_telefone_1 || '';
            const email = data.email || '';

            const nomeInput = document.getElementById('comp-nome');
            const fantasiaInput = document.getElementById('comp-fantasia');
            const logradouroInput = document.getElementById('comp-logradouro');
            const numeroInput = document.getElementById('comp-numero');
            const bairroInput = document.getElementById('comp-bairro');
            const cidadeInput = document.getElementById('comp-cidade');
            const ufInput = document.getElementById('comp-uf');
            const cepInput = document.getElementById('comp-cep');
            const emailInput = document.getElementById('comp-email');

            if (nomeInput) nomeInput.value = razaoSocial;
            if (fantasiaInput && nomeFantasia) fantasiaInput.value = nomeFantasia;
            if (logradouroInput && logradouro) logradouroInput.value = logradouro;
            if (numeroInput && numero) numeroInput.value = numero;
            if (bairroInput && bairro) bairroInput.value = bairro;
            if (cidadeInput && cidade) cidadeInput.value = cidade;
            if (ufInput && uf) ufInput.value = uf;
            if (cepInput && cep) cepInput.value = window.EMCUtils.formatarCep(cep);
            if (emailInput && email && !emailInput.value.trim()) emailInput.value = email;

            // Se veio telefone e a tabela está vazia ou com campos em branco, preenche
            if (telefone) {
              const tbody = document.getElementById('lista-contatos-modal-tbody');
              const primeiroNome = tbody?.querySelector('.contato-nome');
              const primeiroTel = tbody?.querySelector('.contato-telefone');

              if (primeiroTel && !primeiroTel.value.trim()) {
                primeiroTel.value = window.EMCUtils.formatarTelefoneDinamico(telefone);
                if (primeiroNome && !primeiroNome.value.trim()) {
                  primeiroNome.value = 'COMERCIAL / EMPRESA';
                }
              }
            }

            window.EMCUtils.showToast('Dados do CNPJ preenchidos automaticamente via Receita Federal!', 'success');
          } else {
            window.EMCUtils.showToast('Nenhum dado retornado para este CNPJ.', 'warning');
          }
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'CNPJ não localizado na Receita Federal.', 'warning');
        } finally {
          if (docSpinner) docSpinner.style.display = 'none';
        }
      } else if (doc.length === 11) {
        // Validação de CPF Módulo 11
        if (!window.EMCUtils.validarCpf(doc)) {
          window.EMCUtils.showToast('Atenção: O CPF digitado é matematicamente inválido.', 'warning');
        }
      }
    };

    docInput?.addEventListener('blur', handleAutoConsultaDocumento);
    docInput?.addEventListener('change', handleAutoConsultaDocumento);
  },

  async editarCliente(id) {
    try {
      const cliente = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}${id}/`);
      this.abrirModalCadastroCompleto(cliente);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados do cliente.', 'error');
    }
  },

  async excluirCliente(id, nome) {
    window.EMCUtils.openModal({
      title: 'CONFIRMAÇÃO DE EXCLUSÃO',
      size: 'sm',
      confirmText: 'EXCLUIR / INATIVAR',
      cancelText: 'CANCELAR',
      content: `
        <div style="margin-bottom: 12px;">
          <p style="font-size: 14px; margin-bottom: 12px;">
            Deseja realmente excluir/inativar o cadastro de <strong>${window.EMCUtils.escapeHtml(nome)} (#${id})</strong>?
          </p>
          <div class="alert-banner alert-warning" style="font-size: 12px; margin-bottom: 0;">
            <strong>[SOFT DELETE]</strong> O registro será ocultado das operações ativas e movido para a <strong>Lixeira</strong>. Orçamentos e faturas passadas permanecem 100% íntegros e o cadastro poderá ser restaurado pelo administrador a qualquer momento.
          </div>
        </div>
      `,
      onConfirm: async () => {
        try {
          await window.api.delete(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}${id}/`);
          window.EMCUtils.showToast('Cadastro excluído com sucesso! Registro movido para a Lixeira.', 'success');
          this.carregarListaClientes();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao excluir cadastro.', 'error');
          return false;
        }
      }
    });
  },

  // ==========================================================================
  // 2. EQUIPAMENTOS E VEÍCULOS
  // ==========================================================================
  async renderEquipamentos(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <input type="text" id="filtro-equip-busca" class="form-control" placeholder="BUSCAR POR PLACA, IDENTIFICAÇÃO OU DESCRIÇÃO..." style="max-width: 400px;">
          <button class="btn btn-primary" id="btn-novo-equipamento">+ NOVO EQUIPAMENTO / MÁQUINA</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>PLACA</th>
              <th>IDENTIFICAÇÃO</th>
              <th>DESCRIÇÃO</th>
              <th>PROPRIETÁRIO ATUAL</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-equip-tbody">
            <tr><td colspan="6" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-novo-equipamento')?.addEventListener('click', () => this.abrirModalEquipamento());
    document.getElementById('filtro-equip-busca')?.addEventListener('input', () => this.carregarListaEquipamentos());

    await this.carregarListaEquipamentos();
  },

  async carregarListaEquipamentos() {
    const tbody = document.getElementById('lista-equip-tbody');
    if (!tbody) return;

    const busca = document.getElementById('filtro-equip-busca')?.value.trim() || '';

    try {
      const res = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}?search=${encodeURIComponent(busca)}`);
      const lista = res.results || res || [];

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center mono-text" style="color: var(--color-on-surface-variant); padding: 24px;">Nenhum equipamento cadastrado.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((item) => {
        const dono = item.cliente_atual_nome || 'NÃO VINCULADO';
        html += `
          <tr>
            <td class="mono-text">#${item.id}</td>
            <td class="mono-text"><strong>${window.EMCUtils.escapeHtml(item.placa ? window.EMCUtils.formatarPlacaVeiculo(item.placa) : '-')}</strong></td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(item.identificacao || '-')}</td>
            <td>${window.EMCUtils.escapeHtml(item.descricao)}</td>
            <td><span class="status-chip ${item.cliente_atual_nome ? 'info' : 'warning'}">${window.EMCUtils.escapeHtml(dono)}</span></td>
            <td style="text-align: right; white-space: nowrap;">
              <button class="btn btn-secondary btn-sm" onclick="window.CadastrosView.abrirModalHistoricoEquipamento(${item.id})">HISTÓRICO</button>
              <button class="btn btn-ghost btn-sm" onclick="window.CadastrosView.editarEquipamento(${item.id})">EDITAR</button>
              <button class="btn btn-ghost btn-sm" style="color: var(--color-error);" onclick="window.CadastrosView.excluirEquipamento(${item.id}, '${window.EMCUtils.escapeHtml(item.placa || item.identificacao || item.descricao)}')">EXCLUIR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  async abrirModalEquipamento(equip = null, preSelectClienteId = null) {
    const isEdit = !!equip;

    let clientes = [];
    try {
      const resCli = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}?page_size=1000`);
      const todos = resCli.results || resCli || [];
      clientes = todos.filter(c => (c.tipo || '').toUpperCase() !== 'FORNECEDOR');
    } catch (e) {
      console.warn('Erro ao carregar lista de clientes para vinculo:', e);
    }

    const donoAtualId = equip?.cliente_atual?.id || preSelectClienteId || null;

    let clientesOptions = '<option value="">NÃO VINCULADO (OFICINA GERAL / EM TRÂNSITO)</option>';
    clientes.forEach((c) => {
      const isSel = donoAtualId && Number(donoAtualId) === Number(c.id) ? 'selected' : '';
      const doc = c.cnpj_cpf ? ` (${window.EMCUtils.formatarCpfCnpjDinamico(c.cnpj_cpf)})` : '';
      clientesOptions += `<option value="${c.id}" ${isSel}>${window.EMCUtils.escapeHtml(c.nome_razao)}${doc}</option>`;
    });

    window.EMCUtils.openModal({
      title: isEdit ? `EDITAR EQUIPAMENTO #${equip.id}` : 'NOVO EQUIPAMENTO / VEÍCULO',
      size: 'md',
      confirmText: isEdit ? 'ATUALIZAR' : 'CADASTRAR',
      content: `
        <form id="form-equip">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="equip-placa">Placa (Antiga / Mercosul)</label>
              <input type="text" id="equip-placa" class="form-control mono-text" data-mask="placa" placeholder="ABC-1234 ou ABC-1D23" value="${equip?.placa || ''}">
            </div>
            <div class="form-group">
              <label class="form-label" for="equip-identificacao">Identificação / Chassi / Frota</label>
              <input type="text" id="equip-identificacao" class="form-control mono-text" placeholder="EX: TRATOR 04 / CHASSI 9BW..." value="${equip?.identificacao || ''}">
            </div>
          </div>

          <div class="form-group">
            <label class="form-label" for="equip-descricao">Descrição Completa *</label>
            <input type="text" id="equip-descricao" class="form-control" placeholder="EX: ESCAVADEIRA HIDRÁULICA CAT 320D" value="${equip?.descricao || ''}" required>
          </div>

          <div class="form-group mt-12">
            <label class="form-label" for="equip-cliente">Cliente Proprietário / Empresa Responsável</label>
            <select id="equip-cliente" class="form-control">
              ${clientesOptions}
            </select>
            <small class="mono-text" style="font-size: 11px; color: var(--color-on-surface-variant); display: block; margin-top: 4px;">
              ${isEdit ? 'Alterar o cliente proprietário registrará a transferência de titularidade no histórico do equipamento.' : 'Selecione a qual cliente este equipamento ou máquina pertence.'}
            </small>
          </div>
        </form>
      `,
      onConfirm: async () => {
        const descricao = document.getElementById('equip-descricao').value.trim();
        const placa = document.getElementById('equip-placa').value.trim();
        const identificacao = document.getElementById('equip-identificacao').value.trim();
        const clienteVal = document.getElementById('equip-cliente').value;
        const cliente_id = clienteVal ? parseInt(clienteVal) : null;

        if (!descricao) {
          window.EMCUtils.showToast('A descrição é obrigatória.', 'error');
          return false;
        }

        if (placa && !window.EMCUtils.validarPlacaVeiculo(placa)) {
          window.EMCUtils.showToast('Placa inválida. O formato deve ser Padrão Antigo (ex: ABC-1234) ou Mercosul (ex: ABC-1D23).', 'error');
          return false;
        }

        try {
          const payload = {
            descricao,
            placa: window.EMCUtils.sanitizarTextoEmTempoReal(placa),
            identificacao: window.EMCUtils.sanitizarTextoEmTempoReal(identificacao),
            cliente_id
          };

          if (isEdit) {
            await window.api.put(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${equip.id}/`, payload);
            window.EMCUtils.showToast('Equipamento atualizado com sucesso!', 'success');
          } else {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS, payload);
            window.EMCUtils.showToast('Equipamento criado com sucesso!', 'success');
          }
          this.carregarListaEquipamentos();
          this.carregarListaClientes();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar equipamento.', 'error');
          return false;
        }
      }
    });

    // Inicializa a Combobox Pesquisável com Autocomplete
    setTimeout(() => {
      const selectEl = document.getElementById('equip-cliente');
      if (selectEl) {
        window.EMCUtils.initSearchableSelect(selectEl, {
          placeholder: 'SELECIONE OU DIGITE O NOME DO CLIENTE...'
        });
      }
    }, 50);
  },

  async editarEquipamento(id) {
    try {
      const equip = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${id}/`);
      this.abrirModalEquipamento(equip);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados do equipamento.', 'error');
    }
  },

  async excluirEquipamento(id, descricao) {
    window.EMCUtils.openModal({
      title: 'CONFIRMAÇÃO DE EXCLUSÃO',
      size: 'sm',
      confirmText: 'EXCLUIR / INATIVAR',
      cancelText: 'CANCELAR',
      content: `
        <div style="margin-bottom: 12px;">
          <p style="font-size: 14px; margin-bottom: 12px;">
            Deseja realmente excluir/inativar o equipamento <strong>${window.EMCUtils.escapeHtml(descricao)} (#${id})</strong>?
          </p>
          <div class="alert-banner alert-warning" style="font-size: 12px; margin-bottom: 0;">
            <strong>[SOFT DELETE]</strong> O equipamento será desvinculado de frotas ativas e movido para a <strong>Lixeira</strong>. Orçamentos passados permanecem 100% íntegros e o equipamento poderá ser restaurado pelo administrador a qualquer momento.
          </div>
        </div>
      `,
      onConfirm: async () => {
        try {
          await window.api.delete(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${id}/`);
          window.EMCUtils.showToast('Equipamento excluído com sucesso! Registro movido para a Lixeira.', 'success');
          this.carregarListaEquipamentos();
          this.carregarListaClientes();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao excluir equipamento.', 'error');
          return false;
        }
      }
    });
  }
};
