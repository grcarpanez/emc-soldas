# Planejamento: Detecção de Boletos Bancários, Extração Robusta de Chaves (NF-e/NFS-e) e Pré-Visualização Enriquecida do Fornecedor

- **Data:** 2026-09-11
- **Autor:** Antigravity (Pair Programming)
- **Status:** Concluído
- **Registro do Proceed do Usuário:** 2026-09-11 13:43:03-03:00 - "The user has approved this document."

---

## 1. Contexto e Objetivos

A partir de testes práticos com quatro documentos reais (DANFSe v2.0 Juiz de Fora, DANFE Rivelli, Boleto Bancário Novus/Sicoob e Fatura/NFCom Vivo), foram identificadas quatro necessidades cruciais:
1. **Detecção e Alerta Impeditivo de Boletos Bancários:** Impedir que boletos bancários ou fichas de compensação sejam aceitos como notas fiscais de compra, bloqueando o cadastro equivocado de pagadores/beneficiários e direcionando o usuário para o módulo Financeiro (Contas a Pagar).
2. **Extração de Chave da NFS-e Nacional (50 Dígitos):** Permitir a captura da chave oficial do Padrão Nacional da NFS-e (DANFSe v2.0 com 50 dígitos numéricos).
3. **Extração Robusta de Chave da DANFE NF-e (44 Dígitos):** Evitar que padrões regex gananciosos capturem dígitos vizinhos (como o CNPJ do emitente logo acima da chave) e falhem na validação do dígito verificador.
4. **Segregação Estrita Prestador vs. Tomador:** Garantir que o CNPJ capturado no PDF seja sempre o do emitente/fornecedor, jamais do cliente/tomador.
5. **Pré-Visualização Enriquecida do Fornecedor no Modal:** Consultar a Receita Federal imediatamente no backend ao identificar um fornecedor novo e exibir no modal "FORNECEDOR NÃO ENCONTRADO" a Razão Social, Nome Fantasia, CNPJ formatado e Cidade/UF para conferência segura.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Classificação Prévia de Documentos no Backend:**
   - Termos de boleto bancário (`ficha de compensação`, `bloqueto`, `linha digitável`, `autenticação mecânica`, `sacador avalista`, `nosso número`, etc.) sem marcadores fiscais ativam `is_documento_fiscal = False` e `tipo_documento = 'BOLETO'`.
2. **Regex de Chaves e DV:**
   - Chave em 11 blocos de 4 dígitos: `\b(?:\d{4}[\s.-]+){10}\d{4}\b` (44 dígitos com validação de DV via Módulo 11).
   - Chave da NFS-e Nacional: 50 dígitos contínuos (`\b\d{50}\b`) ou via rótulo `CHAVE DE ACESSO DA NFS-e`.
3. **Consulta de CNPJ na Análise Prévia:**
   - Ao identificar emitente não cadastrado, o endpoint `analisar-documento` consulta `consultar_cnpj_externo(cnpj_limpo)` e anexa os dados cadastrais da Receita Federal na resposta JSON.
4. **Design System e Frontend:**
   - Exibir alerta bloqueante para boletos.
   - Card técnico com Razão Social, Fantasia e CNPJ no modal de novo fornecedor.
   - `formatarChaveAcessoNfe` expandido para até 50 dígitos sem truncamento.
5. **Versionamento PWA:**
   - Incremento para `v4.13` no Service Worker (`sw.js`) e Shell SPA (`index.html`).

---

## 3. Arquivos Afetados

- `backend/apps/compras/services.py`
- `backend/apps/compras/views.py`
- `backend/apps/compras/tests.py`
- `frontend/assets/js/utils.js`
- `frontend/assets/js/views/compras-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`

---

## 4. Plano de Verificação

- Testes automatizados do Django via `python backend/manage.py test backend/`.
- Validação com os 4 documentos reais fornecidos pelo usuário.

---

## 5. Relatório de Execução (Pós-Conclusão)

- **Classificador de Boletos:** Implementado em `services.py` e integrado na view `analisar_documento`. Boletos bancários e documentos não fiscais são agora barrados de imediato com aviso orientativo sobre o Contas a Pagar.
- **Extração de Chaves de 44 e 50 dígitos:** Padrão em 11 blocos de 4 dígitos para DANFE NF-e 55 e suporte total à chave de 50 dígitos da NFS-e Nacional.
- **Segregação Prestador vs Tomador:** O CNPJ extraído foca exclusivamente nos blocos `PRESTADOR / FORNECEDOR` e `EMITENTE`, evitando capturar o CNPJ do cliente/tomador.
- **Consulta da Receita Federal:** Integrada via `consultar_cnpj_externo` para pré-carregar Razão Social, Nome Fantasia e Município/UF quando o fornecedor for novo.
- **Frontend Compras:** Modal "FORNECEDOR NÃO ENCONTRADO" reestilizado com card técnico contendo os dados oficiais da empresa. `formatarChaveAcessoNfe` atualizado para até 50 dígitos.
- **Suíte de Testes Automatizados:** 168 testes do Django executados com 100% de aprovação (OK em 68.3s).
- **Versionamento PWA:** Cache atualizado para `v4.13` em `sw.js` e `index.html`.