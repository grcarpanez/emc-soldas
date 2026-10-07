# Implementation Plan - Criação de Orçamento e Fatura de Teste para Conciliação Bancária (Laprotec)

- **Data:** 2026-10-07
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Em Andamento (Aprovado pelo usuário)
- **Arquivo de Registro:** `Planejamento/2026-10-07_01_criacao_orcamento_fatura_teste_conciliacao_laprotec.md`

---

## 1. Contexto e Objetivos

### 1.1 Objetivo do Teste
Validar fim a fim o funcionamento do **Motor de Conciliação Bancária Inteligente Split-Screen (Fase 11)** através de uma transação real/simulada de extrato bancário:
- **Transação do Extrato (PIX Recebido):**
  - Tipo: Entrada / Crédito (PIX Recebido)
  - Pagador: LAPROTEC TRANSPORTES LTDA (CNPJ `09.027.059/0001-48`)
  - Banco Pagador: BCO DO BRASIL S.A. (0001), Agência: 8687, Conta: 53128-6 (Conta bancária de origem pertencente ao cliente)
  - Data: 03/08/2026
  - Valor: R$ 200,00

*Nota: A conta do Banco do Brasil informada no comprovante é a conta de emissão do cliente Laprotec, portanto nenhuma conta bancária do Banco do Brasil será criada na empresa EMC Soldas.*

### 1.2 Mecânica de Cálculo do Orçamento e Fatura
1. **Orçamento Comercial:**
   - Cliente: LAPROTEC TRANSPORTES LTDA (Cliente ID 5 já existente no banco de dados com CNPJ `09027059000148`).
   - Equipamento: Nenhum (`equipamento = None`).
   - Data de Geração: 03/08/2026.
   - Status Operacional: `CONCLUIDO` (para habilitar faturamento imediato).
   - Item do Orçamento (Lançamento Livre / Avulso):
     - Descrição: `SERVICO DE TESTE`
     - Tipo de Item: `SERVICO`
     - Quantidade: `1.000`
     - Preço de Custo Unitário: `R$ 170,00`
     - Preço de Venda Unitário: `R$ 210,53`
     - Desconto: `R$ 0,00`
     - Subtotal do Orçamento: `R$ 210,53`
2. **Faturamento Agregado (Momento 1 + Momento 2):**
   - Regra de Pagamento: `A VISTA NO PIX (5% DESC.)` (Regra ID 1, Meio: PIX, Desconto padrão: 5%).
   - Desconto Comercial Aplicado: 5% sobre R$ 210,53 = `R$ 10,53`.
   - Valor Total Faturado: R$ 210,53 - R$ 10,53 = **R$ 200,00 líquidos**!
   - Status da Fatura: `FATURADA` (com data de emissão/fechamento em 03/08/2026).
   - Conta a Receber Gerada (LancamentoFinanceiro):
     - Tipo: `ENTRADA`
     - Descrição: `FATURA #X - PARCELA 1/1 - LAPROTEC TRANSPORTES E MEIO AMBIENTE LTDA EM RECUPERACAO JUDICIAL`
     - Valor: `R$ 200,00`
     - Data de Vencimento: `03/08/2026`
     - Status: `A_VENCER`
     - `is_conciliado`: `False`
     - Vinculada à Fatura gerada e ao Cliente Laprotec.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Uso Exclusivo do Django ORM e Services Oficiais
- A criação respeitará estritamente as regras de negócio de `apps.orcamentos.services` e `apps.faturamento.services`:
  - Criação do Orçamento com snapshot de custos e histórico de auditoria.
  - Inserção do Item de Orçamento avulso calculando margens de contribuição.
  - Transição para status `CONCLUIDO`.
  - Agrupamento em Fatura via `criar_pre_fatura` com a proposta do PIX.
  - Fechamento da Fatura via `faturar_rascunho` com a regra `A VISTA NO PIX (5% DESC.)` e desconto de `R$ 10,53`.
  - Geração compulsória da parcela no Contas a Receber no valor exato de `R$ 200,00` com vencimento em `03/08/2026`.

### 2.2 Validação do Algoritmo de Conciliação
Ao importar o arquivo OFX ou CSV do extrato bancário na tela de **Conciliação Bancária**:
1. O parser detectará o crédito de `R$ 200,00` em `03/08/2026`.
2. O serviço de conciliação identificará o CNPJ `09.027.059/0001-48` no texto da transação, apontando para o cliente **Laprotec**.
3. Cruzará o valor de R$ 200,00 e encontrará:
   - A Fatura em aberto de R$ 200,00.
   - O Lançamento Financeiro a Receber de R$ 200,00 no Contas a Receber.
4. Sugerirá o match na interface Split-Screen para que o usuário possa confirmar a conciliação com 1 clique, liquidando a fatura e atualizando o saldo real da conta.

---

## 3. Registro de Aprovação (Proceed)

- **Status:** Concluído
- **Data/Hora:** 2026-10-07 11:38:28
- **Instrução do Usuário:** "Não crie essa conta do banco do brasil. essa conta é do cliente, a conta que emitiu o pix. Crie apenas o orçamento e fatura, como solicitei"

---

## 4. Relatório de Execução Técnica

Os registros foram criados no banco de dados com 100% de sucesso via script Django ORM atômico:

1. **Cliente Utilizado:**
   - ID: `5`
   - Razão Social: `LAPROTEC TRANSPORTES E MEIO AMBIENTE LTDA EM RECUPERACAO JUDICIAL`
   - CNPJ: `09027059000148`
2. **Orçamento Criado:**
   - ID: `#3`
   - Data de Geração: `03/08/2026`
   - Equipamento: `Nenhum`
   - Status Operacional: `CONCLUIDO`
   - Status Financeiro: `FATURADO`
   - Fatura Vinculada: `#2`
   - Valor Bruto: `R$ 210,53`
   - Item do Orçamento:
     - ID: `#3`
     - Descrição: `SERVICO DE TESTE`
     - Quantidade: `1.000`
     - Custo Unitário: `R$ 170,00`
     - Valor de Venda Unitário: `R$ 210,53`
3. **Fatura Gerada:**
   - ID: `#2`
   - Data de Emissão: `03/08/2026`
   - Data de Fechamento: `03/08/2026`
   - Status: `FATURADA`
   - Condição Comercial: `A VISTA NO PIX (5% DESC.)` (Regra ID 1)
   - Valor Bruto: `R$ 210,53`
   - Desconto Global Concedido: `R$ 10,53` (5%)
   - Valor Total Faturado: `R$ 200,00`
4. **Lançamento Financeiro a Receber Gerado:**
   - ID: `#120`
   - Tipo: `ENTRADA`
   - Descrição: `FATURA #2 - PARCELA 1/1 - LAPROTEC TRANSPORTES E MEIO AMBIENTE LTDA EM RECUPERACAO JUDICIAL`
   - Valor: `R$ 200,00`
   - Data de Vencimento: `03/08/2026`
   - Status de Pagamento: `A_VENCER`
   - `is_conciliado`: `False`
   - Pronto para matching automático e liquidação na tela de **Conciliação Bancária**.

---

## 5. Roteiro de Verificação no ERP

1. **Acessar Orçamentos:**
   - Conferir Orçamento `#3` do cliente **LAPROTEC TRANSPORTES E MEIO AMBIENTE LTDA**, data `03/08/2026`, status operacional `CONCLUIDO`, status financeiro `FATURADO`, item `SERVICO DE TESTE`.
2. **Acessar Faturamento & Conta Corrente:**
   - Conferir Fatura `#2` emitida para a LAPROTEC, valor total faturado `R$ 200,00`, regra `A VISTA NO PIX (5% DESC.)`.
3. **Acessar Tesouraria & Caixa (Contas a Receber):**
   - Conferir Lançamento `#120` de `R$ 200,00` com vencimento em `03/08/2026` com status `A VENCER`.
4. **Acessar Conciliação Bancária:**
   - Selecionar a conta da oficina (onde o Pix caiu) e importar o extrato com a transação de R$ 200,00 de 03/08/2026 contendo o CNPJ/Nome da Laprotec.
   - Observar o match automático sugerindo a baixa da Fatura `#2` e Lançamento `#120`.
   - Confirmar a conciliação e validar se a fatura transitou para `PAGA` e o lançamento para `PAGO`.

---

## 5. Registro de Aprovação (Proceed)

- **Status:** Pendente
- **Aguardando aprovação do usuário para execução.**
