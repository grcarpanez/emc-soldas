# Plano de Implementação: Gestão de Contas Bancárias e Conciliação Bancária Universal (OFX / CSV)

- **Data:** 2026-09-11
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed:** Aprovado explicitamente pelo usuário em 2026-09-11 15:26:57 ("Sim").

---

## 1. Contexto e Objetivos
1. Criar a interface de gestão de Contas Bancárias e Caixas Físicos na Tesouraria & Caixa, permitindo visualização de saldos, limites de cheque especial, inclusão, edição e inativação de contas.
2. Implementar motor universal e resiliente de parsing para extratos bancários:
   - OFX: Padrão internacional com extração de FITID, metadados de agência/conta, valores com precisão decimal e históricos.
   - CSV: Multi-banco com normalização de acentos, dicionário amplo de sinônimos (Data, Descrição, Valor Único, Débito/Crédito, Tipo D/C, Documento/Identificador), amostragem heurística de dados e filtro de ruído administrativo (linhas de saldo e totalizadores).
3. Sincronizar frontend da Conciliação Split-Screen para consumir os dados do extrato, selecionar a conta bancária e operar matches e lançamentos rápidos no ato.
4. Incrementar versão do Service Worker PWA para `v4.15`.

---

## 2. Relatório de Execução e Evidências
1. **Backend:**
   - Permissão de `ContaBancariaViewSet` expandida para `[HasCadastrosFinanceirosAccess | HasTesourariaAccess]`.
   - `parsers.py`: Novo motor universal de CSV com normalização `NFKD`, sinônimos expandidos de bancos brasileiros, amostragem por inspeção e descarte de ruído administrativo.
   - `services.py`: Retorno com chaves `extrato` e `transacoes` sincronizadas.
2. **Frontend:**
   - `financeiro-view.js`: Nova aba "CONTAS BANCÁRIAS" com cards de KPIs (Saldo Total, Limite de Crédito, Disponível Total), listagem em tabela, modais de cadastro e edição de contas, e inativação lógica.
   - `conciliacao-view.js`: Seletor de conta bancária, banner de metadados do extrato, leitura de transações, auto-match resiliente, confirmação com `lancamento_ids` e modal de lançamento rápido com categoria DRE.
   - `sw.js` e `index.html`: Versão de cache elevada para `v4.15`.
3. **Validação:**
   - Bateria de testes automatizados (`manage.py test apps.financeiro apps.conciliacao`): 27 testes aprovados com 100% de sucesso.
   - Teste de fluxo completo com arquivos reais (OFX Nubank e CSV com acentos): 100% das transações e metadados processados.
