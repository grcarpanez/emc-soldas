# Plano de Implementação: Correção do Z-Index do Toast (Aviso de Erro)

## 1. Metadados
- **Data:** 2026-10-03
- **Autor:** IA Assistente (Antigravity)
- **Status:** Concluído
- **Registro de Aprovação:** Proceed concedido.

## 2. Contexto e Objetivos
O usuário enviou uma captura de tela mostrando que o balão de erro ("preencha os campos em vermelho") está aparecendo por trás do modal de compras. Este elemento é na verdade o `.toast-container`, cujo `z-index` atual é 10000. Como os modais são renderizados via JS com `z-index` a partir de 100000, o toast fica oculto.
O objetivo é corrigir o `z-index` do `.toast-container` e também elevar preventivamente o dos dropdowns (combobox/multiselect) para que nunca sejam ocultados por modais.

## 3. Decisões Técnicas e Arquiteturais
- `.toast-container` terá o `z-index` elevado de `10000` para `999999`.
- `.emc-combobox-dropdown` e `.emc-multiselect-dropdown` terão o `z-index` elevado de `100050` para `999998`.
- Invalidação de cache via versionamento do Service Worker (`sw.js`) e `index.html`.

## 4. Arquivos a Modificar
- `frontend/assets/css/industrial-integrity.css`
- `frontend/sw.js` (incremento para v4.47)
- `frontend/index.html` (incremento da query string)

## 5. Plano de Verificação e Testes
- Os testes backend serão executados.
- Confirmar visualmente se os toasts e dropdowns aparecem sobre qualquer modal.

## 6. Relatório de Execução (Pós-conclusão)
- (A ser preenchido)
