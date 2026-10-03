/**
 * EMC Soldas - Utilitários Globais de Formatação, Sanitização e Máscaras de Entrada
 * Implementa Defesa de Camada 1: Conversão em tempo real e máscaras dinâmicas de interface.
 */

// ============================================================================
// 1. SANITIZAÇÃO DE TEXTO (MAIÚSCULAS SEM ACENTO - ASCII PURO)
// ============================================================================

/**
 * Remove acentos, caracteres diacríticos e converte para MAIÚSCULAS.
 * Preserva caracteres especiais comuns válidos (pontuação, hífens, barras, parênteses, etc.).
 * @param {string} texto 
 * @returns {string}
 */
function sanitizarTextoEmTempoReal(texto) {
  if (!texto || typeof texto !== 'string') return texto;

  // Substitui caracteres ordinais antes da decomposição
  let limpo = texto.replace(/º/g, 'O').replace(/ª/g, 'A').replace(/°/g, 'O');

  // Decompõe diacríticos e remove caracteres combinados
  limpo = limpo
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // remove acentos
    .replace(/ç/gi, 'C');            // trata cedilha explicitamente

  return limpo.toUpperCase();
}

/**
 * Extrai estritamente os dígitos numéricos de uma string.
 * @param {string} valor 
 * @returns {string}
 */
function extrairApenasDigitos(valor) {
  if (!valor) return '';
  return String(valor).replace(/\D/g, '');
}

// ============================================================================
// 2. MÁSCARA MONETÁRIA ESTILO ATM (AUTOATENDIMENTO BANCÁRIO)
// ============================================================================

/**
 * Formata valor em centavos numéricos para o padrão de moeda brasileiro BRL com prefixo fixo.
 * @param {number|string} centavos - Valor em centavos (ex: 5000 para R$ 50,00)
 * @returns {string}
 */
function formatarCentavosParaMoedaATM(centavos) {
  const num = parseInt(centavos, 10) || 0;
  const valorDecimal = num / 100;
  return 'R$ ' + valorDecimal.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * Converte a string formatada em ATM ("R$ 1.250,50") de volta para float ("1250.50").
 * @param {string} valorFormatado 
 * @returns {number}
 */
function converterMoedaATMParaFloat(valorFormatado) {
  const digitos = extrairApenasDigitos(valorFormatado);
  const centavos = parseInt(digitos, 10) || 0;
  return centavos / 100;
}

/**
 * Aplica o comportamento de ATM em um elemento de input.
 * Inicia em R$ 0,00, preenche da direita para a esquerda e recua zeros com Backspace.
 * @param {HTMLInputElement} input 
 */
function aplicarMascaraMoedaATM(input) {
  let digitos = extrairApenasDigitos(input.value);
  if (!digitos) {
    digitos = '0';
  }
  // Limita a 12 dígitos (até 999 milhões) para evitar overflow
  if (digitos.length > 12) {
    digitos = digitos.slice(0, 12);
  }
  input.value = formatarCentavosParaMoedaATM(digitos);
  input.dataset.rawCentavos = digitos;
}

// ============================================================================
// 3. MÁSCARAS DINÂMICAS DE DOCUMENTOS E CONTATOS
// ============================================================================

/**
 * Formata CPF (11 dígitos) ou CNPJ (14 dígitos) dinamicamente conforme a digitação.
 * @param {string} valor 
 * @returns {string}
 */
function formatarCpfCnpjDinamico(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 14);

  if (digitos.length <= 11) {
    // CPF: 000.000.000-00
    return digitos
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d)/, '$1.$2')
      .replace(/(\d{3})(\d{1,2})$/, '$1-$2');
  } else {
    // CNPJ: 00.000.000/0000-00
    return digitos
      .replace(/^(\d{2})(\d)/, '$1.$2')
      .replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3')
      .replace(/\.(\d{3})(\d)/, '.$1/$2')
      .replace(/(\d{4})(\d{1,2})$/, '$1-$2');
  }
}

/**
 * Formata Telefone Fixo (10 dígitos) ou Celular (11 dígitos) dinamicamente.
 * @param {string} valor 
 * @returns {string}
 */
function formatarTelefoneIndividual(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 11);
  if (!digitos) return '';
  if (digitos.length <= 10) {
    // Fixo: (00) 0000-0000
    return digitos
      .replace(/^(\d{2})(\d)/g, '($1) $2')
      .replace(/(\d{4})(\d)/, '$1-$2');
  } else {
    // Celular: (00) 00000-0000
    return digitos
      .replace(/^(\d{2})(\d)/g, '($1) $2')
      .replace(/(\d{5})(\d)/, '$1-$2');
  }
}

function formatarTelefoneDinamico(valor) {
  if (!valor) return '';
  const str = String(valor);
  if (str.includes(';')) {
    return str.split(';').map(p => formatarTelefoneIndividual(p)).filter(Boolean).join('; ');
  }
  return formatarTelefoneIndividual(str);
}

/**
 * Formata CEP: 00000-000
 * @param {string} valor 
 * @returns {string}
 */
function formatarCep(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 8);
  return digitos.replace(/^(\d{5})(\d)/, '$1-$2');
}

/**
 * Valida se a placa atende estritamente ao Padrão Antigo (AAA-0000) ou Mercosul (AAA0A00):
 * - 3 primeiros dígitos são letras (A-Z)
 * - 4º dígito é número (0-9)
 * - 5º dígito é letra ou número (A-Z ou 0-9)
 * - 6º e 7º dígitos são números (0-9)
 * @param {string} valor 
 * @returns {boolean}
 */
function validarPlacaVeiculo(valor) {
  if (!valor || !valor.trim()) return true;
  const limpo = valor.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
  if (limpo.length !== 7) return false;
  return /^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$/.test(limpo);
}

/**
 * Formata e filtra Placa de Veículo em tempo real aceitando apenas os padrões Antigo e Mercosul:
 * - 1º, 2º e 3º dígitos: Letras (A-Z)
 * - 4º dígito: Número (0-9)
 * - 5º dígito: Letra ou Número (A-Z ou 0-9)
 * - 6º e 7º dígitos: Números (0-9)
 * Máscara universal automática com hífen (###-####): Antigo AAA-0000 e Mercosul AAA-0A00.
 * O hífen é inserido automaticamente após a 3ª letra sem exigir que o usuário digite '-'.
 * @param {string} valor 
 * @returns {string}
 */
function formatarPlacaVeiculo(valor) {
  if (!valor) return '';
  const bruto = sanitizarTextoEmTempoReal(valor).replace(/[^A-Z0-9]/g, '');
  let resultado = '';

  for (let i = 0; i < bruto.length && resultado.length < 7; i++) {
    const char = bruto[i];
    const pos = resultado.length; // índice de 0 a 6
    if (pos >= 0 && pos <= 2) {
      if (/[A-Z]/.test(char)) {
        resultado += char;
      }
    } else if (pos === 3) {
      if (/\d/.test(char)) {
        resultado += char;
      }
    } else if (pos === 4) {
      if (/[A-Z0-9]/.test(char)) {
        resultado += char;
      }
    } else if (pos === 5 || pos === 6) {
      if (/\d/.test(char)) {
        resultado += char;
      }
    }
  }

  // Insere hífen automaticamente após as 3 primeiras letras (padrão universal ###-####)
  if (resultado.length > 3) {
    return resultado.slice(0, 3) + '-' + resultado.slice(3);
  }
  return resultado;
}

/**
 * Formata Chave de Acesso NFe/NFCe (44 dígitos em grupos de 4).
 * @param {string} valor 
 * @returns {string}
 */
function formatarChaveAcessoNfe(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 50);

  // Máscara da NFS-e Nacional de 50 dígitos: 9999999 9 99999999999999 99999 999999999999999 9999999 9
  if (digitos.length > 44) {
    const partes = [];
    if (digitos.length > 0) partes.push(digitos.slice(0, 7));
    if (digitos.length > 7) partes.push(digitos.slice(7, 8));
    if (digitos.length > 8) partes.push(digitos.slice(8, 22));
    if (digitos.length > 22) partes.push(digitos.slice(22, 27));
    if (digitos.length > 27) partes.push(digitos.slice(27, 42));
    if (digitos.length > 42) partes.push(digitos.slice(42, 49));
    if (digitos.length > 49) partes.push(digitos.slice(49, 50));
    return partes.filter(Boolean).join(' ');
  }

  // Padrão canônico da NF-e / NFCom / NFC-e de 44 dígitos: 11 grupos de 4 dígitos
  return digitos.replace(/(\d{4})(?=\d)/g, '$1 ');
}

/**
 * Formata Linha Digitável de Boleto Bancário.
 * @param {string} valor 
 * @returns {string}
 */
function formatarLinhaDigitavelBoleto(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 47);
  if (digitos.length <= 44) {
    // Código de barras / padrão simples
    return digitos;
  }
  return digitos
    .replace(/^(\d{5})(\d{5})(\d{5})(\d{6})(\d{5})(\d{6})(\d{1})(\d{14})$/, '$1.$2 $3.$4 $5.$6 $7 $8');
}

/**
 * Valida CPF utilizando o algoritmo oficial Módulo 11.
 * @param {string} cpf 
 * @returns {boolean}
 */
function validarCpf(cpf) {
  const digitos = extrairApenasDigitos(cpf);
  if (digitos.length !== 11) return false;
  if (/^(\d)\1{10}$/.test(digitos)) return false;

  let soma = 0;
  for (let i = 0; i < 9; i++) {
    soma += parseInt(digitos[i], 10) * (10 - i);
  }
  let resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  if (resto !== parseInt(digitos[9], 10)) return false;

  soma = 0;
  for (let i = 0; i < 10; i++) {
    soma += parseInt(digitos[i], 10) * (11 - i);
  }
  resto = (soma * 10) % 11;
  if (resto === 10 || resto === 11) resto = 0;
  return resto === parseInt(digitos[10], 10);
}

/**
 * Valida CNPJ utilizando o algoritmo oficial Módulo 11.
 * @param {string} cnpj 
 * @returns {boolean}
 */
function validarCnpj(cnpj) {
  const digitos = extrairApenasDigitos(cnpj);
  if (digitos.length !== 14) return false;
  if (/^(\d)\1{13}$/.test(digitos)) return false;

  const pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  let soma = 0;
  for (let i = 0; i < 12; i++) {
    soma += parseInt(digitos[i], 10) * pesos1[i];
  }
  let resto = soma % 11;
  const dig1 = resto < 2 ? 0 : 11 - resto;
  if (dig1 !== parseInt(digitos[12], 10)) return false;

  const pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  soma = 0;
  for (let i = 0; i < 13; i++) {
    soma += parseInt(digitos[i], 10) * pesos2[i];
  }
  resto = soma % 11;
  const dig2 = resto < 2 ? 0 : 11 - resto;
  return dig2 === parseInt(digitos[13], 10);
}

// ============================================================================
// 4. FORMATADORES DE EXIBIÇÃO E CONVERSÃO
// ============================================================================

/**
 * Formata um número/string decimal para moeda brasileira (R$ 1.250,50).
 * @param {number|string} valor 
 * @returns {string}
 */
function formatarMoeda(valor) {
  const num = parseFloat(valor) || 0;
  return 'R$ ' + num.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  });
}

/**
 * Formata data ISO (YYYY-MM-DD) para padrão brasileiro (DD/MM/YYYY).
 * @param {string} dataIso 
 * @returns {string}
 */
function formatarDataPtBr(dataIso) {
  if (!dataIso) return '-';
  const partes = String(dataIso).split('T')[0].split('-');
  if (partes.length === 3) {
    return `${partes[2]}/${partes[1]}/${partes[0]}`;
  }
  return dataIso;
}

/**
 * Formata data e hora ISO para padrão brasileiro (DD/MM/YYYY HH:mm).
 * @param {string} dataHoraIso 
 * @returns {string}
 */
function formatarDataHoraPtBr(dataHoraIso) {
  if (!dataHoraIso) return '-';
  try {
    const d = new Date(dataHoraIso);
    if (isNaN(d.getTime())) return dataHoraIso;
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const ano = d.getFullYear();
    const hora = String(d.getHours()).padStart(2, '0');
    const min = String(d.getMinutes()).padStart(2, '0');
    return `${dia}/${mes}/${ano} ${hora}:${min}`;
  } catch {
    return dataHoraIso;
  }
}

/**
 * Formata número de horas para exibição (ex: "1,50 h").
 * @param {number|string} valor 
 * @returns {string}
 */
function formatarHoras(valor) {
  const num = parseFloat(valor) || 0;
  return num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' h';
}

/**
 * Formata porcentagem (ex: "5,00 %").
 * @param {number|string} valor 
 * @returns {string}
 */
function formatarPorcentagem(valor) {
  const num = parseFloat(valor) || 0;
  return num.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + ' %';
}

/**
 * Escapa strings contra XSS ao interpolar em HTML.
 * @param {string} str 
 * @returns {string}
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ============================================================================
// 5. SISTEMA DE NOTIFICAÇÕES TOAST (INDUSTRIAL INTEGRITY)
// ============================================================================

/**
 * Exibe notificação toast estilo industrial no canto superior direito.
 * @param {string} mensagem - Texto da mensagem
 * @param {'success'|'error'|'warning'|'info'} tipo - Tipo do toast
 * @param {number} duracaoMs - Tempo em milissegundos
 */
function showToast(mensagem, tipo = 'info', duracaoMs = 4000) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${tipo}`;
  
  const prefixo = {
    success: '[SUCESSO]',
    error: '[ERRO]',
    warning: '[ALERTA]',
    info: '[INFO]'
  }[tipo] || '[INFO]';

  toast.innerHTML = `
    <span class="mono-text" style="font-weight: 700; margin-right: 8px;">${prefixo}</span>
    <span class="toast-text">${escapeHtml(mensagem)}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.classList.add('toast-fade-out');
    setTimeout(() => {
      if (toast.parentElement) toast.parentElement.removeChild(toast);
    }, 300);
  }, duracaoMs);
}

// ============================================================================
// 6. MODAL UNIVERSAL INDUSTRIAL (0PX BORDER-RADIUS)
// ============================================================================

/**
 * Abre modal universal no container #modal-root.
 * @param {Object} options
 * @param {string} options.title - Título do cabeçalho
 * @param {string} options.content - Conteúdo HTML ou texto
 * @param {string} [options.confirmText] - Texto do botão de confirmação
 * @param {string} [options.cancelText] - Texto do botão de cancelamento
 * @param {Function} [options.onConfirm] - Callback de confirmação
 * @param {Function} [options.onCancel] - Callback de cancelamento
 * @param {'sm'|'md'|'lg'|'xl'|'full'} [options.size='md'] - Tamanho do modal
 * @param {boolean} [options.hideFooter=false] - Oculta os botões padrão de rodapé
 */
// Pilha de modais para suporte a modais empilhados (stacked modals)
const modalStack = [];

/**
 * Abre um modal com cabeçalho, corpo e rodapé personalizáveis com suporte a modais empilhados.
 * @param {Object} options - Configurações do modal
 * @param {string} [options.title='Confirmação'] - Título do modal
 * @param {string} [options.content=''] - HTML do conteúdo do corpo
 * @param {string} [options.confirmText='CONFIRMAR'] - Texto do botão de confirmação
 * @param {string} [options.cancelText='CANCELAR'] - Texto do botão de cancelamento
 * @param {Function} [options.onConfirm] - Callback de confirmação
 * @param {Function} [options.onCancel] - Callback de cancelamento
 * @param {'sm'|'md'|'lg'|'xl'|'full'} [options.size='md'] - Tamanho do modal
 * @param {boolean} [options.hideFooter=false] - Oculta os botões padrão de rodapé
 * @param {boolean} [options.showCancel=true] - Exibe ou oculta o botão de cancelamento
 */
function openModal(options = {}) {
  const modalRoot = document.getElementById('modal-root');
  if (!modalRoot) return;

  const {
    title = 'Confirmação',
    content = '',
    confirmText = 'CONFIRMAR',
    cancelText = 'CANCELAR',
    onConfirm = null,
    onCancel = null,
    size = 'md',
    hideFooter = false,
    showCancel = true
  } = options;

  const overlayId = 'modal-overlay-' + Date.now() + '-' + Math.random().toString(36).substr(2, 5);
  const zIndex = 100000 + (modalStack.length * 20);

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = overlayId;
  overlay.style.zIndex = zIndex;

  overlay.innerHTML = `
    <div class="modal-card modal-size-${size}">
      <div class="modal-header">
        <h3 class="modal-title">${escapeHtml(title)}</h3>
        <button class="modal-close-btn" title="Fechar (ESC)">✕</button>
      </div>
      <div class="modal-body">
        ${content}
      </div>
      ${!hideFooter ? `
        <div class="modal-footer">
          ${showCancel !== false ? `<button class="btn btn-secondary modal-cancel-btn">${escapeHtml(cancelText)}</button>` : ''}
          <button class="btn btn-primary modal-confirm-btn">${escapeHtml(confirmText)}</button>
        </div>
      ` : ''}
    </div>
  `;

  modalRoot.appendChild(overlay);

  const closeBtn = overlay.querySelector('.modal-close-btn');
  const cancelBtn = overlay.querySelector('.modal-cancel-btn');
  const confirmBtn = overlay.querySelector('.modal-confirm-btn');

  function fechar() {
    const idx = modalStack.indexOf(overlay);
    if (idx !== -1) {
      modalStack.splice(idx, 1);
    }
    overlay.remove();
  }

  modalStack.push(overlay);

  if (closeBtn) {
    closeBtn.addEventListener('click', () => {
      fechar();
      if (onCancel) onCancel();
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener('click', () => {
      fechar();
      if (onCancel) onCancel();
    });
  }

  if (confirmBtn) {
    confirmBtn.addEventListener('click', async () => {
      if (onConfirm) {
        const ret = await onConfirm();
        if (ret !== false) fechar();
      } else {
        fechar();
      }
    });
  }
}

/**
 * Fecha o modal ativo no topo da pilha.
 */
function closeModal() {
  if (modalStack.length > 0) {
    const topo = modalStack.pop();
    if (topo) topo.remove();
  } else {
    const modalRoot = document.getElementById('modal-root');
    if (modalRoot) modalRoot.innerHTML = '';
  }
}

// ============================================================================
// 7. OUVIDO GLOBAL DE EVENTOS (DELEGAÇÃO NO DOCUMENT)
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  // Inicializa campos de moeda ATM existentes na tela
  document.querySelectorAll('input[data-mask="moeda-atm"]').forEach((input) => {
    if (!input.value) {
      input.value = 'R$ 0,00';
    } else {
      aplicarMascaraMoedaATM(input);
    }
  });
});

// Listener global de digitação (input)
document.addEventListener('input', (event) => {
  const target = event.target;
  if (!target || !target.tagName) return;

  const tag = target.tagName.toUpperCase();
  const type = (target.type || '').toLowerCase();

  // 1. Tratamento de Máscaras Especiais
  const maskType = target.dataset.mask;

  if (maskType === 'moeda-atm') {
    aplicarMascaraMoedaATM(target);
    return;
  }

  if (maskType === 'cpf-cnpj') {
    target.value = formatarCpfCnpjDinamico(target.value);
    return;
  }

  if (maskType === 'telefone') {
    target.value = formatarTelefoneDinamico(target.value);
    return;
  }

  if (maskType === 'cep') {
    target.value = formatarCep(target.value);
    return;
  }

  if (maskType === 'placa') {
    target.value = formatarPlacaVeiculo(target.value);
    return;
  }

  if (maskType === 'chave-nfe') {
    target.value = formatarChaveAcessoNfe(target.value);
    return;
  }

  if (maskType === 'linha-boleto') {
    target.value = formatarLinhaDigitavelBoleto(target.value);
    return;
  }

  // 2. Tratamento Universal de Uppercase sem Acentos para Textos Livres
  if ((tag === 'INPUT' && type === 'text') || tag === 'TEXTAREA') {
    // Ignora e-mail, senha, campos explicitamente marcados como data-no-transform ou com máscaras específicas
    if (target.dataset.noTransform || type === 'email' || type === 'password' || maskType) {
      return;
    }

    const start = target.selectionStart;
    const end = target.selectionEnd;
    const valorOriginal = target.value;
    const valorSanitizado = sanitizarTextoEmTempoReal(valorOriginal);

    if (valorOriginal !== valorSanitizado) {
      target.value = valorSanitizado;
      if (start !== null && end !== null) {
        target.setSelectionRange(start, end);
      }
    }
  }
});

// Listener global de colagem (paste)
document.addEventListener('paste', (event) => {
  const target = event.target;
  if (!target || !target.tagName) return;

  const maskType = target.dataset.mask;
  if (maskType === 'moeda-atm') {
    setTimeout(() => aplicarMascaraMoedaATM(target), 0);
    return;
  }
  if (maskType === 'cpf-cnpj') {
    setTimeout(() => { target.value = formatarCpfCnpjDinamico(target.value); }, 0);
    return;
  }
  if (maskType === 'telefone') {
    setTimeout(() => { target.value = formatarTelefoneDinamico(target.value); }, 0);
    return;
  }
  if (maskType === 'chave-nfe') {
    setTimeout(() => { target.value = formatarChaveAcessoNfe(target.value); }, 0);
    return;
  }
});

// ============================================================================
// 12. COMBOBOX AUTOCOMPLETE PESQUISÁVEL INDUSTRIAL
// ============================================================================

/**
 * Transforma um <select> nativo em uma combobox pesquisável com autocomplete,
 * pesquisa rápida de alta performance, navegação por teclado e sem cantos arredondados.
 * @param {HTMLSelectElement} selectEl 
 * @param {Object} opts 
 * @returns {Object} Instância com método refresh() e destroy()
 */
function initSearchableSelect(selectEl, opts = {}) {
  if (!selectEl) return null;
  if (selectEl._emcCombobox) {
    selectEl._emcCombobox.refresh();
    return selectEl._emcCombobox;
  }

  const placeholder = opts.placeholder || selectEl.getAttribute('placeholder') || 'SELECIONE OU PESQUISE...';

  // Cria estrutura da Combobox
  const container = document.createElement('div');
  container.className = 'emc-combobox';
  if (selectEl.id) container.dataset.for = selectEl.id;

  const trigger = document.createElement('div');
  trigger.className = 'emc-combobox-trigger';
  trigger.tabIndex = 0;

  const triggerText = document.createElement('span');
  triggerText.className = 'emc-combobox-trigger-text';
  
  const triggerArrow = document.createElement('span');
  triggerArrow.className = 'emc-combobox-trigger-arrow';
  triggerArrow.textContent = '▼';

  trigger.appendChild(triggerText);
  trigger.appendChild(triggerArrow);

  const dropdown = document.createElement('div');
  dropdown.className = 'emc-combobox-dropdown';

  const searchWrapper = document.createElement('div');
  searchWrapper.className = 'emc-combobox-search-wrapper';

  const searchInput = document.createElement('input');
  searchInput.type = 'text';
  searchInput.className = 'emc-combobox-search';
  searchInput.placeholder = 'DIGITE PARA FILTRAR...';
  searchWrapper.appendChild(searchInput);

  dropdown.appendChild(searchWrapper);

  // Ação integrada (ex: + NOVO CADASTRO)
  if (opts.action && opts.action.label) {
    const actionEl = document.createElement('div');
    actionEl.className = 'emc-combobox-action';
    actionEl.innerHTML = `<span>${escapeHtml(opts.action.label)}</span>`;
    actionEl.addEventListener('click', (e) => {
      e.stopPropagation();
      fecharDropdown();
      if (typeof opts.action.onClick === 'function') {
        opts.action.onClick(searchInput.value.trim());
      }
    });
    dropdown.appendChild(actionEl);
  }

  const optionsList = document.createElement('ul');
  optionsList.className = 'emc-combobox-options';
  dropdown.appendChild(optionsList);

  // Insere container antes do select nativo e oculta o select
  selectEl.style.display = 'none';
  selectEl.parentNode.insertBefore(container, selectEl);
  container.appendChild(trigger);
  container.appendChild(dropdown);

  let itens = [];
  let itemAtivoIndex = -1;

  function extrairOpcoes() {
    itens = [];
    const options = selectEl.querySelectorAll('option');
    options.forEach((opt, idx) => {
      itens.push({
        index: idx,
        value: opt.value,
        text: opt.textContent.trim(),
        selected: opt.selected,
        disabled: opt.disabled
      });
    });
  }

  function atualizarTriggerText() {
    const selOpt = selectEl.options[selectEl.selectedIndex];
    if (selOpt && selOpt.value !== '') {
      triggerText.textContent = selOpt.textContent.trim();
      triggerText.style.color = 'var(--color-on-surface)';
    } else {
      triggerText.textContent = selOpt ? selOpt.textContent.trim() : placeholder;
      triggerText.style.color = 'var(--color-on-surface-variant)';
    }
  }

  function renderizarOpcoes(filtro = '') {
    optionsList.innerHTML = '';
    const filtroUpper = sanitizarTextoEmTempoReal(filtro);
    let encontrados = 0;

    itens.forEach((it, idx) => {
      const textUpper = sanitizarTextoEmTempoReal(it.text);
      if (!filtroUpper || textUpper.includes(filtroUpper)) {
        encontrados++;
        const li = document.createElement('li');
        li.className = 'emc-combobox-item';
        if (it.selected) li.classList.add('selected');
        li.textContent = it.text;
        li.dataset.index = idx;
        li.dataset.value = it.value;

        li.addEventListener('click', (e) => {
          e.stopPropagation();
          selecionarItem(it.value);
        });

        optionsList.appendChild(li);
      }
    });

    if (encontrados === 0) {
      const noRes = document.createElement('li');
      noRes.className = 'emc-combobox-no-results';
      if (opts.action && opts.action.label) {
        noRes.innerHTML = `
          <div>NENHUM RESULTADO ENCONTRADO</div>
          <button type="button" class="btn btn-secondary btn-sm emc-combobox-no-res-btn" style="margin-top: 8px; font-size: 11px; padding: 4px 10px;">
            ${escapeHtml(opts.action.label)}
          </button>
        `;
        noRes.querySelector('.emc-combobox-no-res-btn')?.addEventListener('click', (e) => {
          e.stopPropagation();
          fecharDropdown();
          if (typeof opts.action.onClick === 'function') {
            opts.action.onClick(searchInput.value.trim());
          }
        });
      } else {
        noRes.textContent = 'NENHUM RESULTADO ENCONTRADO';
      }
      optionsList.appendChild(noRes);
    }
  }

  function selecionarItem(val) {
    selectEl.value = val;
    extrairOpcoes();
    atualizarTriggerText();
    fecharDropdown();
    // Dispara evento change no select nativo
    selectEl.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function abrirDropdown() {
    document.querySelectorAll('.emc-combobox.open').forEach(c => {
      if (c !== container) c.classList.remove('open');
    });

    container.classList.add('open');
    searchInput.value = '';
    renderizarOpcoes();
    setTimeout(() => searchInput.focus(), 50);
  }

  function fecharDropdown() {
    container.classList.remove('open');
    itemAtivoIndex = -1;
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    if (container.classList.contains('open')) {
      fecharDropdown();
    } else {
      abrirDropdown();
    }
  });

  trigger.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
      e.preventDefault();
      abrirDropdown();
    }
  });

  searchInput.addEventListener('input', (e) => {
    renderizarOpcoes(e.target.value);
  });

  searchInput.addEventListener('keydown', (e) => {
    const listItems = optionsList.querySelectorAll('.emc-combobox-item');
    if (e.key === 'Escape') {
      fecharDropdown();
      trigger.focus();
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (listItems.length > 0) {
        itemAtivoIndex = (itemAtivoIndex + 1) % listItems.length;
        destacarItem(listItems);
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (listItems.length > 0) {
        itemAtivoIndex = (itemAtivoIndex - 1 + listItems.length) % listItems.length;
        destacarItem(listItems);
      }
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (itemAtivoIndex >= 0 && listItems[itemAtivoIndex]) {
        listItems[itemAtivoIndex].click();
      } else if (listItems.length === 1) {
        listItems[0].click();
      }
    }
  });

  function destacarItem(listItems) {
    listItems.forEach((li, i) => {
      li.classList.toggle('active', i === itemAtivoIndex);
      if (i === itemAtivoIndex) {
        li.scrollIntoView({ block: 'nearest' });
      }
    });
  }

  // Fecha ao clicar fora
  document.addEventListener('click', (e) => {
    if (!container.contains(e.target)) {
      fecharDropdown();
    }
  });

  // Inicializa dados
  extrairOpcoes();
  atualizarTriggerText();

  const instancia = {
    refresh() {
      extrairOpcoes();
      atualizarTriggerText();
      renderizarOpcoes(searchInput.value);
    },
    setValue(val) {
      selecionarItem(val);
    },
    updateOptions(newHtml, selectedValue = null) {
      selectEl.innerHTML = newHtml;
      if (selectedValue !== null && selectedValue !== undefined) {
        selectEl.value = selectedValue;
      }
      extrairOpcoes();
      atualizarTriggerText();
      renderizarOpcoes();
    },
    destroy() {
      container.remove();
      selectEl.style.display = '';
      delete selectEl._emcCombobox;
    }
  };

  selectEl._emcCombobox = instancia;
  return instancia;
}

/**
 * Inicializa uma Combobox Multi-Seleção com Flags (Checkboxes) no padrão Industrial Integrity.
 * Permite selecionar 1 ou N opções simultaneamente.
 * @param {HTMLElement} targetEl - Elemento select ou container div
 * @param {Object} opts - Opções de configuração
 * @param {string} [opts.placeholder='TODOS'] - Texto exibido quando nenhuma opção específica estiver marcada
 * @param {string} [opts.singularLabel='SELECIONADO'] - Sufixo quando apenas 1 item estiver marcado
 * @param {string} [opts.prefix=''] - Prefixo no trigger quando múltiplos selecionados (ex: 'STATUS')
 * @param {Array<{value: string, label: string, selected?: boolean}>} [opts.items] - Itens caso não seja select
 * @param {Function} [opts.onChange] - Callback (selectedValues, selectedLabels) => {}
 * @returns {Object} Instância com getValues(), setValues(), refresh(), destroy()
 */
function initMultiSelectCombobox(targetEl, opts = {}) {
  if (!targetEl) return null;
  if (targetEl._emcMultiSelect) {
    targetEl._emcMultiSelect.refresh();
    return targetEl._emcMultiSelect;
  }

  const isSelect = targetEl.tagName === 'SELECT';
  const placeholder = opts.placeholder || targetEl.getAttribute('placeholder') || 'TODOS';
  const onChangeCallback = typeof opts.onChange === 'function' ? opts.onChange : null;

  // Cria estrutura da Combobox Multi-Seleção
  const container = document.createElement('div');
  container.className = 'emc-multiselect';
  if (targetEl.id) container.dataset.for = targetEl.id;
  if (opts.width) container.style.width = opts.width;

  const trigger = document.createElement('div');
  trigger.className = 'emc-multiselect-trigger';
  trigger.tabIndex = 0;

  const triggerText = document.createElement('span');
  triggerText.className = 'emc-multiselect-trigger-text';

  const triggerArrow = document.createElement('span');
  triggerArrow.className = 'emc-multiselect-trigger-arrow';
  triggerArrow.textContent = '▼';

  trigger.appendChild(triggerText);
  trigger.appendChild(triggerArrow);

  const dropdown = document.createElement('div');
  dropdown.className = 'emc-multiselect-dropdown';

  // Cabeçalho de Ações Rápidas (Todos / Limpar)
  const header = document.createElement('div');
  header.className = 'emc-multiselect-header';

  const btnMarcarTodos = document.createElement('button');
  btnMarcarTodos.type = 'button';
  btnMarcarTodos.textContent = '✓ TODOS';
  btnMarcarTodos.title = 'Marcar todas as opções';

  const btnLimpar = document.createElement('button');
  btnLimpar.type = 'button';
  btnLimpar.textContent = '✕ LIMPAR';
  btnLimpar.title = 'Desmarcar todas as opções';

  header.appendChild(btnMarcarTodos);
  header.appendChild(btnLimpar);
  dropdown.appendChild(header);

  const optionsList = document.createElement('ul');
  optionsList.className = 'emc-multiselect-options';
  dropdown.appendChild(optionsList);

  if (isSelect) {
    targetEl.style.setProperty('display', 'none', 'important');
    targetEl.parentNode.insertBefore(container, targetEl);
  } else {
    targetEl.appendChild(container);
  }

  container.appendChild(trigger);
  container.appendChild(dropdown);

  let itens = [];

  function extrairOpcoes() {
    itens = [];
    if (isSelect) {
      const options = targetEl.querySelectorAll('option');
      options.forEach((opt) => {
        if (opt.value !== '') {
          itens.push({
            value: opt.value,
            label: opt.textContent.trim(),
            selected: opt.selected
          });
        }
      });
    } else if (Array.isArray(opts.items)) {
      itens = opts.items.map(it => ({
        value: String(it.value),
        label: it.label || it.text || String(it.value),
        selected: !!it.selected
      }));
    }
  }

  function getSelectedValues() {
    return itens.filter(it => it.selected).map(it => it.value);
  }

  function getSelectedLabels() {
    return itens.filter(it => it.selected).map(it => it.label);
  }

  function atualizarTriggerText() {
    const selecionados = itens.filter(it => it.selected);
    if (selecionados.length === 0) {
      triggerText.textContent = placeholder;
      triggerText.style.color = 'var(--color-on-surface-variant)';
      container.title = placeholder;
    } else if (selecionados.length === 1) {
      triggerText.textContent = selecionados[0].label;
      triggerText.style.color = 'var(--color-on-surface)';
      container.title = selecionados[0].label;
    } else if (selecionados.length === itens.length && itens.length > 1) {
      triggerText.textContent = opts.allSelectedText || placeholder;
      triggerText.style.color = 'var(--color-on-surface)';
      container.title = selecionados.map(s => s.label).join(', ');
    } else {
      const labelPrefix = opts.prefix ? `${opts.prefix}: ` : '';
      triggerText.textContent = `${labelPrefix}${selecionados.length} SELECIONADOS`;
      triggerText.style.color = 'var(--color-rust-orange-bright)';
      container.title = selecionados.map(s => s.label).join(', ');
    }
  }

  function sincronizarComSelectNativo() {
    if (isSelect) {
      const options = targetEl.querySelectorAll('option');
      options.forEach(opt => {
        const item = itens.find(it => it.value === opt.value);
        if (item) {
          opt.selected = item.selected;
        } else if (opt.value === '') {
          opt.selected = itens.every(it => !it.selected);
        }
      });
      targetEl.dispatchEvent(new Event('change', { bubbles: true }));
    }
    if (onChangeCallback) {
      onChangeCallback(getSelectedValues(), getSelectedLabels());
    }
  }

  function renderizarLista() {
    optionsList.innerHTML = '';
    itens.forEach((it) => {
      const li = document.createElement('li');
      li.className = 'emc-multiselect-item' + (it.selected ? ' selected' : '');

      const chk = document.createElement('input');
      chk.type = 'checkbox';
      chk.checked = it.selected;

      const span = document.createElement('span');
      span.textContent = it.label;

      li.appendChild(chk);
      li.appendChild(span);

      li.addEventListener('click', (e) => {
        if (e.target !== chk) {
          chk.checked = !chk.checked;
        }
        it.selected = chk.checked;
        li.classList.toggle('selected', it.selected);
        atualizarTriggerText();
        sincronizarComSelectNativo();
      });

      optionsList.appendChild(li);
    });
  }

  btnMarcarTodos.addEventListener('click', (e) => {
    e.stopPropagation();
    itens.forEach(it => it.selected = true);
    renderizarLista();
    atualizarTriggerText();
    sincronizarComSelectNativo();
  });

  btnLimpar.addEventListener('click', (e) => {
    e.stopPropagation();
    itens.forEach(it => it.selected = false);
    renderizarLista();
    atualizarTriggerText();
    sincronizarComSelectNativo();
  });

  function abrirDropdown() {
    document.querySelectorAll('.emc-combobox.open, .emc-multiselect.open').forEach(c => {
      if (c !== container) c.classList.remove('open');
    });
    container.classList.add('open');
  }

  function fecharDropdown() {
    container.classList.remove('open');
  }

  trigger.addEventListener('click', (e) => {
    e.stopPropagation();
    if (container.classList.contains('open')) {
      fecharDropdown();
    } else {
      abrirDropdown();
    }
  });

  trigger.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ' || e.key === 'ArrowDown') {
      e.preventDefault();
      abrirDropdown();
    } else if (e.key === 'Escape') {
      fecharDropdown();
    }
  });

  document.addEventListener('click', (e) => {
    if (!container.contains(e.target)) {
      fecharDropdown();
    }
  });

  extrairOpcoes();
  renderizarLista();
  atualizarTriggerText();

  const instancia = {
    getValues: getSelectedValues,
    getLabels: getSelectedLabels,
    setValues(vals) {
      const arr = Array.isArray(vals) ? vals.map(String) : [String(vals)];
      itens.forEach(it => {
        it.selected = arr.includes(it.value);
      });
      renderizarLista();
      atualizarTriggerText();
      sincronizarComSelectNativo();
    },
    setItems(novosItens) {
      opts.items = novosItens;
      extrairOpcoes();
      renderizarLista();
      atualizarTriggerText();
    },
    refresh() {
      extrairOpcoes();
      renderizarLista();
      atualizarTriggerText();
    },
    destroy() {
      container.remove();
      if (isSelect) targetEl.style.display = '';
      delete targetEl._emcMultiSelect;
    }
  };

  targetEl._emcMultiSelect = instancia;
  return instancia;
}

/**
 * Aplica máscaras imediatas em todos os inputs com data-mask contidos em um elemento/container.
 */
function aplicarMascarasEmContainer(container = document) {
  if (!container) return;
  container.querySelectorAll('input[data-mask]').forEach((input) => {
    const maskType = input.dataset.mask;
    if (!input.value) return;

    if (maskType === 'cpf-cnpj') {
      input.value = formatarCpfCnpjDinamico(input.value);
    } else if (maskType === 'telefone') {
      input.value = formatarTelefoneDinamico(input.value);
    } else if (maskType === 'moeda-atm') {
      aplicarMascaraMoedaATM(input);
    } else if (maskType === 'cep') {
      input.value = formatarCep(input.value);
    } else if (maskType === 'placa') {
      input.value = formatarPlacaVeiculo(input.value);
    } else if (maskType === 'chave-nfe') {
      input.value = formatarChaveAcessoNfe(input.value);
    } else if (maskType === 'linha-boleto') {
      input.value = formatarLinhaDigitavelBoleto(input.value);
    }
  });
}

/**
 * Renderiza uma barra de paginação padronizada (Industrial Integrity) em um container.
 */
function renderPagination({
  container,
  currentPage = 1,
  pageSize = 25,
  totalCount = 0,
  pageSizeOptions = [25, 50, 100],
  itemLabel = 'ITENS',
  onPageChange,
  onPageSizeChange
}) {
  const el = typeof container === 'string' ? document.querySelector(container) : container;
  if (!el) return;

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const safePage = Math.min(Math.max(1, currentPage), totalPages);

  const startRecord = totalCount === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const endRecord = Math.min(safePage * pageSize, totalCount);

  // Calcula janela inteligente de páginas a exibir
  const pages = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (safePage > 4) {
      pages.push('...');
    }
    const startRange = Math.max(2, safePage - 1);
    const endRange = Math.min(totalPages - 1, safePage + 1);

    for (let i = startRange; i <= endRange; i++) {
      if (!pages.includes(i)) pages.push(i);
    }

    if (safePage < totalPages - 3) {
      pages.push('...');
    }
    if (!pages.includes(totalPages)) {
      pages.push(totalPages);
    }
  }

  let pagesHtml = '';
  pages.forEach((p) => {
    if (p === '...') {
      pagesHtml += `<span class="emc-pagination-ellipsis">...</span>`;
    } else if (p === safePage) {
      pagesHtml += `<button type="button" class="btn btn-primary btn-sm emc-pagination-btn active" data-page="${p}">${p}</button>`;
    } else {
      pagesHtml += `<button type="button" class="btn btn-secondary btn-sm emc-pagination-btn" data-page="${p}">${p}</button>`;
    }
  });

  const sizeSelectHtml = pageSizeOptions && pageSizeOptions.length ? `
    <div class="emc-pagination-size-wrapper">
      <span style="color: var(--color-on-surface-variant); font-size: 11px;">POR PÁG:</span>
      <select class="form-control form-control-sm emc-pagination-size-select">
        ${pageSizeOptions.map(opt => `<option value="${opt}" ${opt === pageSize ? 'selected' : ''}>${opt}</option>`).join('')}
      </select>
    </div>
  ` : '';

  el.innerHTML = `
    <div class="emc-pagination">
      <div class="emc-pagination-info">
        <span>EXIBINDO <strong>${startRecord}</strong> A <strong>${endRecord}</strong> DE <strong>${totalCount}</strong> ${escapeHtml(itemLabel.toUpperCase())}</span>
        ${sizeSelectHtml}
      </div>

      <div class="emc-pagination-controls">
        <button type="button" class="btn btn-secondary btn-sm emc-pagination-btn emc-btn-first" data-page="1" ${safePage <= 1 ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''} title="Primeira Página">«</button>
        <button type="button" class="btn btn-secondary btn-sm emc-pagination-btn emc-btn-prev" data-page="${safePage - 1}" ${safePage <= 1 ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''} title="Página Anterior">‹</button>
        ${pagesHtml}
        <button type="button" class="btn btn-secondary btn-sm emc-pagination-btn emc-btn-next" data-page="${safePage + 1}" ${safePage >= totalPages ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''} title="Próxima Página">›</button>
        <button type="button" class="btn btn-secondary btn-sm emc-pagination-btn emc-btn-last" data-page="${totalPages}" ${safePage >= totalPages ? 'disabled style="opacity: 0.4; cursor: not-allowed;"' : ''} title="Última Página">»</button>
        <span class="emc-pagination-counter">PÁG. <strong>${safePage}</strong> DE <strong>${totalPages}</strong></span>
      </div>
    </div>
  `;

  // Event Listeners dos botões de página
  el.querySelectorAll('.emc-pagination-btn[data-page]').forEach((btn) => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (btn.hasAttribute('disabled')) return;
      const targetPage = parseInt(btn.dataset.page, 10);
      if (targetPage && targetPage !== safePage && typeof onPageChange === 'function') {
        onPageChange(targetPage);
      }
    });
  });

  // Event Listener do seletor de tamanho de página
  const sizeSelect = el.querySelector('.emc-pagination-size-select');
  if (sizeSelect && typeof onPageSizeChange === 'function') {
    sizeSelect.addEventListener('change', (e) => {
      const newSize = parseInt(e.target.value, 10);
      if (newSize) {
        onPageSizeChange(newSize);
      }
    });
  }
}

// Disponibilização no escopo global para consumo da SPA
window.EMCUtils = {
  sanitizarTextoEmTempoReal,
  extrairApenasDigitos,
  validarCpf,
  validarCnpj,
  validarPlacaVeiculo,
  formatarCentavosParaMoedaATM,
  converterMoedaATMParaFloat,
  aplicarMascaraMoedaATM,
  formatarCpfCnpjDinamico,
  formatarTelefoneDinamico,
  formatarCep,
  formatarPlacaVeiculo,
  formatarChaveAcessoNfe,
  formatarLinhaDigitavelBoleto,
  formatarMoeda,
  formatarDataPtBr,
  formatarDataHoraPtBr,
  formatarHoras,
  formatarPorcentagem,
  escapeHtml,
  showToast,
  openModal,
  closeModal,
  initSearchableSelect,
  initMultiSelectCombobox,
  aplicarMascarasEmContainer,
  renderPagination
};
