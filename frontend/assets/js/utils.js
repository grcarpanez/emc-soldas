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
function formatarTelefoneDinamico(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 11);

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
 * Formata Placa de Veículo (Antiga AAA-0000 ou Mercosul AAA0A00) em Uppercase.
 * @param {string} valor 
 * @returns {string}
 */
function formatarPlacaVeiculo(valor) {
  if (!valor) return '';
  const limpo = sanitizarTextoEmTempoReal(valor).replace(/[^A-Z0-9]/g, '').slice(0, 7);

  if (limpo.length > 3) {
    // Se o 5º caractere for número (padrão antigo AAA-0000), insere hífen
    const quintoChar = limpo[4];
    if (quintoChar && /\d/.test(quintoChar)) {
      return limpo.slice(0, 3) + '-' + limpo.slice(3);
    }
  }
  return limpo;
}

/**
 * Formata Chave de Acesso NFe/NFCe (44 dígitos em grupos de 4).
 * @param {string} valor 
 * @returns {string}
 */
function formatarChaveAcessoNfe(valor) {
  const digitos = extrairApenasDigitos(valor).slice(0, 44);
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
    hideFooter = false
  } = options;

  modalRoot.innerHTML = `
    <div class="modal-overlay" id="active-modal-overlay">
      <div class="modal-card modal-size-${size}">
        <div class="modal-header">
          <h3 class="modal-title">${escapeHtml(title)}</h3>
          <button class="btn btn-ghost btn-sm" id="modal-close-btn" title="Fechar">X</button>
        </div>
        <div class="modal-body" id="active-modal-body">
          ${content}
        </div>
        ${!hideFooter ? `
          <div class="modal-footer">
            <button class="btn btn-secondary" id="modal-cancel-btn">${escapeHtml(cancelText)}</button>
            <button class="btn btn-primary" id="modal-confirm-btn">${escapeHtml(confirmText)}</button>
          </div>
        ` : ''}
      </div>
    </div>
  `;

  const overlay = document.getElementById('active-modal-overlay');
  const closeBtn = document.getElementById('modal-close-btn');
  const cancelBtn = document.getElementById('modal-cancel-btn');
  const confirmBtn = document.getElementById('modal-confirm-btn');

  function fechar() {
    modalRoot.innerHTML = '';
  }

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
 * Fecha o modal ativo.
 */
function closeModal() {
  const modalRoot = document.getElementById('modal-root');
  if (modalRoot) modalRoot.innerHTML = '';
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

// Disponibilização no escopo global para consumo da SPA
window.EMCUtils = {
  sanitizarTextoEmTempoReal,
  extrairApenasDigitos,
  validarCpf,
  validarCnpj,
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
  closeModal
};
