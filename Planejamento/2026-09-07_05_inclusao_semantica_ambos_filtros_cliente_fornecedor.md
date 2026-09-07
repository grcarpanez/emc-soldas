# Registro de Planejamento: Inclusão Semântica de Parceiros Tipo 'Ambos' nos Filtros de Clientes e Fornecedores

- **Identificador:** `Planejamento/2026-09-07_05_inclusao_semantica_ambos_filtros_cliente_fornecedor.md`
- **Data:** 2026-09-07
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-09-07T15:03:16-03:00
  - **Aprovação:** Usuário aprovou expressamente o plano de implementação no artifact `implementation_plan.md` ("The user has approved this document.").

---

## 1. Contexto e Motivação
Na listagem de clientes/fornecedores (`/#cadastros`), quando um parceiro é cadastrado com o tipo `'Ambos'` (cliente e fornecedor simultaneamente), ele não estava aparecendo ao filtrar por "CLIENTES" nem por "FORNECEDORES".
A causa raiz foi identificada no backend (`ClienteFornecedorViewSet.get_queryset` em `backend/apps/cadastros/views.py`): o filtro comparava `if tipo == 'Cliente'` de forma case-sensitive, enquanto o frontend enviava maiúsculas (`?tipo=CLIENTE` e `?tipo=FORNECEDOR`). Como resultado, a condição falhava e caía no `else: queryset = queryset.filter(tipo=tipo)`, excluindo completamente os registros `'Ambos'`.

O usuário optou pela **Abordagem Ágil**: manter o schema de banco intacto e normalizar o tratamento do filtro no backend, garantindo que `Ambos` seja retornado tanto para filtros de clientes quanto de fornecedores.

---

## 2. Decisões Técnicas e Arquiteturais
1. **Normalização no Backend:**
   - Tratar o parâmetro `tipo` recebido via query params com `.strip().upper()`.
   - Se `tipo_upper in ('CLIENTE', 'CLIENTES')`: filtrar `tipo__in=['Cliente', 'Ambos']`.
   - Se `tipo_upper in ('FORNECEDOR', 'FORNECEDORES')`: filtrar `tipo__in=['Fornecedor', 'Ambos']`.
   - Se `tipo_upper in ('AMBOS', 'CLIENTE/FORNECEDOR', 'CLIENTE_FORNECEDOR')`: filtrar `tipo='Ambos'`.
   - Caso contrário: manter `filter(tipo=tipo)`.
2. **Preservação de Integridade:**
   - Nenhuma migração de banco necessária.
   - Nenhuma quebra de contrato de API.
3. **Testes Automatizados:**
   - Adicionar testes cobrindo requisições com `tipo=CLIENTE`, `tipo=Cliente`, `tipo=FORNECEDOR`, `tipo=Fornecedor` e sem parâmetro `tipo`.

---

## 3. Arquivos Modificados
- `backend/apps/cadastros/views.py`: ajuste em `ClienteFornecedorViewSet.get_queryset` com normalização de string e `tipo__in`.
- `backend/apps/cadastros/tests.py`: inclusão do método `test_filtro_tipo_clientes_e_fornecedores_inclui_ambos`.
- `docs/STATUS.md`: atualização do status e checklist da Fase 14.5.

---

## 4. Relatório de Execução e Evidências de Testes
1. **Testes Unitários do Módulo de Cadastros:**
   - Comando: `.\venv\Scripts\python.exe backend/manage.py test apps.cadastros`
   - Resultado: 17 testes executados com 100% de sucesso (`OK`).
2. **Suíte Global de Testes do Sistema:**
   - Comando: `.\venv\Scripts\python.exe backend/manage.py test backend/`
   - Resultado: 158 testes executados com 100% de sucesso (`OK`) em 63.6s, com zero regressões.
