# Plano de Implementacao: Selecao Obrigatoria de Conta e Deteccao Inteligente de Meios de Pagamento na Conciliacao

- **Data de Elaboracao:** 2026-09-14
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluido
- **Registro do Proceed:** Aprovado formalmente pelo usuario em 2026-09-14 02:04:14 (The user has approved this document).

---

## 1. Contexto e Objetivos

O usuario reportou tres pontos operacionais criticos na Conciliacao Bancaria:
1. A combobox de conta bancaria iniciava pre-selecionada no Caixa Fisico, induzindo o usuario a importar e conciliar na conta errada por acidente.
2. Todas as transacoes importadas eram classificadas genericamente como BOLETO BANCARIO, ignorando se eram PIX, Cartao, TED ou Dinheiro.
3. Necessidade de clarificar se transferencias de clientes deveriam criar faturas retroativas ou lancamentos de receita direta.

---

## 2. Solucoes Implementadas

### 2.1 Selecao Manual Obrigatoria de Conta Bancaria
- A combobox de conta bancaria inicia obrigatoriamente em -- SELECIONE A CONTA BANCARIA * -- sem pre-selecao automatica.
- Bloqueio preventivo do botao + IMPORTAR EXTRATO e acoes da mesa caso nenhuma conta esteja selecionada, com toast orientando a escolha da conta.

### 2.2 Motor Heuristico de Deteccao de Meio de Pagamento
- Criada funcao detectar_meio_pagamento_transacao em pps/conciliacao/services.py analisando <MEMO>, canal e <TRNTYPE>:
  - PIX: PIX, TRANSF PIX, PAGTO PIX, LIQ PIX, QR CODE, CHAVE PIX.
  - Cartoes: CARTAO, MAQ, POS, CIELO, REDE, GETNET, STONE, VISA, MASTER, ELO (classificando em Debito ou Credito conforme canal/tipo).
  - TED/DOC: TED, DOC, TEF, TRANSF, TRANSFERENCIA.
  - Boleto: BOLETO, TITULO, PAGTO TITULO, COBRANCA, LIQ TITULO.
  - Dinheiro/Deposito: DEPOSITO, DEP DINHEIRO, SAQUE.
  - Fallback dinamico inteligente para entradas (PIX/TED) e saidas (PIX/Boleto).

### 2.3 Mesa de Triagem no Frontend & Sincronizacao
- A Mesa de Triagem agora exibe combobox de Meio de Pagamento pre-selecionada com o meio detectado para cada card, permitindo ajuste manual do operador.
- O payload de executarImportacaoLote envia meio_pagamento_id individualmente.
- O backend grava o meio de pagamento real especificado para cada LancamentoFinanceiro.

---

## 3. Arquivos Afetados
- backend/apps/conciliacao/services.py
- frontend/assets/js/views/conciliacao-view.js
- frontend/sw.js (versao elevada para emc-soldas-v4.28)
- frontend/index.html (cache-busting ?v=4.28)
- Planejamento/2026-09-14_02_selecao_obrigatoria_conta_e_meios_pagamento.md
- docs/STATUS.md
- walkthrough.md

---

## 4. Relatorio de Execucao e Evidencias

1. Deteccao Heuristica Validada:
   - PIX TRANSF GUSTAVO CARPANEZ -> PIX (ID 1)
   - PGTO ELETRON COBRANCA BRADESCO -> BOLETO BANCARIO (ID 3)
   - COMPRA CARTAO VISA ELETRO -> CARTAO DE DEBITO (ID 5)
   - TRANSF TED 237 -> TRANSFERENCIA TED/DOC (ID 6)
   - DEPOSITO EM DINHEIRO -> DEPOSITO BANCARIO (ID 7)

2. Testes Automatizados:
   - 184 testes executados com 100% de aprovacao (OK) em 74 segundos.
