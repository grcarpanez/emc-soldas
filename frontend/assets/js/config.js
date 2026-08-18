/**
 * Configurações globais da aplicação Frontend PWA (EMC Soldas).
 */

const CONFIG = {
  API_BASE_URL: '/api',
  DEFAULT_TIMEOUT_MS: 15000,
  SOFT_LOCK_TIMEOUT_MINUTES: 30,
  APP_VERSION: '1.0.0',
  ENDPOINTS: {
    AUTH: {
      LOGIN: '/auth/login/',
      LOGOUT: '/auth/logout/',
      UNLOCK_PIN: '/auth/unlock-pin/',
      SET_PIN: '/auth/set-pin/',
      FORGOT_PASSWORD: '/auth/forgot-password/',
      RESET_PASSWORD: '/auth/reset-password/',
      ME: '/auth/me/'
    },
    CADASTROS: {
      CLIENTES: '/cadastros/clientes-fornecedores/',
      EQUIPAMENTOS: '/cadastros/equipamentos/',
      DICIONARIO_UOM: '/cadastros/dicionario-uom/',
      DICIONARIO_ATRIBUTOS: '/cadastros/dicionario-atributos/',
      CONSULTA_CNPJ: '/cadastros/consulta-cnpj/'
    },
    CATALOGO: {
      ITENS: '/catalogo/itens/',
      PRODUTOS: '/catalogo/produtos/',
      FICHAS_TECNICAS: '/catalogo/fichas-tecnicas/'
    },
    ORCAMENTOS: {
      LISTA: '/orcamentos/',
      CANCELAR: '/orcamentos/{id}/cancelar/',
      PDF: '/orcamentos/{id}/pdf/'
    },
    FATURAMENTO: {
      FATURAS: '/faturamento/faturas/',
      CONTA_CORRENTE: '/faturamento/conta-corrente/',
      FATURAR: '/faturamento/faturas/{id}/faturar/',
      CANCELAR: '/faturamento/faturas/{id}/cancelar/'
    },
    FINANCEIRO: {
      LANCAMENTOS: '/financeiro/lancamentos-financeiros/',
      CONTAS: '/financeiro/contas-bancarias/',
      MEIOS_PAGAMENTO: '/financeiro/meios-pagamento/',
      REGRAS_PAGAMENTO: '/financeiro/regras-pagamento/',
      CATEGORIAS: '/financeiro/categorias-financeiras/',
      LIQUIDAR: '/financeiro/lancamentos-financeiros/{id}/liquidar/',
      ESTORNAR: '/financeiro/lancamentos-financeiros/{id}/estornar/'
    },
    DASHBOARD: {
      FLIP_CARDS: '/relatorios/dashboard/flip-cards/',
      GRAFICOS: '/relatorios/dashboard/graficos/'
    }
  }
};

window.CONFIG = CONFIG;
