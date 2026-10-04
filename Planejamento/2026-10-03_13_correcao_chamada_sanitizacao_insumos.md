# Implementation Plan - Correção da Chamada de Sanitização em Compras (Uso de `sanitizarTextoEmTempoReal`)

- **Data:** 2026-10-03
- **Autor:** Antigravity (Pair Programming IA)
- **Status:** Concluído
- **Fase de Referência:** Fase 14.5 (UX, Compras e Cadastros)
- **Versão do PWA Alvo:** v4.44 (Incremento de v4.43 -> v4.44)
- **Registro de Aprovação:** Aprovado explicitamente pelo usuário via `Proceed` em 2026-10-03 22:51:02-03:00.

---

## 1. Contexto e Diagnóstico

### 1.1 O Erro
Ao clicar em **CADASTRAR E SELECIONAR** no modal de cadastro rápido de insumo, ocorria o erro:
```text
window.EMCUtils.sanitizarTextoMaiusculo is not a function
```

### 1.2 Causa Raiz
Houve uma confusão de nomenclatura entre ecossistemas:
- **No Backend (Python):** a função canônica chama-se `sanitizar_texto_maiusculo` (`backend/core/utils.py`).
- **No Frontend (JavaScript):** a função canônica padrão de todo o sistema chama-se **`window.EMCUtils.sanitizarTextoEmTempoReal`** (`frontend/assets/js/utils.js`), já amplamente utilizada em `cadastros-view.js`, comboboxes e máscaras.

No arquivo `frontend/assets/js/views/compras-view.js`, a linha 741 foi escrita erroneamente com `window.EMCUtils.sanitizarTextoMaiusculo(nome)`.

---

## 2. Decisão Técnica Correta

1. **Intocabilidade de `utils.js`:**
   - O arquivo de utilitários globais (`utils.js`) permanece **100% inalterado**, preservando a assinatura original, canônica e estável utilizada em toda a aplicação.
2. **Correção Direta na View (`compras-view.js`):**
   - Corrigir a linha 741 de `frontend/assets/js/views/compras-view.js` para chamar a função correta do frontend:
     ```javascript
     nome: window.EMCUtils.sanitizarTextoEmTempoReal(nome),
     ```
3. **Versionamento PWA (Regra 12):**
   - Atualizar `CACHE_NAME` de `emc-soldas-v4.43` para `emc-soldas-v4.44` em `frontend/sw.js`.
   - Atualizar os sufixos de cache-busting nos scripts e estilos para `?v=4.44` em `frontend/index.html`.
4. **Governança e Homologação:**
   - Testar sintaxe com `node -c`.
   - Rodar suíte de testes de `apps.compras`.
   - Atualizar `docs/STATUS.md` e atualizar o plano em `Planejamento/2026-10-03_13_correcao_chamada_sanitizacao_insumos.md`.
   - Commit semântico (Regra 13): `fix(compras): corrigir chamada para sanitizarTextoEmTempoReal no cadastro de insumo`.

---

## 3. Arquivos Afetados

| Arquivo | Ação | Descrição |
| :--- | :--- | :--- |
| `frontend/assets/js/views/compras-view.js` | Modificar | Trocar `sanitizarTextoMaiusculo` por `sanitizarTextoEmTempoReal`. |
| `frontend/sw.js` | Modificar | Incrementar `CACHE_NAME` para `emc-soldas-v4.44` (Regra 12). |
| `frontend/index.html` | Modificar | Atualizar sufixos para `?v=4.44` (Regra 12). |
| `Planejamento/2026-10-03_13_correcao_chamada_sanitizacao_insumos.md` | Criar | Arquivamento do plano e registro de governança. |
| `docs/STATUS.md` | Modificar | Registro da versão v4.44. |

---

## 4. Plano de Verificação e Testes

1. `node -c frontend/assets/js/views/compras-view.js`
2. `python backend/manage.py test apps.compras`
3. Teste no navegador (com `Ctrl + Shift + R`):
   - Acessar Compras -> + Lançar Nota de Compra -> + NOVO INSUMO.
   - Preencher nome com letras minúsculas ou acentos (ex: `eletrodo de aco 2.5mm`).
   - Clicar em **CADASTRAR E SELECIONAR**.
   - Conferir se o insumo é salvo com sucesso em maiúsculas limpas (`ELETRODO DE ACO 2.5MM`) e selecionado na nota fiscal.

---

## 5. Relatório de Execução e Evidências

1. **Modificações Realizadas:**
   - `frontend/assets/js/views/compras-view.js`: Corrigida a chamada da linha 741 para utilizar a função canônica original `window.EMCUtils.sanitizarTextoEmTempoReal(nome)`.
   - `frontend/assets/js/utils.js`: Permaneceu 100% inalterado, preservando a pureza e estabilidade do módulo central.
   - `frontend/sw.js`: Versão de cache atualizada para `emc-soldas-v4.44`.
   - `frontend/index.html`: Sufixos de cache-busting atualizados para `?v=4.44`.
2. **Validação Técnica:**
   - Validação de sintaxe JS (`node -c`) executada e aprovada com código 0.
   - 28 testes de `apps.compras` executados e aprovados com 100% de sucesso.
3. **Governança:**
   - `docs/STATUS.md` atualizado com o registro da entrega v4.44.
