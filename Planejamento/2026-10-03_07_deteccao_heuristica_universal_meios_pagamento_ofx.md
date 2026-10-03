# Plano de Implementação: Detecção Heurística Universal de Meios de Pagamento, Gestão de Guias Fiscais (DAS vs GPS) e Bloqueio de Pendências com Destaque Visual

## 1. Metadados do Plano
- **Data de Elaboração:** 03/10/2026
- **Autor:** Antigravity (Pair Programming IA)
- **Status:** `Concluído`
- **Identificador:** `Planejamento/2026-10-03_07_deteccao_heuristica_universal_meios_pagamento_ofx.md`
- **Registro do Proceed:** Aprovado formalmente pelo usuário em 03/10/2026 às 14:44:54 ("Execute considerando o comentário"). Ajuste acatado: texto genérico "⚠️ GUIA RECEITA FEDERAL".

---

## 2. Contexto Operacional, Esclarecimento de Dúvidas e Diagnóstico

### 2.1 Esclarecimento das Observações do Usuário

#### 1. Transação de Fevereiro/2026 (`PIX ENVIADO DES: EMC SOLDAS 19/02`)
> *Comentário do Usuário: "Não temos nenhum lançamento em fevereiro. Não compreendi isso."*
- **Esclarecimento:** Essa transação **não está cadastrada no seu ERP**. Ela está registrada **dentro do arquivo `doc testes/Extrato OFC Bradesco Fev.2026.OFX`** que você colocou na pasta de testes para análise prévia.
- Como você nos informou que ainda não importou o extrato do Bradesco para o sistema (estava testando apenas com o Nubank), fizemos a leitura direta do arquivo em código para inspecionar como o banco Bradesco estrutura as informações. Essa transação só entrará no ERP quando você decidir importar esse extrato.

#### 2. Duas Guias da Receita Federal no Extrato (DAS do Simples Nacional vs. GPS / INSS)
> *Comentário do Usuário: "Vamos deixar só assim. Melhor não dizer o que pode ser. Futuramente podem ter outras, então vamos deixar mais genérico. '⚠️ GUIA RECEITA FEDERAL'"*
- **Diagnóstico nos Arquivos Reais (Nubank e Bradesco):**
  - No extrato do Nubank de Junho/2025 (dia 18/06/2025):
    - `Transferência enviada pelo Pix - RECEITA FEDERAL - 00.394.460/0058-87 - R$ 342,12`
    - `Transferência enviada pelo Pix - RECEITA FEDERAL - 00.394.460/0058-87 - R$ 250,47`
  - No extrato do Bradesco de Fevereiro/2026 (dia 20/02/2026):
    - `PIX QR CODE DINAMICO DES: RECEITA FEDERAL - R$ 408,42`
    - `PIX QR CODE DINAMICO DES: RECEITA FEDERAL - R$ 250,47`
  - **A Realidade Técnica Bancária:**
    Tanto no Nubank quanto no Bradesco (e em qualquer banco brasileiro), pagamentos de guias tributárias federais via Pix QR Code Dinâmico são emitidos com o favorecido único **RECEITA FEDERAL DO BRASIL** (CNPJ `00.394.460/0058-87`). O extrato bancário não sabe o conteúdo da guia (se é o DAS do Simples Nacional ou a GPS/DCTFWeb referente ao INSS/Previdência).
  - **Problema da Regra Anterior:** O sistema classificava cegamente qualquer `RECEITA FEDERAL` como `IMPOSTOS E TRIBUTOS` (Simples Nacional), forçando a GPS/INSS a entrar na categoria errada!
  - **Solução Alinhada com a Regra do Usuário:**
    1. Se a descrição contiver expressamente `DAS` ou `SIMPLES NACIONAL`, sugere `IMPOSTOS E TRIBUTOS`.
    2. Se contiver expressamente `GPS` ou `INSS` ou `PREVIDENCIA`, sugere `ENCARGOS TRABALHISTAS`.
    3. Quando o extrato trouxer apenas `RECEITA FEDERAL` genérico (sem especificar qual guia é), o sistema **NÃO chuta a categoria**: deixa a **Categoria DRE em aberto (não definida)** e exibe um card de atenção com aviso contextual genérico:  
       `⚠️ GUIA RECEITA FEDERAL`.  
       Dessa forma, o operador é obrigado a bater o olho e definir com 100% de precisão contábil.

#### 3. Verificação do Usuário, Bloqueio de Lacunas e Destaque Visual nos Cards
> *Comentário do Usuário: "Podemos colocar uma verificação do usuário? Assim como nas categorias, quando ele não encontra, ele pede ao usuário que selecione. Não podemos fazer a mesma coisa aqui? Assim, o que temos certeza, é classificado automaticamente, o que não está mapeado, leva a responsabilidade para o usuário definir, garantindo segurança. Aproveite para verificar, por favor, porque não testei isso, se caso o usuário passe por uma categoria não definida, e agora, por um meio não definido, sem perceber, o sistema salva a informação em branco ou bloqueia a importação pedindo que o usuário complete as lacunas? Esse seria o correto, e para facilitar a visualização, marcar o card que precisa de atenção de uma cor chamativa."*
- **Diagnóstico do Comportamento Atual:**
  - **Categoria Contábil:** O frontend já bloqueava a importação caso houvesse categoria vazia, mas o card não possuía um destaque visual forte (apenas uma borda amarela sutil no select).
  - **Meio de Pagamento:** **Não bloqueava!** Havia um fallback cego: se o meio não fosse identificado, o backend atribuía `PIX` ou o primeiro meio ativo do banco (`meio_padrao`), salvando silenciosamente sem avisar o usuário!
- **Nova Solução Definitiva:**
  1. **Fim do Chute Cego:** O motor heurístico não força mais `PIX` nem `meio_padrao`. Se a transação não puder ser classificada com convicção absoluta, ela retorna `None` (Meio Não Definido).
  2. **Bloqueio Duplo (Frontend e Backend):** A importação em lote é estritamente **bloqueada** se houver qualquer lançamento ativo com Categoria DRE vazia **OU** Meio de Pagamento vazio.
  3. **Destaque Visual Chamativo nos Cards Pendentes:**
     - Qualquer card com Categoria ou Meio pendente ganha:
       - Borda chamativa em cor de alerta industrial (`border: 2px solid var(--color-warning); box-shadow: 0 0 10px rgba(245, 166, 35, 0.25); background: rgba(245, 166, 35, 0.08);`).
       - Badge destacado no topo do card: `⚠️ ATENÇÃO: DEFINA O MEIO E/OU CATEGORIA DRE`.
       - O select vazio fica destacado com borda de aviso.
     - **Reatividade em Tempo Real:** Conforme o usuário seleciona a categoria ou meio no card, o card se auto-valida dinamicamente; se ambos estiverem preenchidos, o alerta visual desaparece instantaneamente.

---

### 2.2 Universalidade para Todos os Bancos Brasileiros (Padrão Febraban / OFX)

O padrão Febraban e OFX permite cobrir universalmente todos os bancos operando no Brasil:

| Banco | Cartão de Débito | Pix | Boleto / Cobrança | Tarifas / Débito em Conta |
| :--- | :--- | :--- | :--- | :--- |
| **Nubank** | `Compra no débito - ...` | `Transferência enviada pelo Pix - ...`, `Transferência recebida pelo Pix - ...` | `Boleto de cobrança` | `Tarifa - ...` |
| **Bradesco** | `COMPRA CARTAO DEBITO ...`, `COMPRA VISA DEBITO ...`, `COMPRA ELO DEBITO ...` | `PIX ENVIADO DES: ...`, `PIX QR CODE ESTATICO DES: ...`, `PIX QR CODE DINAMICO DES: ...` | `LIQUIDACAO DE COBRANCA VALOR DISPONIVEL`, `PAGTO COBRANCA` | `TARIFA REGISTRO COBRANCA ...`, `DEBITO AUTOMATICO` |
| **Itaú** | `COMPRA A DEBITO ...`, `RSHOP ...` (RedeShop), `COMPRA DEB ...` | `PIX TRANSF ...`, `PIX PAGTO ...`, `PIX QRCODE ...` | `PAGTO TITULO ...`, `LIQ TITULO ...` | `TAR CONTA ...`, `DA ...` (Débito Automático) |
| **Banco do Brasil** | `BB COMPRA DEBITO ...`, `COMPRA COM CARTAO ...`, `COMPRA VISA/ELO/MASTER ...` | `PIX - ENVIADO ...`, `PIX - RECEBIDO ...` | `LIQ COBRANCA ...`, `PAGTO TITULO ...` | `TARIFA PACOTE ...`, `DEBITO AUT ...` |
| **Santander** | `COMPRA DEBITO ...`, `COMPRA NO DEBITO ...`, `COMPRA CARTAO ...` | `PIX ENVIADO ...`, `PIX RECEBIDO ...` | `LIQ TITULO ...`, `TITULO BANCARIO ...` | `TAR PACOTE ...`, `DEB CONTA ...` |
| **Caixa Econômica** | `COMPRA ELO DEBITO ...`, `COMPRA VISA DEBITO ...`, `COMPRA DÉBITO ...` | `ENVIO PIX ...`, `RECEB PIX ...` | `PAGTO BOLETO ...`, `LIQ TITULO ...` | `DEB CESTA ...`, `DEB AUTO ...` |
| **Bancos Digitais (Inter, C6, Stone, PagBank)** | `Compra Débito ...`, `Compra no cartão de débito ...`, `Transação POS` | `Pix Enviado ...`, `Pix Recebido ...` | `Pagamento de Boleto ...` | `Tarifa de Manutenção ...` |

---

## 3. Decisões Técnicas e Arquiteturais

### 3.1 Refatoração do Motor Heurístico (`backend/apps/conciliacao/services.py`)

A função `detectar_meio_pagamento_transacao` passará a seguir as seguintes regras:

1. **Sanitização Inicial de Acentos:**
   - `sanitizar_texto_maiusculo(descricao)` garante que `débito` vire `DEBITO`, eliminando falhas por acentuação.
2. **Prioridade 1: PIX**
   - Palavras-chave: `PIX`, `TRANSF PIX`, `PAGTO PIX`, `LIQ PIX`, `QR CODE`, `QRCODE`, `CHAVE PIX`, `PIX RECEBIDO`, `PIX ENVIADO`, `PIX TRANSF`, `DICT `, `PAGAMENTO PIX`, `RECEBIMENTO PIX`, `INSTANTANEO`.
   - Meio Alvo: `PIX`.
3. **Prioridade 2: CARTÃO DE DÉBITO (Cobertura Universal)**
   - Padrões explícitos:
     - `COMPRA NO DEBITO`, `COMPRA A DEBITO`, `COMPRA DEBITO`, `COMPRA DEB`
     - `COMPRA CARTAO DEBITO`, `COMPRA COM CARTAO`, `CARTAO DEBITO`, `CARTAO DEB`
     - `DEBITO CARTAO`, `DEB CARTAO`, `COMPRA NO CARTAO`
     - `RSHOP`, `REDE SHOP` (Itaú RedeShop)
     - `MAESTRO`, `VISA ELECTRON`, `ELECTRON`
     - `ELO DEBITO`, `DEBITO ELO`, `DEBITO VISA`, `DEBITO MASTER`
     - `POS ` ou `trntype_upper == 'POS'` (quando for SAIDA)
     - Compras em adquirentes (`CIELO`, `REDE`, `GETNET`, `STONE`, `PAGSEGURO`, `SUMUP`, `PAG*`, `MERC PAGO`, `BIN `) associadas a `COMPRA` em saída, desde que não contenham `CREDITO`.
   - **Exceção Defensiva:** Não casar com débitos automáticos em conta (`DEBITO AUTOMATICO`, `DEBITO EM CONTA`, `DEB AUTO`, `DEB CONTA`).
   - Meio Alvo: `CARTAO DE DEBITO`.
4. **Prioridade 3: CARTÃO DE CRÉDITO**
   - Padrões: `COMPRA NO CREDITO`, `COMPRA A CREDITO`, `COMPRA CREDITO`, `COMPRA CRED`, `CARTAO CREDITO`, `CREDITO CARTAO`, `FATURA CARTAO`.
   - Meio Alvo: `CARTAO DE CREDITO`.
5. **Prioridade 4: DÉBITO EM CONTA / TARIFAS BANCÁRIAS**
   - Padrões: `TARIFA`, `TAR `, `CESTA`, `MANUT CONTA`, `TAXA SERVICO`, `IOF`, `DEBITO AUTOMATICO`, `DEB AUTO`, `DEBITO EM CONTA`, `DEB CONTA`.
   - Meio Alvo: `DEBITO EM CONTA` (id 10 já existente no MySQL; se inativo, fallback para `TRANSFERENCIA TED/DOC`).
6. **Prioridade 5: BOLETO BANCÁRIO / TÍTULO / COBRANÇA**
   - Padrões: `BOLETO`, `TITULO`, `PAGTO TITULO`, `COBRANCA`, `LIQ TITULO`, `LIQ COBRANCA`, `LIQUIDACAO DE COBRANCA`, `CONVENIO`, `BLOQUETO`.
   - Meio Alvo: `BOLETO BANCARIO`.
7. **Prioridade 6: TRANSFERÊNCIA BANCÁRIA (TED / DOC / TEF / Inter-contas)**
   - Padrões: `TED `, `DOC `, `TEF `, `TRANSF `, `TRANSFERENCIA`, `TRANSF ENTRE CONTAS`, `TRANSF C/C`, `DOC/TED`.
   - Meio Alvo: `TRANSFERENCIA TED/DOC`.
8. **Prioridade 7: DINHEIRO / DEPÓSITO / SAQUE**
   - Padrões: `DEPOSITO`, `DEP DINHEIRO`, `SAQUE`, `ESPECIE`.
   - Meio Alvo: `DEPOSITO BANCARIO` (se ENTRADA) ou `DINHEIRO` (se SAIDA).
9. **Prioridade 8: CHEQUE**
   - Padrões: `CHEQUE`, `CHQ `.
   - Meio Alvo: `CHEQUE`.
10. **Zero Chute Cego (Retorno de Meio Não Definido):**
    - Se a transação não se enquadrar com convicção em nenhuma regra acima, a função retorna `None`. O sistema não força chute, repassando a escolha consciente para o operador na tela.

---

### 3.2 Refinamento na Classificação DRE (`enriquecer_transacao_inteligencia`)
- **Proteção do Nome da Empresa:** Utilizar regex de palavra inteira `\bDAS\b` para que o nome `EMC SOLDAS` não seja classificado como tributo fiscal.
- **Tratamento das Guias da Receita Federal (DAS vs GPS):**
  - Se contiver `DAS` ou `SIMPLES NACIONAL`: Categoria `IMPOSTOS E TRIBUTOS (SIMPLES NACIONAL / ISS / TAXAS)`.
  - Se contiver `GPS` ou `INSS`: Categoria `ENCARGOS TRABALHISTAS (FGTS E INSS)`.
  - Se contiver apenas `RECEITA FEDERAL` genérico: **Não define categoria automaticamente** (retorna `None`) e adiciona alerta visual informativo orientando o usuário a escolher entre DAS ou GPS.
- **Rendimentos Financeiros:** Reconhecer `RENTAB`, `INVEST`, `APLICACAO` como Categoria DRE `OUTRAS RECEITAS OPERACIONAIS E RENDIMENTOS`.

---

### 3.3 Bloqueio de Lacunas e Destaque Visual no Frontend (`conciliacao-view.js` e CSS)

1. **Bloqueio Mandatório na Importação em Lote:**
   - Em `executarImportacaoLote`, validar rigorosamente:
     - `pendentesCategoria = ativos.filter(p => !p.categoria_id && (!p.lancamento_existente_id || p.acao_duplicidade !== 'VINCULAR'))`
     - `pendentesMeio = ativos.filter(p => !p.meio_pagamento_id && (!p.lancamento_existente_id || p.acao_duplicidade !== 'VINCULAR'))`
   - Se houver qualquer item pendente, abortar com aviso:  
     *"Existem X lançamento(s) com Categoria Contábil ou Meio de Pagamento pendente(s). Preencha todas as lacunas em destaque antes de gerar o lote."*
2. **Validação no Backend:**
   - Em `executar_importacao_lote` (`services.py`), se `categoria_id` ou `meio_pagamento_id` estiverem vazios para novos lançamentos, lançar `ValidationError`, impedindo que registros incompletos sejam salvos.
3. **Destaque Visual Chamativo nos Cards Pendentes:**
   - Adicionar classe `.card-pendente-atencao` nos cards que possuem Categoria ou Meio pendente:
     - Borda chamativa em tom de alerta industrial: `border: 2px solid #f5a623 !important; box-shadow: 0 0 10px rgba(245, 166, 35, 0.25); background: rgba(245, 166, 35, 0.06);`
     - Badge no topo do card: `<div class="badge-alerta-pendencia">⚠️ ATENÇÃO: DEFINA O MEIO E/OU CATEGORIA DRE</div>`
     - Borda de atenção destacada no `select` pendente.
   - **Reatividade em Tempo Real:** Conforme o usuário seleciona os valores nos campos, os eventos `atualizarCategoriaPreLancamento` e `atualizarMeioPreLancamento` reavaliam o estado do card e removem o destaque de alerta assim que todas as lacunas forem preenchidas.

---

## 4. Arquivos a Modificar / Criar

| Arquivo | Ação | Descrição |
| :--- | :--- | :--- |
| `Planejamento/2026-10-03_07_deteccao_heuristica_universal_meios_pagamento_ofx.md` | Atualizar | Este plano estruturado |
| `backend/apps/conciliacao/services.py` | Modificar | Refatoração de `detectar_meio_pagamento_transacao`, `enriquecer_transacao_inteligencia` e validação em `executar_importacao_lote` |
| `frontend/assets/js/views/conciliacao-view.js` | Modificar | Bloqueio duplo de lacunas, destaque chamativo nos cards pendentes e reatividade |
| `frontend/assets/css/industrial-integrity.css` | Modificar | Estilos para `.card-pendente-atencao`, `.badge-alerta-pendencia` e `.select-pendente-alerta` |
| `frontend/sw.js` | Modificar | Incremento de versão de cache (`v4.37` -> `v4.38`) |
| `frontend/index.html` | Modificar | Cache-busting dos arquivos JS e CSS (`?v=4.38`) |
| `backend/apps/conciliacao/tests.py` | Modificar | Bateria de testes unitários cobrindo Nubank, Bradesco, Itaú, BB, Santander, Caixa, Inter e bloqueio de lacunas |
| `docs/STATUS.md` | Modificar | Atualização de status da Fase 11 / 14.5 |

---

## 5. Plano de Verificação e Testes

1. **Testes Automatizados de Backend:**
   - Validação da classificação das compras de débito e transferências Pix do Nubank.
   - Validação de tarifas e liquidação de cobrança do Bradesco.
   - Validação de que `EMC SOLDAS` não vira imposto.
   - Validação de que `RECEITA FEDERAL` genérico deixa categoria em aberto para decisão do usuário.
   - Validação de que a API bloqueia importação com meio ou categoria em branco.
2. **Testes Visuais e Interativos no Frontend:**
   - Verificação de que transações com meio ou categoria pendentes ganham o card chamativo com borda de alerta e badge de atenção.
   - Verificação de que ao selecionar o meio e a categoria, o card remove a borda de alerta em tempo real.
   - Verificação de que o botão de importação em lote bloqueia a confirmação se houver lacunas pendentes.
3. **Commit Semântico:**
   - `feat(conciliacao): deteccao universal de meios de pagamento e bloqueio de pendencias no extrato`

---

## 6. Relatório de Execução e Homologação Técnica (Pós-conclusão)

### 6.1 Implementações Realizadas
1. **Motor Heurístico Universal (`backend/apps/conciliacao/services.py`):**
   - Sanitização de strings em maiúsculas sem acentos (`sanitizar_texto_maiusculo`) permitindo que descrições como `"Compra no débito"` virem `"COMPRA NO DEBITO"`.
   - Hierarquia precisa cobrindo universalmente os padrões de extratos bancários brasileiros (Nubank, Bradesco, Itaú, BB, Santander, Caixa, Inter, C6, etc.).
   - Eliminação de chutes cegos: se não houver convicção absoluta na descrição, retorna `None` (deixando a escolha segura para o operador).
   - Regex de palavra inteira `\b(DAS|DARF|IPTU|IPVA)\b` impedindo que a razão social `EMC SOLDAS` seja confundida com tributo fiscal.
   - Detecção contextual de guias federais: guias emitidas para `RECEITA FEDERAL` genérica deixam a Categoria DRE em aberto (`None`) e ativam a flag `alerta_receita_federal = True`.
   - Categorização automática de rendimentos bancários e aplicações financeiras como `OUTRAS RECEITAS OPERACIONAIS E RENDIMENTOS`.
   - Validação defensiva rigorosa em `executar_importacao_lote`: lançamento de `ValidationError` caso `categoria_id` ou `meio_pagamento_id` estejam vazios em novos lançamentos.

2. **Interface Visual e Reatividade no Frontend (`frontend/assets/js/views/conciliacao-view.js` e CSS):**
   - Criação de classes no design system *Industrial Integrity* (`.card-pendente-atencao`, `.badge-alerta-pendencia`, `.badge-alerta-rf`, `.select-pendente-alerta`).
   - Cards com lacunas pendentes são destacados com borda de alerta industrial `#f5a623`, fundo sutil e badge no topo.
   - Inclusão do aviso informativo genérico `"⚠️ GUIA RECEITA FEDERAL"` conforme diretriz expressa do usuário.
   - Implementado método `atualizarEstadoCard(idx)` reativo em tempo real: conforme o operador seleciona o meio ou a categoria no card, o destaque de alerta é removido instantaneamente.
   - Bloqueio no botão de lote `btn-gerar-lote` e validação preventiva com Toast industrial ao clicar para gerar o lote com pendências.

3. **Versionamento PWA e Cache-Busting:**
   - `frontend/sw.js`: `CACHE_NAME = 'emc-soldas-v4.38'`
   - `frontend/index.html`: tags de scripts e folhas de estilo atualizadas com `?v=4.38`.

### 6.2 Resultados de Homologação Automatizada
- **Testes Unitários de Conciliação (`apps/conciliacao/tests.py`):** 18 testes executados com 100% de aprovação, validando Nubank, Bradesco, Itaú, BB, Caixa, Santander, guias da Receita Federal e bloqueio de lacunas.
- **Suíte Global de Regressão:** 197 testes automatizados executados e 100% aprovados sem qualquer quebra (OK em 75.3s).
