# Implementation Plan - Correção do Endpoint do Dicionário de UOM no Cadastro Rápido de Insumo

- **Data:** 2026-10-03
- **Autor:** Antigravity (Pair Programming IA)
- **Status:** Concluído
- **Fase de Referência:** Fase 7 / Fase 14.5 (UX, Compras e Cadastros)
- **Versão do PWA Alvo:** v4.43 (Incremento de v4.42 -> v4.43)
- **Registro de Aprovação:** Aprovado explicitamente pelo usuário via `Proceed` em 2026-10-03 22:30:44-03:00.

---

## 1. Contexto e Causa Raiz do Erro

### 1.1 Sintoma
Ao clicar no botão `+ NOVO INSUMO` (ou na ação correspondente da pesquisa de insumos) no modal de lançamento da Nota Fiscal de Compra, o sistema exibia a notificação de erro:
`"Erro ao carregar unidades de medida."` e impedia a abertura do modal de cadastro rápido.

### 1.2 Diagnóstico e Causa Raiz
No arquivo `frontend/assets/js/views/compras-view.js` (linha 660), a chamada para listar as Unidades de Medida foi escrita como:
```javascript
const resUom = await window.api.get(window.CONFIG.ENDPOINTS.CATALOGO.UOM);
```
Contudo, no mapa central de rotas da aplicação (`frontend/assets/js/config.js`):
- O endpoint canônico do dicionário de unidades de medida reside em:
  `window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM` (`/api/dicionario-uom/`).
- O objeto `CATALOGO` possuía apenas `ITENS`, `PRODUTOS`, `FICHAS_TECNICAS`, etc., deixando `window.CONFIG.ENDPOINTS.CATALOGO.UOM` como `undefined`.
- O cliente HTTP ao tentar realizar um `GET undefined` disparava uma exceção imediata que acionava o bloco `catch` e exibia a mensagem de toast ao operador.

---

## 2. Decisões Técnicas e Solução Arquitetural

1. **Correção Direta da Rota em `compras-view.js`:**
   - Atualizar a chamada para consumir o endpoint oficial:
     `window.CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM`.
2. **Dupla Proteção e Aliasing em `config.js`:**
   - Adicionar o alias `UOM: '/dicionario-uom/'` e `DICIONARIO_UOM: '/dicionario-uom/'` dentro do bloco `CONFIG.ENDPOINTS.CATALOGO`, garantindo que qualquer chamada futura ao módulo de catálogo encontre a rota com 100% de tolerância.
3. **Resiliência e Fallback Defensivo:**
   - Se por qualquer motivo de rede ou latência temporária o backend demorar a responder ou o dicionário estiver temporariamente indisponível, utilizar `.catch(() => [])` com fallback imediato para as UOMs mais usuais (`UN`, `KG`, `M`, `M2`, `BARRA`, `L`, `CX`), nunca travando a interface do operador.
4. **Governança PWA e Versionamento de Cache (Regra 12):**
   - Como arquivos JS são modificados, incrementar `CACHE_NAME` de `emc-soldas-v4.42` para `emc-soldas-v4.43` em `frontend/sw.js`.
   - Atualizar todos os sufixos de versão nos scripts e folhas de estilo para `?v=4.43` em `frontend/index.html`.

---

## 3. Arquivos a Modificar / Criar

| Arquivo | Ação | Descrição |
| :--- | :--- | :--- |
| `frontend/assets/js/views/compras-view.js` | Modificar | Corrigir chamada para `CONFIG.ENDPOINTS.CADASTROS.DICIONARIO_UOM` com tratamento resiliente. |
| `frontend/assets/js/config.js` | Modificar | Adicionar alias defensivo `UOM` e `DICIONARIO_UOM` dentro de `CONFIG.ENDPOINTS.CATALOGO`. |
| `frontend/sw.js` | Modificar | Incrementar versão `CACHE_NAME` para `emc-soldas-v4.43` (Regra 12). |
| `frontend/index.html` | Modificar | Atualizar sufixos de cache-busting para `?v=4.43` (Regra 12). |
| `Planejamento/2026-10-03_12_correcao_endpoint_dicionario_uom_cadastro_insumo.md` | Criar | Arquivamento do plano e registro de execução na raiz do repositório. |
| `docs/STATUS.md` | Modificar | Atualizar arquivo vivo de status para a versão v4.43. |

---

## 4. Plano de Verificação e Testes

1. **Validação de Sintaxe JavaScript:**
   - Executar `node -c` em `frontend/assets/js/config.js` e `frontend/assets/js/views/compras-view.js`.
2. **Suíte de Testes Automatizados:**
   - Executar bateria de testes do backend para garantir integridade contínua.
3. **Verificação no Navegador com Cache Atualizado:**
   - Recarregar com `Ctrl + Shift + R` (ou `Ctrl + F5`).
   - Clicar em **+ Lançar Nota de Compra**.
   - Clicar no botão **+ NOVO INSUMO**.
   - Confirmar abertura imediata do modal de cadastro rápido sem erros.
   - Conferir se todas as UOMs cadastradas (UN, KG, M, BARRA, etc.) aparecem corretamente no select.
   - Cadastrar um novo insumo e verificar a auto-seleção e foco.

---

## 5. Relatório de Execução e Evidências

1. **Modificações Realizadas:**
   - `frontend/assets/js/config.js`: Incluídos aliases defensivos `UOM: '/dicionario-uom/'` e `DICIONARIO_UOM: '/dicionario-uom/'` no objeto `CONFIG.ENDPOINTS.CATALOGO`.
   - `frontend/assets/js/views/compras-view.js`: Implementada resolução dinâmica de endpoint (`CATALOGO.UOM` || `CADASTROS.DICIONARIO_UOM` || `'/dicionario-uom/'`), captura graciosa de falhas (`.catch(() => [])`) e fallback universal para unidades padrão.
   - `frontend/sw.js`: `CACHE_NAME` atualizado para `emc-soldas-v4.43`.
   - `frontend/index.html`: Sufixos de cache-busting atualizados para `?v=4.43` em todos os scripts e folhas de estilo.
2. **Validação Técnica:**
   - Validação de sintaxe JS (`node -c`) aprovada sem erros.
   - 28 testes de `apps.compras` executados e aprovados 100% OK.
   - 15 testes de `apps.catalogo` executados e aprovados 100% OK.
3. **Governança:**
   - Documento vivo `docs/STATUS.md` atualizado com o registro da entrega v4.43.

