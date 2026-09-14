# Plano de Implementação: Correção e Proteção do Saldo de Contas Bancárias e Recálculo Automático

Este plano apresenta o diagnóstico detalhado da causa raiz do saldo zerado na conta bancária após a importação do extrato e a renomeação para "NUBANK", e estabelece as correções no backend, no seeder e na base de dados para garantir integridade contábil perpétua.

---

## 1. Diagnóstico e Causa Raiz

Realizamos uma auditoria profunda no banco de dados e nos arquivos de log (`app-2026-09-14.log`):

1. **Os 10 lançamentos do extrato estão 100% íntegros:**
   - Foram importados às `02:23:24`:
     - Entradas (2): R$ 6.948,20 + R$ 3.950,00 = **R$ 10.898,20**
     - Saídas (8): R$ 0,90 + R$ 450,00 + R$ 519,91 + R$ 250,47 + R$ 2.026,53 + R$ 550,00 + R$ 2.300,00 + R$ 2.700,00 = **R$ 8.797,81**
   - Saldo líquido real apurado: **+ R$ 2.100,39**.
2. **O que ocasionou o saldo zerado?**
   - Às `15:39:15`, quando executamos o comando `seed_initial_data` para sincronizar as 20 categorias DRE, a Seção 6 do seeder executou:
     ```python
     ContaBancaria.objects.update_or_create(
         nome='CONTA BANCARIA PRINCIPAL',
         defaults={'saldo': 0.00, 'limite_credito': 1000.00}
     )
     ```
     Como a conta ainda se chamava `CONTA BANCARIA PRINCIPAL`, o `update_or_create` localizou a conta e sobrescreveu o saldo real (`R$ 2.100,39`) para `R$ 0,00`.
   - Às `16:03:35`, você abriu a tela de Contas Bancárias para renomear a conta para `NUBANK`. Como o saldo já havia sido zerado pelo seeder, o formulário exibiu `R$ 0,00` e enviou o PATCH mantendo o saldo em zero.
   - Renomear a conta para `NUBANK` **não foi o problema**: todos os lançamentos estão perfeitamente amarrados pelo `conta_id: 2`.

---

## 2. Soluções Técnicas Propostas

### 2.1 Blindagem Definitiva do Seeder (`seed_initial_data.py`)
- Modificar a rotina de contas bancárias no `seed_initial_data.py`:
  - Se já existirem contas bancárias no banco (`ContaBancaria.all_objects.exists()`), o seeder **NUNCA** altera, reseta ou sobrescreve os saldos nem cria contas duplicadas com os nomes de fábrica.
  - Ele apenas emite log informativo: `"[OK] Contas Bancárias existentes preservadas com seus saldos intactos."`.

### 2.2 Endpoint de Recálculo de Saldo (`POST /api/contas-bancarias/{id}/recalcular-saldo/`)
- Implementar uma action oficial `@action(detail=True, methods=['post'], url_path='recalcular-saldo')` no `ContaBancariaViewSet`:
  - Calcula a soma das entradas liquidadas (`tipo='ENTRADA', status='PAGO'`), subtrai as saídas liquidadas (`tipo='SAIDA', status='PAGO'`) e aplica o saldo líquido das transferências inter-contas (`TRANSFERENCIA`).
  - Atualiza `conta.saldo` com o valor auditado e devolve um payload estruturado:
    ```json
    {
      "status": "sucesso",
      "conta_id": 2,
      "nome": "NUBANK",
      "saldo_anterior": 0.00,
      "novo_saldo": 2100.39,
      "total_entradas": 10898.20,
      "total_saidas": 8797.81
    }
    ```

### 2.3 Botão "RECALCULAR SALDO" no Frontend (`financeiro-view.js`)
- Na tabela de Contas Bancárias em `#/tesouraria`:
  - Adicionar um botão auxiliar `RECALCULAR` ao lado de `EDITAR` e `EXCLUIR`.
  - Ao clicar, o sistema consulta todos os lançamentos pagos daquela conta no banco e ajusta o saldo em tempo real com feedback via Toast notification.

### 2.4 Restauração Imediata da Conta `NUBANK`
- Executar o recálculo imediato na base de dados para a conta #2 (`NUBANK`), reestabelecendo o saldo correto de **R$ 2.100,39**.

---

## 3. Arquivos Afetados

### Backend
1. `backend/core/management/commands/seed_initial_data.py`:
   - Blindar a Seção 6 de contas bancárias contra sobrescrita de saldo em contas existentes.
2. `backend/apps/financeiro/views.py`:
   - Adicionar a action `recalcular_saldo` no `ContaBancariaViewSet`.
3. `backend/apps/financeiro/tests.py`:
   - Adicionar teste unitário validando o recálculo do saldo a partir dos lançamentos pagos.

### Frontend
4. `frontend/assets/js/views/financeiro-view.js`:
   - Adicionar método `recalcularSaldoConta(contaId, nome)` e botão de ação `RECALCULAR` na listagem de contas.
5. `frontend/sw.js` e `frontend/index.html`:
   - Versionamento PWA incrementado para `v4.29` (cache-busting).

---

## 4. Plano de Verificação e Testes

1. **Restauração e Recálculo da Conta NUBANK:**
   - Executar o recálculo e verificar se `NUBANK` assume exatamente `R$ 2.100,39`.
2. **Teste do Seeder:**
   - Executar `python backend/manage.py seed_initial_data` e verificar se o saldo de `NUBANK` permanece rigorosamente em `R$ 2.100,39` (sem ser zerado).
3. **Bateria de Testes Automatizados:**
   - Executar `.\venv\Scripts\python.exe backend/manage.py test backend/` garantindo 100% de aprovação.
4. **Governança:**
   - Salvar plano aprovado em `Planejamento/2026-09-14_04_protecao_e_recalculo_saldo_contas_bancarias.md`.
   - Atualizar `docs/STATUS.md` e executar commit semântico.

---

## 5. Relatório de Execução e Evidências

1. **Blindagem do Seeder (\seed_initial_data.py\):**
   - Alterada a Seção 6 para verificar \if not ContaBancaria.all_objects.exists():\.
   - Contas bancárias existentes têm seus saldos e limites estritamente preservados.
   - Teste prático executado: seeder rodado sem alterar o saldo da conta NUBANK.

2. **Endpoint de Recálculo de Saldo (ecalcular-saldo\):**
   - Implementada action \@action(detail=True, methods=['post'], url_path='recalcular-saldo')\ em \ContaBancariaViewSet\.
   - Adicionado teste unitário \	est_recalcular_saldo_conta_bancaria\ em \pps/financeiro/tests.py\.
   - Conta NUBANK (ID #2) recalculada e restaurada para R$ 2.100,39.

3. **Frontend PWA (v4.29):**
   - Adicionado botão \RECALCULAR\ na tabela de Contas Bancárias em \#/tesouraria\.
   - Adicionado método ecalcularSaldoConta(contaId, nome)\ com modal de confirmação e feedback Toast.
   - Sincronizado cache PWA para \emc-soldas-v4.29\ em \sw.js\ e \index.html\.

4. **Homologação:**
   - Suíte de 185 testes automatizados do Django executada com 100% de aprovação (OK em 71.573s).
