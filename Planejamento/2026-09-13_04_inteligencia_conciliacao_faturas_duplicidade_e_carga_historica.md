# Plano de Implementação: Inteligência de Conciliação Bancária, Prevenção de Duplicidade, Faturas com ISS Retido e Carga Histórica

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed:** Aprovado formalmente pelo usuário em 2026-09-13 15:47:31 com incorporação da regra de ISS Retido, Alíquotas Globais e tolerância de 5 centavos.

---

## 1. Contexto e Objetivos

O usuário solicitou uma expansão estratégica fundamental na Conciliação Bancária para viabilizar a carga de 1 ano de histórico real da empresa:
1. **Prevenção Rigorosa de Duplicações:** A importação deve verificar se lançamentos do extrato já existem no ERP (por FITID bancário ou valor/data) ou já foram conciliados previamente, alertando o usuário e impedindo duplicações.
2. **Reconhecimento Inteligente de Clientes e Fornecedores:** Identificar CNPJ/CPF e Razão Social contidos na descrição do extrato (ex: `PAGAMENTO RECEBIDO - PETRA MG INDUSTRIA... - 02.329.307/0001-66`) e cruzá-los com a base de parceiros.
3. **Cruzamento com Faturas em Aberto com Dedução de ISS Retido:**
   - Adicionar a flag **`ISS RETIDO`** no cadastro de clientes para identificar tomadores que efetuam retenção na fonte;
   - Adicionar nos **Parâmetros Globais** as alíquotas de **ISS (%)** (para cálculo do desconto do ISS sobre a fatura) e **Simples Nacional (%)** (informativa);
   - O motor de match de faturas calcula o valor líquido esperado (`valor_fatura - iss_retido`) e considera **margem de tolerância de até 5 centavos (`R$ 0,05`)** para arredondamentos bancários.
4. **Viabilização da Carga de 1 Ano de Histórico Real:** Permitir que recebimentos e pagamentos históricos de clientes/fornecedores entrem na contabilidade (DRE e Dossiê do Cliente) devidamente vinculados ao parceiro, sem exigir a criação manual e artificial de orçamentos retroativos de serviços passados.
5. **Classificação Heurística de Tributos e Tarifas:** Sugerir automaticamente categorias para despesas bancárias e tributos (DAS, GPS, FGTS) com base no histórico do extrato.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Banco de Dados e Modelos
- **`apps/cadastros/models.py` (`ClienteFornecedor`):**
  - `iss_retido`: `models.BooleanField(default=False, verbose_name="Tomador com Retenção de ISS na Fonte")`.
- **`apps/administracao/models.py` (`ConfiguracaoGlobal`):**
  - `aliquota_iss`: `models.DecimalField(max_digits=5, decimal_places=2, default=3.00, verbose_name="Alíquota Padrão de ISS Retido (%)")`.
  - `aliquota_simples_nacional`: `models.DecimalField(max_digits=5, decimal_places=2, default=8.50, verbose_name="Alíquota Padrão Simples Nacional (%) - Informativa")`.
- **`apps/financeiro/models.py` (`LancamentoFinanceiro`):**
  - `fitid`: `models.CharField(max_length=150, null=True, blank=True, db_index=True, verbose_name="Identificador Único Bancário (FITID)")`.
  - `cliente_fornecedor`: `models.ForeignKey('cadastros.ClienteFornecedor', on_delete=models.SET_NULL, null=True, blank=True, related_name='lancamentos_financeiros', db_column='cliente_fornecedor_id', verbose_name="Cliente ou Fornecedor Vinculado")`.

### 2.2 Motor de Inteligência Heurística (`apps/conciliacao/services.py`)
- **Extração de CNPJ/CPF:** Expressão regular nos textos do extrato (`\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}`, `\d{14}`, etc.).
- **Detecção de Duplicidade:** Checagem por `fitid` exato (O(1)) ou combinação conta + valor + data ±2 dias.
- **Match de Faturas com Tolerância de R$ 0,05 e Cálculo de ISS Retido:**
  - Para recebimentos de clientes identificados, consulta faturas em aberto (`status='FATURADA'`).
  - Se `cliente.iss_retido == True`:
    - `aliquota = config.aliquota_iss`
    - `valor_iss = (valor_fatura * (aliquota / 100)).quantize(Decimal('0.01'))`
    - `valor_esperado = valor_fatura - valor_iss`
  - Se `abs(valor_extrato - valor_esperado) <= Decimal('0.05')` OU `abs(valor_extrato - valor_fatura) <= Decimal('0.05')`:
    - Match localizado! Conecta a linha Bézier e sugere `[LIQUIDAR FATURA #X (Líquida de ISS)]`.
- **Carga Histórica sem Fatura:**
  - Criação de receita operacional com `cliente_fornecedor_id` associado, sem exigir orçamento ou fatura retroativa.

### 2.3 Frontend PWA e Telas
- **`cadastros-view.js`:** Adicionar o checkbox `[ ] Tomador com Retenção de ISS na Fonte` no formulário de clientes.
- **`administracao-view.js`:** Adicionar campos de `Alíquota ISS (%)` e `Alíquota Simples Nacional (%)` na aba de Parâmetros Globais.
- **`conciliacao-view.js`:**
  - Badges semânticos de cliente identificado, fatura sugerida com aviso de ISS e duplicidade bloqueada;
  - Sugestão de liquidação de fatura com 1 clique;
  - Versionamento elevado para `v4.22`.

---

## 3. Arquivos Afetados
- `backend/apps/cadastros/models.py`
- `backend/apps/cadastros/serializers.py`
- `backend/apps/administracao/models.py`
- `backend/apps/administracao/serializers.py`
- `backend/apps/financeiro/models.py`
- `backend/apps/financeiro/serializers.py`
- `backend/apps/conciliacao/services.py`
- `backend/apps/conciliacao/serializers.py`
- `backend/apps/conciliacao/tests.py`
- `frontend/assets/js/views/cadastros-view.js`
- `frontend/assets/js/views/administracao-view.js`
- `frontend/assets/js/views/conciliacao-view.js`
- `frontend/assets/css/industrial-integrity.css`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`
- `walkthrough.md`
