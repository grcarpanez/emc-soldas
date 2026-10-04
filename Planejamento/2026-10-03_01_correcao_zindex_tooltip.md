# Plano de Implementação: Correção do Z-Index das Tooltips

## 1. Metadados
- **Data:** 2026-10-03
- **Autor:** IA Assistente (Antigravity)
- **Status:** Concluído
- **Registro de Aprovação:** Proceed concedido.

## 2. Contexto e Objetivos
O usuário relatou que as tooltips do sistema estão sendo exibidas atrás de modais. A análise técnica confirmou que a classe `.chart-tooltip` possui um `z-index` de 1000, enquanto elementos como `.modal-overlay`, `.modal-card` e dropdowns possuem `z-index` variando de 9999 a 100050.
O objetivo é garantir que as tooltips customizadas sempre sobreponham qualquer outro elemento visual da tela, ajustando seu z-index para um valor superior a todos os demais componentes.

## 3. Decisões Técnicas e Arquiteturais
- O `z-index` da classe `.chart-tooltip` será alterado para `999999`.
- Como a modificação envolve um arquivo CSS e a arquitetura é um PWA, é obrigatório incrementar a versão do Service Worker (`sw.js`) e os parâmetros de *cache-busting* no shell da SPA (`index.html`) para garantir que os usuários recebam a folha de estilos atualizada imediatamente.

## 4. Arquivos a Modificar
- `frontend/assets/css/industrial-integrity.css`: Atualizar o `z-index` da `.chart-tooltip`.
- `frontend/sw.js`: Incrementar a constante `CACHE_NAME` (ex: de `vX.Y` para a próxima versão).
- `frontend/index.html`: Atualizar a query string `?v=X.Y` no `<link>` do CSS `industrial-integrity.css`.

## 5. Plano de Verificação e Testes
- Verificar visualmente no navegador se as tooltips sobrepõem corretamente qualquer janela modal ativa.
- Confirmar se o carregamento em um navegador atualiza o cache corretamente via *cache-busting* sem necessidade de forçar a limpeza manual do cache além de recarregar a página (Ctrl+Shift+R).

## 6. Relatório de Execução (Pós-conclusão)
- (A ser preenchido após a conclusão).
