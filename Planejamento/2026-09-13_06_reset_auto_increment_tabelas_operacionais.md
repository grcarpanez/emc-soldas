# Plano de Implementacao: Reset de Contadores AUTO_INCREMENT no Comando de Gerenciamento do Django (reset_banco_para_producao)

- **Data de Elaboracao:** 2026-09-13
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluido
- **Registro do Proceed:** Aprovado formalmente pelo usuario em 2026-09-13 20:03:21 (The user has approved this document).

---

## 1. Contexto e Objetivos

Ao executar o comando de gerenciamento python backend/manage.py reset_banco_para_producao --confirmar, todos os dados operacionais e de teste sao expurgados com sucesso. No entanto, o motor MySQL preserva o ponteiro sequencial interno de chave primaria (AUTO_INCREMENT) para cada tabela. Como consequencia, novos cadastros (como o primeiro cliente real) estavam recebendo IDs subsequentes (ex: ID 5, ID 6) em vez de iniciarem no ID 1.

O objetivo desta melhoria foi instruir o MySQL a resetar o AUTO_INCREMENT para 1 em todas as tabelas esvaziadas, garantindo que o primeiro cliente cadastrado seja o Cliente #1, o primeiro orcamento seja o Orcamento #1, a primeira fatura seja a Fatura #1, etc.

---

## 2. Tabelas Operacionais com AUTO_INCREMENT Resetado para 1
As seguintes tabelas esvaziadas recebem ALTER TABLE <tabela> AUTO_INCREMENT = 1;:
1. clientes_fornecedores
2. clientes_contatos
3. equipamentos
4. cliente_equipamento
5. itens
6. item_atributos_valores
7. produtos
8. ficha_tecnica
9. orcamentos
10. orcamento_itens
11. orcamento_propostas_pagamento
12. faturas
13. fatura_propostas_pagamento
14. lancamentos_financeiros
15. documentos_fiscais_compra
16. nota_compra_itens

As tabelas estruturais que mantem registros essenciais (usuarios, dicionario_uom, dicionario_atributos, categorias_financeiras, meios_pagamento, regras_pagamento, contas_bancarias) nao sofreram reset forcado de contador, garantindo estabilidade e integridade dos IDs mestre.

---

## 3. Arquivos Afetados
- backend/core/management/commands/reset_banco_para_producao.py
- Planejamento/2026-09-13_06_reset_auto_increment_tabelas_operacionais.md
- docs/STATUS.md
- walkthrough.md

---

## 4. Relatorio de Execucao e Evidencias

1. Alteracao Aplicada no Comando de Gerenciamento:
   - Adicionada execucao nativa de ALTER TABLE ... AUTO_INCREMENT = 1 no MySQL via connection.cursor() dentro da transacao atomica.
   - Nomes de tabelas validados diretamente contra o schema fisico (clientes_contatos, cliente_equipamento, fatura_propostas_pagamento).

2. Validacao do Contador Sequencial:
   - Teste automatizado com criacao de um cliente real via ORM: gerado rigorosamente com ID = 1.
   - Limpeza final executada com sucesso, deixando o banco com 0 registros operacionais e o proximo ID preparado no 1.
