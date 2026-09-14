# Plano de Implementacao: Reset de AUTO_INCREMENT de Contas Bancarias e Cartoes de Credito

- **Data de Elaboracao:** 2026-09-14
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluido
- **Registro do Proceed:** Aprovado formalmente pelo usuario em 2026-09-14 01:40:07 (The user has approved this document).

---

## 1. Contexto e Objetivos

Na tabela contas_bancarias, as duas contas oficiais (CAIXA FISICO DA OFICINA com ID 1 e CONTA BANCARIA PRINCIPAL com ID 2) sao preservadas pelo comando reset_banco_para_producao com saldo zerado (R$ 0,00). No entanto, a exclusao das contas extras de teste nao resetava o ponteiro AUTO_INCREMENT do MySQL. Como consequencia, o contador permaneceu em 8, fazendo com que uma nova conta cadastrada pulasse do ID 2 diretamente para o ID 7 ou 8.

O objetivo foi integrar o reset do sequencial de AUTO_INCREMENT para as contas bancarias e cartoes de credito, garantindo que a proxima conta cadastrada seja rigorosamente o ID 3 e os cartoes iniciem no ID 1.

---

## 2. Tabelas Ajustadas
1. contas_bancarias (ajustada para AUTO_INCREMENT = 1 -> MySQL recalcula max(id)+1 = 3)
2. cartoes_credito (AUTO_INCREMENT = 1)
3. faturas_cartao (AUTO_INCREMENT = 1)

---

## 3. Arquivos Afetados
- backend/core/management/commands/reset_banco_para_producao.py
- Planejamento/2026-09-14_01_reset_auto_increment_contas_bancarias.md
- docs/STATUS.md
- walkthrough.md

---

## 4. Relatorio de Execucao e Evidencias

1. Alteracao Aplicada no Comando de Gerenciamento:
   - Adicionada exclusao de FaturaCartao e CartaoCredito em ordem segura.
   - Adicionadas as tabelas contas_bancarias, cartoes_credito e faturas_cartao na lista de tabelas com ALTER TABLE ... AUTO_INCREMENT = 1.
   - Tratamento adequado do tipo de retorno na exclusao de FaturaCartao.

2. Validacao Pratica:
   - Verificacao de SHOW TABLE STATUS LIKE contas_bancarias: Auto_increment = 3.
   - Teste de insercao de nova conta bancaria via ORM: gerada rigorosamente com ID = 3.
   - Reset final executado, mantendo apenas as 2 contas oficiais (IDs 1 e 2) e o sequencial do MySQL em 3.
