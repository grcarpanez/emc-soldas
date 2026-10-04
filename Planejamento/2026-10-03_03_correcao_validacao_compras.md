# Plano de Implementação: Correção de Validação Visual do Fornecedor

## 1. Metadados
- **Data:** 2026-10-03
- **Autor:** IA Assistente (Antigravity)
- **Status:** Concluído
- **Registro de Aprovação:** Proceed concedido.

## 2. Contexto e Objetivos
O usuário percebeu que ao tentar salvar uma nota de entrada sem preencher o "Fornecedor", uma mensagem de erro é exibida (o Toast), mas o campo do fornecedor não fica destacado em vermelho, quebrando a indicação visual para o usuário.
A causa raiz é que no JavaScript (`compras-view.js`), a lógica de validação tenta encontrar o container visual da caixa de seleção buscando por um ancestral `closest('.emc-combobox-wrapper')`. No entanto, a estrutura correta criada pelo sistema injeta o componente customizado como irmão (`.emc-combobox[data-for="..."]`) e oculta o `<select>` original.

## 3. Decisões Técnicas e Arquiteturais
- Corrigir a lógica de localização do componente customizado em `compras-view.js`. O código deve buscar o container correto pela sintaxe `document.querySelector('.emc-combobox[data-for="' + fornecedorSelect.id + '"]')`.
- Limpar cache de JS incrementando a versão do PWA em `sw.js` e em `index.html`.

## 4. Arquivos a Modificar
- `frontend/assets/js/views/compras-view.js`
- `frontend/sw.js` (incremento para v4.48)
- `frontend/index.html` (incremento da query string)

## 5. Plano de Verificação e Testes
- Simular o erro internamente.
- Testar se os testes automatizados que cobrem esse arquivo continuam passando.

## 6. Relatório de Execução (Pós-conclusão)
- (A ser preenchido)
