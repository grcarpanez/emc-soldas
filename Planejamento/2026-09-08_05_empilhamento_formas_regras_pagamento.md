# Planejamento: Reestruturação Visual e Empilhamento de Formas & Regras de Pagamento

## Metadados
- **Data:** 2026-09-08
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Aprovado via interface pelo usuário em 2026-09-08 18:49:15.

---

## 1. Contexto e Diagnóstico Visual
Na versão anterior, a aba **"FORMAS & REGRAS DE PAGAMENTO"** na Central do Administrador (`#/administracao`) posicionava os cards de **Meios de Pagamento** e **Regras Comerciais** lado a lado em duas colunas (`5fr` / `7fr`). 
A tabela de Regras Comerciais possui 9 colunas densas (`ID`, `NOME DA REGRA`, `MEIO`, `COBRANÇA`, `PARCELAS`, `PRAZOS`, `DESC. %`, `STATUS`, `AÇÕES`), resultando em esmagamento dos dados, quebra lateral e corte no botão do cabeçalho.
A decisão aprovada pelo usuário é reorganizar a interface verticalmente, empilhando os dois cards um abaixo do outro com 100% de largura.

---

## 2. Decisões Técnicas e Arquiteturais
1. **Empilhamento Vertical com 100% de Largura:**
   - **Card Superior:** MEIOS DE PAGAMENTO (100% largura, tabela limpa e confortável, `max-height: 360px`).
   - **Card Inferior:** REGRAS & CONDIÇÕES COMERCIAIS (100% largura, espaço amplo para todas as 9 colunas, botão com texto completo `+ NOVA REGRA COMERCIAL`, sem scroll horizontal forçado).
2. **Versionamento PWA (Regra Mandatória 12 do AGENTS.md):**
   - Atualização de `CACHE_NAME = 'emc-soldas-v4.0'` em `frontend/sw.js`.
   - Atualização dos sufixos de cache-busting para `?v=4.0` em `frontend/index.html`.

---

## 3. Arquivos Afetados
- `frontend/assets/js/views/administracao-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `Planejamento/2026-09-08_05_empilhamento_formas_regras_pagamento.md`

---

## 4. Verificação e Testes
- Execução de testes automatizados do Django: `python backend/manage.py test apps.administracao apps.financeiro`.
- Verificação visual no navegador com recarregamento `Ctrl + Shift + R`.

---

## 5. Relatório de Execução Pós-Conclusão
- **Reorganização dos Cards:** A classe `grid` paralela de 2 colunas foi removida e substituída por dois cards independentes com `width: 100%` e `margin-bottom: 24px`, eliminando o esmagamento das tabelas.
- **Tabela de Meios de Pagamento:** Exibida no topo com largura integral, colunas bem distribuídas e botão `+ NOVO MEIO DE PAGAMENTO`.
- **Tabela de Regras Comerciais:** Exibida logo abaixo com largura integral, acomodando perfeitamente todas as 9 colunas sem cortes ou quebras artificiais, e botão com rótulo completo `+ NOVA REGRA COMERCIAL`.
- **Versionamento PWA:** Cache do Service Worker sincronizado para `emc-soldas-v4.0` e tags do `index.html` atualizadas com `?v=4.0`.
- **Bateria de Testes:** 34 testes executados e 100% aprovados (`apps.administracao`, `apps.financeiro`).
