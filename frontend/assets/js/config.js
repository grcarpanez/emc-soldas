const isCustomDevPort = typeof window !== 'undefined' && window.location.port && window.location.port !== '8000';
const API_BASE = isCustomDevPort 
  ? `${window.location.protocol}//${window.location.hostname}:8000/api` 
  : '/api';

const CONFIG = {
  API_BASE_URL: API_BASE,
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
      ACTIVATE_ACCOUNT: '/auth/activate-account/',
      ME: '/auth/me/'
    },
    USUARIOS: {
      LISTA: '/usuarios/',
      DETALHE: '/usuarios/{id}/',
      CONVIDAR: '/usuarios/convidar/',
      DESBLOQUEAR: '/usuarios/{id}/desbloquear/'
    },
    PERMISSOES: {
      LISTA: '/permissoes/',
      DETALHE: '/permissoes/{id}/'
    },
    CADASTROS: {
      CLIENTES: '/clientes-fornecedores/',
      EQUIPAMENTOS: '/equipamentos/',
      CLIENTE_EQUIPAMENTOS: '/cliente-equipamentos/',
      ANEXOS_CLIENTES: '/anexos-gerais-clientes/',
      DICIONARIO_UOM: '/dicionario-uom/',
      DICIONARIO_ATRIBUTOS: '/dicionario-atributos/',
      CONSULTA_CNPJ: '/utilitarios/consulta-cnpj/{cnpj}/',
      VERIFICAR_DOCUMENTO: '/utilitarios/verificar-documento/'
    },
    CATALOGO: {
      ITENS: '/itens/',
      ITEM_ATRIBUTO_VALORES: '/item-atributos-valores/',
      PRODUTOS: '/produtos/',
      FICHAS_TECNICAS: '/fichas-tecnicas/',
      ITEM_ONDE_USADO: '/itens/{id}/onde-usado/',
      PRODUTO_CUSTO_DETALHADO: '/produtos/{id}/custo-detalhado/',
      PRODUTO_ATUALIZAR_FICHA: '/produtos/{id}/atualizar-ficha-tecnica/'
    },
    COMPRAS: {
      NOTAS: '/documentos-fiscais-compra/',
      NOTA_ITENS: '/nota-compra-itens/',
      ANEXAR_ARQUIVO: '/documentos-fiscais-compra/{id}/anexar-arquivo/',
      DOWNLOAD_ANEXO: '/documentos-fiscais-compra/{id}/download-anexo/',
      HISTORICO_PRECOS: '/documentos-fiscais-compra/historico-precos/'
    },
    ORCAMENTOS: {
      LISTA: '/orcamentos/',
      DETALHE: '/orcamentos/{id}/',
      ITENS: '/orcamento-itens/',
      PROPOSTAS: '/orcamento-propostas-pagamento/',
      RENOVAR: '/orcamentos/{id}/renovar/',
      CANCELAR: '/orcamentos/{id}/cancelar/',
      GERAR_PDF: '/orcamentos/{id}/gerar-pdf/',
      VERIFICAR_INADIMPLENCIA: '/orcamentos/verificar-inadimplencia/'
    },
    FATURAMENTO: {
      FATURAS: '/faturas/',
      DETALHE: '/faturas/{id}/',
      CONTA_CORRENTE: '/faturas/conta-corrente/',
      PROPOSTAS: '/fatura-propostas-pagamento/',
      FATURAR: '/faturas/{id}/faturar/',
      CANCELAR: '/faturas/{id}/cancelar/',
      RECEBER: '/faturas/{id}/receber/',
      CORTESIA: '/faturas/{id}/cortesia/',
      GERAR_PDF: '/faturas/{id}/gerar-pdf/'
    },
    FINANCEIRO: {
      LANCAMENTOS: '/lancamentos-financeiros/',
      CONTAS_BANCARIAS: '/contas-bancarias/',
      CARTOES_CREDITO: '/cartoes-credito/',
      FATURAS_CARTAO: '/faturas-cartao/',
      FECHAR_FATURA_CARTAO: '/faturas-cartao/{id}/fechar-fatura/',
      CATEGORIAS: '/categorias-financeiras/',
      MEIOS_PAGAMENTO: '/meios-pagamento/',
      REGRAS_PAGAMENTO: '/regras-pagamento/',
      LIQUIDAR: '/lancamentos-financeiros/{id}/liquidar/',
      ESTORNAR: '/lancamentos-financeiros/{id}/estornar/',
      TRANSFERIR: '/lancamentos-financeiros/transferir/',
      CANCELAR_TITULO: '/lancamentos-financeiros/{id}/cancelar/',
      LOG_ESTORNOS: '/log-estornos/'
    },
    CONCILIACAO: {
      EXTRATOS: '/conciliacao/extratos/',
      UPLOAD_EXTRATO: '/conciliacao/upload-extrato/',
      MATCH_SUGESTOES: '/conciliacao/match-sugestoes/',
      CONFIRMAR: '/conciliacao/confirmar/',
      LANCAMENTO_RAPIDO: '/conciliacao/lancamento-rapido/',
      DIVERGENCIAS: '/conciliacao/divergencias/'
    },
    ADMINISTRACAO: {
      CONFIGURACOES_GLOBAIS: '/configuracoes-globais/',
      TESTAR_SMTP: '/configuracoes-globais/testar-smtp/',
      CONTROLE_LOGS: '/controle-arquivos-log/',
      EXPURGAR_LOGS: '/controle-arquivos-log/expurgar/',
      LOG_VIEWER: '/controle-arquivos-log/visualizar-log/',
      DOWNLOAD_LOG: '/controle-arquivos-log/download-log/',
      LIXEIRA: '/lixeira/',
      RESTAURAR_LIXEIRA: '/lixeira/{entidade}/{id}/restaurar/'
    },
    RELATORIOS: {
      DASHBOARD_FLIP_CARDS: '/dashboard/flip-cards/',
      DASHBOARD_GRAFICOS: '/dashboard/graficos/',
      DASHBOARD_FEED: '/dashboard/feed/',
      INADIMPLENCIA: '/relatorios/inadimplencia/',
      DOSSIE_CLIENTE: '/relatorios/dossie-cliente/{id}/',
      CURVA_ABC_CLIENTES: '/relatorios/curva-abc-clientes/',
      CURVA_ABC_ITENS: '/relatorios/curva-abc-itens/',
      DRE: '/relatorios/dre/',
      DIVERGENCIAS_CONCILIACAO: '/relatorios/divergencias-conciliacao/'
    }
  }
};

window.CONFIG = CONFIG;
