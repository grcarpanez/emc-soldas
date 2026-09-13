# Plano de Implementação: Limpeza Operacional do Banco de Dados para Carga Real (Do Zero)

- **Data de Elaboração:** 2026-09-13
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluído
- **Registro do Proceed:** Aprovado formalmente pelo usuário em 2026-09-13 19:39:17 (The user has approved this document).

---

## 1. Contexto e Objetivos

O usuário solicitou a limpeza total dos dados cadastrais e transacionais de testes do banco de dados MySQL para iniciar a alimentação real da empresa do zero, cobrindo:
- Carga e conciliação completa dos extratos bancários históricos a partir de **02/2025**;
- Cadastro dos clientes, fornecedores e frotas reais;
- Alimentação condizente com a contabilidade real da EMC Soldas.

> [!IMPORTANT]
> **Preservação Mandatória:**
> 1. **Dicionários e Tabelas de Domínio:** UOMs (UN, KG, M, L, etc.) e Dicionário de Atributos Técnicos;
> 2. **Meios e Regras Comerciais de Pagamento:** PIX, Boleto, Cartões, Condições Comerciais;
> 3. **Categorias Financeiras DRE:** Estrutura contábil padronizada do DRE;
> 4. **Parâmetros e Configuração Global:** Dados da oficina, alíquota de ISS retido (3.00%), alíquota do Simples Nacional (8.50%) e configurações SMTP;
> 5. **Usuário Administrador Geral Master e Permissões:** admin@emcsoldas.com.br com seus 10 toggles RBAC ativos para login imediato;
> 6. **Integridade das Migrações e Estrutura Relacional:** Nenhuma alteração estrutural de tabelas ou colunas.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Entidades a Serem Expuradas (100% Limpas)
A limpeza executou exclusão física em ordem segura de dependência referencial (respeitando as Foreign Keys do MySQL com `transaction.atomic`):

1. **Conciliação e Transações Financeiras:**
   - LancamentoFinanceiro (todas as receitas, despesas, parcelas de faturas e registros conciliados ou a vencer);
2. **Faturamento:**
   - FaturaPropostaPagamento
   - Fatura (todas as faturas emitidas de testes).
3. **Orçamentos:**
   - OrcamentoItem
   - OrcamentoPropostaPagamento
   - Orcamento (todos os orçamentos de testes).
4. **Compras:**
   - NotaCompraItem
   - DocumentoFiscalCompra (todas as notas de entrada e XMLs de testes).
5. **Catálogo Operacional:**
   - FichaTecnica
   - ItemAtributoValor
   - Produto (produtos de testes)
   - Item (insumos de testes).
6. **Cadastros Operacionais:**
   - ClienteEquipamento (vínculos de frota)
   - Equipamento (veículos/máquinas de testes)
   - ClienteContato
   - ClienteFornecedor (todos os clientes e fornecedores de testes).
7. **Contas Bancárias:**
   - Reset do saldo para R$ 0,00 das contas existentes com preservação das contas padrão estruturais (`CAIXA FISICO DA OFICINA`, `CONTA BANCARIA PRINCIPAL`), prontas para receber os extratos bancários de 02/2025.

### 2.2 Método de Execução
Criado comando de management Django dedicado e seguro:
`backend/core/management/commands/reset_banco_para_producao.py`
Executável via:
```powershell
.\venv\Scripts\python.exe backend/manage.py reset_banco_para_producao --confirmar
```

---

## 3. Arquivos Criados e Afetados
- `backend/core/management/commands/reset_banco_para_producao.py`
- `Planejamento/2026-09-13_05_limpeza_banco_para_carga_real.md`
- `docs/STATUS.md`
- `walkthrough.md`

---

## 4. Relatório de Execução e Evidências

1. **Comando Executado com Sucesso:**
   - `LancamentoFinanceiro` removidos: 3
   - `Fatura` removidas: 0
   - `Orcamento` removidos: 0
   - `DocumentoFiscalCompra` removidos: 1 (Itens: 1)
   - `Produto` removidos: 1, `Item` removidos: 3, `FichaTecnica`: 3
   - `Equipamento` removidos: 1, `ClienteEquipamento`: 1, `ClienteContato`: 4
   - `ClienteFornecedor` removidos: 4
   - Contas bancárias extras removidas: 3
   - Contas bancárias padrão preservadas (`CAIXA FISICO DA OFICINA`, `CONTA BANCARIA PRINCIPAL`) com saldo zerado (`R$ 0,00`).

2. **Auditoria de Integridade pós-reset:**
   - Clientes/Fornecedores: 0
   - Equipamentos: 0
   - Produtos / Insumos: 0
   - Orçamentos: 0
   - Faturas: 0
   - Lançamentos Financeiros: 0
   - Contas Bancárias ativas: 2 (`CAIXA FISICO DA OFICINA` e `CONTA BANCARIA PRINCIPAL`, ambas com R$ 0,00)
   - UOMs preservadas: 13
   - Atributos Técnicos preservados: 7
   - Categorias Financeiras DRE preservadas: 13
   - Meios de Pagamento preservados: 9
   - Regras de Pagamento preservadas: 9
   - Usuário Administrador Master preservado: `admin@emcsoldas.com.br` (Ativo, com PIN e 10 toggles RBAC intactos).

3. **Validação de Testes Automatizados:**
   - Executada a suíte completa de testes (`python backend/manage.py test backend/`).
   - Resultado: **177 testes executados com 100% de aprovação (OK)**.
