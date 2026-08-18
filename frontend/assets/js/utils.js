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

// ============================================================================
// 4. OUVIDO GLOBAL DE EVENTOS (DELEGAÇÃO NO DOCUMENT)
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
    // Ignora e-mail, senha, campos explicitamente marcados como data-no-transform ou máscaras com lógica própria
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
});

// Disponibilização no escopo global para consumo da SPA
window.EMCUtils = {
  sanitizarTextoEmTempoReal,
  extrairApenasDigitos,
  formatarCentavosParaMoedaATM,
  converterMoedaATMParaFloat,
  aplicarMascaraMoedaATM,
  formatarCpfCnpjDinamico,
  formatarTelefoneDinamico,
  formatarCep,
  formatarPlacaVeiculo,
  formatarChaveAcessoNfe,
  formatarLinhaDigitavelBoleto
};
