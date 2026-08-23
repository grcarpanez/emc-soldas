/**
 * EMC Soldas - View de Cadastros Básicos (Clientes, Fornecedores, Equipamentos, UOM, Atributos)
 */

window.CadastrosView = {
  currentTab: 'clientes',

  render(container) {
    container.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px;">
        <div>
          <h1 style="font-size: 24px; font-weight: 700;">CADASTROS &STRUTURAIS</h1>
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">GESTÃO DE CLIENTES, FORNECEDORES, MÁQUINAS E DICIONÁRIOS</p>
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
        <button class="tab-btn ${this.currentTab === 'dicionario-uom' ? 'active' : ''}" id="tab-btn-uom">
          DICIONÁRIO UOM
        </button>
        <button class="tab-btn ${this.currentTab === 'dicionario-atributos' ? 'active' : ''}" id="tab-btn-atributos">
          DICIONÁRIO ATRIBUTOS
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
    document.getElementById('tab-btn-uom')?.addEventListener('click', () => {
      this.currentTab = 'dicionario-uom';
      this.render(container);
    });
    document.getElementById('tab-btn-atributos')?.addEventListener('click', () => {
      this.currentTab = 'dicionario-atributos';
      this.render(container);
    });

    const content = document.getElementById('cadastros-tab-content');
    if (this.currentTab === 'clientes') {
      this.renderClientes(content);
    } else if (this.currentTab === 'equipamentos') {
      this.renderEquipamentos(content);
    } else if (this.currentTab === 'dicionario-uom') {
      this.renderDicionarioUom(content);
    } else if (this.currentTab === 'dicionario-atributos') {
      this.renderDicionarioAtributos(content);
    }
  },

  // ==========================================================================
  // 1. CLIENTES E FORNECEDORES
  // ==========================================================================
  async renderClientes(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <div style="display: flex; gap: 8px; flex: 1; min-width: 280px;">
            <input type="text" id="filtro-cliente-busca" class="form-control" placeholder="BUSCAR POR NOME, CNPJ/CPF OU CIDADE..." style="flex: 1;">
            <select id="filtro-cliente-tipo" class="form-control" style="width: 160px;">
              <option value="">TODOS OS TIPOS</option>
              <option value="CLIENTE">CLIENTES</option>
              <option value="FORNECEDOR">FORNECEDORES</option>
              <option value="AMBOS">AMBOS</option>
            </select>
          </div>

          <div style="display: flex; gap: 8px;">
            <button class="btn btn-secondary" id="btn-novo-cliente-rapido">+ CADASTRO RÁPIDO</button>
            <button class="btn btn-primary" id="btn-novo-cliente-completo">+ NOVO CADASTRO</button>
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
        const badgeTipo = item.tipo === 'CLIENTE' ? 'info' : (item.tipo === 'FORNECEDOR' ? 'warning' : 'success');
        html += `
          <tr>
            <td class="mono-text">#${item.id}</td>
            <td><span class="status-chip ${badgeTipo}">${item.tipo}</span></td>
            <td><strong>${window.EMCUtils.escapeHtml(item.nome_razao)}</strong></td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(item.cnpj_cpf ? window.EMCUtils.formatarCpfCnpjDinamico(item.cnpj_cpf) : '-')}</td>
            <td class="mono-text">${window.EMCUtils.escapeHtml(item.telefone ? window.EMCUtils.formatarTelefoneDinamico(item.telefone) : '-')}</td>
            <td>${window.EMCUtils.escapeHtml(item.cidade || '-')}${item.uf ? ' / ' + item.uf : ''}</td>
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" onclick="window.CadastrosView.editarCliente(${item.id})">EDITAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="7" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
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

    window.EMCUtils.openModal({
      title: title,
      size: 'lg',
      confirmText: isEdit ? 'ATUALIZAR' : 'CADASTRAR',
      content: `
        <form id="form-cliente-completo">
          <!-- Topo Absoluto: Tipo de Pessoa e CPF/CNPJ com Auto-Consulta -->
          <div class="card mb-16" style="background-color: var(--color-surface-container-high);">
            <div style="display: grid; grid-template-columns: 140px 1fr auto; gap: 12px; align-items: flex-end;">
              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label">Tipo Pessoa</label>
                <select id="comp-tipo-pessoa" class="form-control">
                  <option value="PJ" ${cliente?.tipo_pessoa === 'PJ' ? 'selected' : ''}>PJ (CNPJ)</option>
                  <option value="PF" ${cliente?.tipo_pessoa === 'PF' ? 'selected' : ''}>PF (CPF)</option>
                </select>
              </div>

              <div class="form-group" style="margin-bottom: 0;">
                <label class="form-label" for="comp-documento">CPF / CNPJ (Primeiro Campo)</label>
                <input type="text" id="comp-documento" class="form-control mono-text" data-mask="cpf-cnpj" placeholder="Digite o documento..." value="${cliente?.cnpj_cpf || ''}">
              </div>

              <button type="button" class="btn btn-secondary" id="btn-consultar-cnpj" style="height: 42px;">
                BUSCAR DADOS ➔
              </button>
            </div>
            <div id="doc-validation-feedback" class="mono-text mt-16" style="font-size: 12px; display: none;"></div>
          </div>

          <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-nome">Razão Social / Nome Completo *</label>
              <input type="text" id="comp-nome" class="form-control" value="${cliente?.nome_razao || ''}" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-fantasia">Nome Fantasia</label>
              <input type="text" id="comp-fantasia" class="form-control" value="${cliente?.nome_fantasia || ''}">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-tipo">Tipo de Cadastro</label>
              <select id="comp-tipo" class="form-control">
                <option value="CLIENTE" ${cliente?.tipo === 'CLIENTE' ? 'selected' : ''}>CLIENTE</option>
                <option value="FORNECEDOR" ${cliente?.tipo === 'FORNECEDOR' ? 'selected' : ''}>FORNECEDOR</option>
                <option value="AMBOS" ${cliente?.tipo === 'AMBOS' ? 'selected' : ''}>AMBOS</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-telefone">Telefone Principal *</label>
              <input type="text" id="comp-telefone" class="form-control mono-text" data-mask="telefone" value="${cliente?.telefone || ''}" required>
            </div>
            <div class="form-group">
              <label class="form-label" for="comp-email">E-mail</label>
              <input type="email" id="comp-email" class="form-control" data-no-transform="true" value="${cliente?.email || ''}">
            </div>
          </div>

          <div style="display: grid; grid-template-columns: 140px 1fr 100px; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="comp-cep">CEP</label>
              <input type="text" id="comp-cep" class="form-control mono-text" data-mask="cep" value="${cliente?.cep || ''}">
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
        </form>
      `,
      onConfirm: async () => {
        const payload = {
          nome_razao: document.getElementById('comp-nome').value.trim(),
          nome_fantasia: document.getElementById('comp-fantasia').value.trim(),
          tipo: document.getElementById('comp-tipo').value,
          tipo_pessoa: document.getElementById('comp-tipo-pessoa').value,
          cnpj_cpf: window.EMCUtils.extrairApenasDigitos(document.getElementById('comp-documento').value),
          telefone: window.EMCUtils.extrairApenasDigitos(document.getElementById('comp-telefone').value),
          email: document.getElementById('comp-email').value.trim().toLowerCase(),
          cep: window.EMCUtils.extrairApenasDigitos(document.getElementById('comp-cep').value),
          logradouro: document.getElementById('comp-logradouro').value.trim(),
          numero: document.getElementById('comp-numero').value.trim(),
          bairro: document.getElementById('comp-bairro').value.trim(),
          cidade: document.getElementById('comp-cidade').value.trim(),
          uf: document.getElementById('comp-uf').value.trim().toUpperCase()
        };

        if (!payload.nome_razao || !payload.telefone) {
          window.EMCUtils.showToast('Nome e Telefone são obrigatórios.', 'error');
          return false;
        }

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

    // Listener para busca de CNPJ automática
    const btnConsultar = document.getElementById('btn-consultar-cnpj');
    const docInput = document.getElementById('comp-documento');
    const feedback = document.getElementById('doc-validation-feedback');

    const handleConsultaCnpj = async () => {
      const doc = window.EMCUtils.extrairApenasDigitos(docInput.value);
      if (doc.length !== 14) {
        window.EMCUtils.showToast('Digite um CNPJ válido de 14 dígitos para buscar.', 'warning');
        return;
      }

      btnConsultar.disabled = true;
      btnConsultar.textContent = 'CONSULTANDO...';

      try {
        const endpoint = window.CONFIG.ENDPOINTS.CADASTROS.CONSULTA_CNPJ.replace('{cnpj}', doc);
        const res = await window.api.get(endpoint);

        if (res.razao_social) {
          document.getElementById('comp-nome').value = res.razao_social;
          if (res.nome_fantasia) document.getElementById('comp-fantasia').value = res.nome_fantasia;
          if (res.logradouro) document.getElementById('comp-logradouro').value = res.logradouro;
          if (res.numero) document.getElementById('comp-numero').value = res.numero;
          if (res.bairro) document.getElementById('comp-bairro').value = res.bairro;
          if (res.cidade) document.getElementById('comp-cidade').value = res.cidade;
          if (res.uf) document.getElementById('comp-uf').value = res.uf;
          if (res.cep) document.getElementById('comp-cep').value = window.EMCUtils.formatarCep(res.cep);
          if (res.telefone) document.getElementById('comp-telefone').value = window.EMCUtils.formatarTelefoneDinamico(res.telefone);
          if (res.email) document.getElementById('comp-email').value = res.email;

          window.EMCUtils.showToast('Dados do CNPJ preenchidos automaticamente!', 'success');
        }
      } catch (err) {
        window.EMCUtils.showToast(err.message || 'CNPJ não localizado ou serviço indisponível.', 'warning');
      } finally {
        btnConsultar.disabled = false;
        btnConsultar.textContent = 'BUSCAR DADOS ➔';
      }
    };

    btnConsultar?.addEventListener('click', handleConsultaCnpj);
  },

  async editarCliente(id) {
    try {
      const cliente = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.CLIENTES}${id}/`);
      this.abrirModalCadastroCompleto(cliente);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados do cliente.', 'error');
    }
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
            <td style="text-align: right;">
              <button class="btn btn-ghost btn-sm" onclick="window.CadastrosView.editarEquipamento(${item.id})">EDITAR</button>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  abrirModalEquipamento(equip = null) {
    const isEdit = !!equip;

    window.EMCUtils.openModal({
      title: isEdit ? `EDITAR EQUIPAMENTO #${equip.id}` : 'NOVO EQUIPAMENTO / VEÍCULO',
      size: 'md',
      confirmText: isEdit ? 'ATUALIZAR' : 'CADASTRAR',
      content: `
        <form id="form-equip">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="form-group">
              <label class="form-label" for="equip-placa">Placa (Antiga / Mercosul)</label>
              <input type="text" id="equip-placa" class="form-control mono-text" data-mask="placa" placeholder="ABC-1234 ou ABC1D23" value="${equip?.placa || ''}">
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
        </form>
      `,
      onConfirm: async () => {
        const descricao = document.getElementById('equip-descricao').value.trim();
        const placa = document.getElementById('equip-placa').value.trim();
        const identificacao = document.getElementById('equip-identificacao').value.trim();

        if (!descricao) {
          window.EMCUtils.showToast('A descrição é obrigatória.', 'error');
          return false;
        }

        try {
          const payload = {
            descricao,
            placa: window.EMCUtils.sanitizarTextoEmTempoReal(placa),
            identificacao: window.EMCUtils.sanitizarTextoEmTempoReal(identificacao)
          };

          if (isEdit) {
            await window.api.put(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${equip.id}/`, payload);
            window.EMCUtils.showToast('Equipamento atualizado com sucesso!', 'success');
          } else {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS, payload);
            window.EMCUtils.showToast('Equipamento criado com sucesso!', 'success');
          }
          this.carregarListaEquipamentos();
          return true;
        } catch (err) {
          window.EMCUtils.showToast(err.message || 'Erro ao salvar equipamento.', 'error');
          return false;
        }
      }
    });
  },

  async editarEquipamento(id) {
    try {
      const equip = await window.api.get(`${window.CONFIG.ENDPOINTS.CADASTROS.EQUIPAMENTOS}${id}/`);
      this.abrirModalEquipamento(equip);
    } catch (err) {
      window.EMCUtils.showToast('Erro ao carregar dados do equipamento.', 'error');
    }
  },

  // ==========================================================================
  // 3. DICIONÁRIO UOM
  // ==========================================================================
  async renderDicionarioUom(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">UNIDADES DE MEDIDA PADRONIZADAS (COMPRA, CONSUMO E VENDA)</p>
          <button class="btn btn-primary" id="btn-novo-uom">+ NOVA UNIDADE DE MEDIDA</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>SIGLA</th>
              <th>DESCRIÇÃO OFICIAL</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-uom-tbody">
            <tr><td colspan="4" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-novo-uom')?.addEventListener('click', () => {
      window.EMCUtils.openModal({
        title: 'NOVA UNIDADE DE MEDIDA (UOM)',
        size: 'sm',
        confirmText: 'SALVAR',
        content: `
          <div class="form-group">
            <label class="form-label">Sigla (Ex: KG, M2, L, UN, CX) *</label>
            <input type="text" id="uom-sigla" class="form-control mono-text" maxlength="10" required autofocus>
          </div>
          <div class="form-group">
            <label class="form-label">Descrição Oficial *</label>
            <input type="text" id="uom-desc" class="form-control" required>
          </div>
        `,
        onConfirm: async () => {
          const sigla = document.getElementById('uom-sigla').value.trim();
          const descricao = document.getElementById('uom-desc').value.trim();
          if (!sigla || !descricao) return false;

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM, { sigla, descricao });
            window.EMCUtils.showToast('UOM cadastrada com sucesso!', 'success');
            this.renderDicionarioUom(container);
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao salvar UOM.', 'error');
            return false;
          }
        }
      });
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM);
      const lista = res.results || res || [];
      const tbody = document.getElementById('lista-uom-tbody');

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center mono-text">Nenhuma UOM cadastrada.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((u) => {
        html += `
          <tr>
            <td class="mono-text">#${u.id}</td>
            <td class="mono-text"><strong>${window.EMCUtils.escapeHtml(u.sigla)}</strong></td>
            <td>${window.EMCUtils.escapeHtml(u.descricao)}</td>
            <td style="text-align: right;">
              <span class="mono-text" style="color: var(--color-on-surface-variant); font-size: 11px;">PADRÃO</span>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-uom-tbody').innerHTML = `<tr><td colspan="4" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  },

  // ==========================================================================
  // 4. DICIONÁRIO ATRIBUTOS
  // ==========================================================================
  async renderDicionarioAtributos(container) {
    container.innerHTML = `
      <div class="card mb-16">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
          <p class="mono-text" style="font-size: 13px; color: var(--color-on-surface-variant);">CATÁLOGO CENTRAL DE CARACTERÍSTICAS TÉCNICAS (ESPESSURA, DIÂMETRO, LIGA)</p>
          <button class="btn btn-primary" id="btn-novo-atributo">+ NOVO ATRIBUTO</button>
        </div>
      </div>

      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>NOME DO ATRIBUTO</th>
              <th style="text-align: right;">AÇÕES</th>
            </tr>
          </thead>
          <tbody id="lista-atributos-tbody">
            <tr><td colspan="3" class="text-center"><div class="loader-spinner"></div></td></tr>
          </tbody>
        </table>
      </div>
    `;

    document.getElementById('btn-novo-atributo')?.addEventListener('click', () => {
      window.EMCUtils.openModal({
        title: 'NOVO ATRIBUTO TÉCNICO',
        size: 'sm',
        confirmText: 'SALVAR',
        content: `
          <div class="form-group">
            <label class="form-label">Nome do Atributo (Ex: ESPESSURA, LIGA, ROSCA) *</label>
            <input type="text" id="attr-nome" class="form-control" required autofocus>
          </div>
        `,
        onConfirm: async () => {
          const nome_atributo = document.getElementById('attr-nome').value.trim();
          if (!nome_atributo) return false;

          try {
            await window.api.post(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_ATRIBUTOS, { nome_atributo });
            window.EMCUtils.showToast('Atributo cadastrado com sucesso!', 'success');
            this.renderDicionarioAtributos(container);
            return true;
          } catch (e) {
            window.EMCUtils.showToast(e.message || 'Erro ao salvar atributo.', 'error');
            return false;
          }
        }
      });
    });

    try {
      const res = await window.api.get(window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_ATRIBUTOS);
      const lista = res.results || res || [];
      const tbody = document.getElementById('lista-atributos-tbody');

      if (!lista.length) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-center mono-text">Nenhum atributo cadastrado.</td></tr>';
        return;
      }

      let html = '';
      lista.forEach((a) => {
        html += `
          <tr>
            <td class="mono-text">#${a.id}</td>
            <td><strong>${window.EMCUtils.escapeHtml(a.nome_atributo)}</strong></td>
            <td style="text-align: right;">
              <span class="mono-text" style="color: var(--color-on-surface-variant); font-size: 11px;">ATIVO</span>
            </td>
          </tr>
        `;
      });
      tbody.innerHTML = html;
    } catch (err) {
      document.getElementById('lista-atributos-tbody').innerHTML = `<tr><td colspan="3" class="text-center" style="color: var(--color-error);">${window.EMCUtils.escapeHtml(err.message)}</td></tr>`;
    }
  }
};
