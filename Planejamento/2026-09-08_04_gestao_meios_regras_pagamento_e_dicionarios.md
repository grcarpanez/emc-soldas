# Planejamento: Gestão Visual de Formas/Regras de Pagamento & CRUD Completo de Dicionários Mestres (UOM & Atributos)

## Metadados
- **Data:** 2026-09-08
- **Autor:** Antigravity / EMC Soldas
- **Status:** Concluído
- **Registro do Proceed:** Aprovado via interface pelo usuário em 2026-09-08 15:41:12 ("Já temos na view isso implementado dessa maneira, só não temos CRUD completo. Só podemos adicionar, sem a opção de alterar ou excluir").

---

## 1. Contexto e Diagnóstico da Varredura
Após uma varredura detalhada entre o backend (29 entidades ORM, endpoints da API REST, serializers e regras de negócio) e o frontend (telas e abas da SPA), foram identificadas as seguintes necessidades:

1. **Meios de Pagamento (`MeioPagamento`) e Regras Comerciais de Pagamento (`RegraPagamento`):**
   - Estão 100% modelados e com rotas REST ativas em `/api/meios-pagamento/` e `/api/regras-pagamento/`, mas **não possuíam nenhuma interface visual** para visualização, cadastro, edição e inativação pelo Administrador.
   - Devem residir na **Central do Administrador** (`#/administracao`), mantendo a coerência de que parametrizações estruturais e políticas do sistema são geridas pelo Admin.

2. **Dicionários Mestres (UOM & Atributos Técnicos):**
   - A aba `DICIONÁRIOS MESTRES (UOM & ATRIBUTOS)` já existe na Central do Administrador e possui listagem e botão de adição, **mas não possui CRUD completo (faltam botões e modais de Alteração/Edição e Exclusão/Inativação com validação de vínculo)**.
   - O backend já possui `PUT/PATCH/DELETE` com regras de integridade (impede inativar UOM em uso por itens/produtos e impede inativar Atributo vinculado a itens). Portanto, o frontend precisa dos botões `EDITAR` e `EXCLUIR` nas duas tabelas.

3. **Demais Entidades Mapeadas no Backend sem View Própria:**
   - **Contas Bancárias (`ContaBancaria`):** CRUD no backend `/api/contas-bancarias/`. No frontend, usada apenas nos selects de extrato/transferência.
   - **Categorias Financeiras DRE (`CategoriaFinanceira`):** CRUD no backend `/api/categorias-financeiras/`. No frontend, usada apenas no select de lançamentos.
   - Ambas serão documentadas e registradas formalmente no arquivo `docs/STATUS.md` para posterior construção de suas interfaces.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Nova Aba na Central do Administrador: `FORMAS & REGRAS DE PAGAMENTO`
- **Posicionamento:** Aba no menu da Central do Administrador (`#/administracao`), posicionada logo após "Serviço SMTP" e antes de "Dicionários Mestres".
- **Seção 1: Dicionário de Meios de Pagamento:**
  - Tabela com: ID, Nome do Meio, Permite Taxa de Maquininha (Badge Sim/Não), Status (Ativo/Inativo), Ações (`EDITAR` / `EXCLUIR`).
  - Botão `+ NOVO MEIO DE PAGAMENTO`.
  - Modal industrial para cadastrar/editar com campos:
    - Nome do Meio (Uppercase sem acento).
    - Toggle `Permite Desconto de Taxa de Maquininha`.
    - Toggle `Ativo`.
  - Ação de exclusão/inativação com confirmação e tratamento defensivo caso o meio esteja em uso por regras ou lançamentos (erro 400 amigável retornado pelo backend).
- **Seção 2: Matriz de Regras e Condições Comerciais:**
  - Tabela com: ID, Nome da Regra, Meio Vinculado, Tipo de Cobrança (À Vista, A Prazo, Parcelado), Nº Parcelas, Prazos (1ª Parcela / Intervalo), Desconto Padrão (%), Status, Ações (`EDITAR` / `EXCLUIR`).
  - Botão `+ NOVA REGRA COMERCIAL`.
  - Modal industrial para cadastrar/editar com:
    - Nome da Regra.
    - Meio de Pagamento vinculado (Select dinâmico).
    - Tipo de Cobrança (`A_VISTA`, `A_PRAZO`, `PARCELADO`).
    - Número de Parcelas.
    - Prazo da 1ª Parcela (dias) e Intervalo entre Parcelas (dias).
    - Desconto Padrão (%) com máscara de porcentagem.
    - Toggle `Ativo`.
  - Ação de exclusão/inativação com confirmação e tratamento defensivo caso esteja vinculado a orçamentos ou faturas.

### 2.2 Evolução para CRUD Completo na Aba `DICIONÁRIOS MESTRES (UOM & ATRIBUTOS)`
- **Unidades de Medida (UOM):**
  - Adição de coluna de `AÇÕES` na tabela.
  - Botão `EDITAR`: abre modal com dados da UOM pré-preenchidos para alteração de sigla e descrição via `PUT /api/dicionario-uom/{id}/`.
  - Botão `EXCLUIR`: abre modal de confirmação para inativação via `DELETE /api/dicionario-uom/{id}/`, com exibição de toast de alerta caso esteja em uso por itens/produtos.
- **Atributos Técnicos:**
  - Adição de coluna de `AÇÕES` na tabela.
  - Botão `EDITAR`: abre modal para renomear o atributo via `PUT /api/dicionario-atributos/{id}/`.
  - Botão `EXCLUIR`: modal de confirmação para inativação via `DELETE /api/dicionario-atributos/{id}/`, com bloqueio amigável se estiver em uso em fichas técnicas/itens.

### 2.3 Registro e Governança no `docs/STATUS.md`
- Inserir as novas entregas na Fase 14.5 e adicionar no checklist as pendências mapeadas na varredura (Contas Bancárias e Categorias Financeiras DRE) para que nenhuma funcionalidade fique esquecida.

### 2.4 Versionamento PWA (Regra 12 do AGENTS.md)
- `frontend/sw.js`: Elevar para `CACHE_NAME = 'emc-soldas-v3.9'`.
- `frontend/index.html`: Atualizar sufixos para `?v=3.9`.

---

## 3. Arquivos a Modificar
- `frontend/assets/js/views/administracao-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`

---

## 4. Verificação e Testes
- Testes automatizados do Django (`backend/manage.py test apps.financeiro apps.catalogo apps.administracao`).
- Testes manuais no navegador:
  - Criação, edição e inativação de Meios de Pagamento.
  - Criação, edição e inativação de Regras Comerciais.
  - Edição e exclusão de Unidades de Medida (UOM) e Atributos Técnicos.
  - Validação dos bloqueios de segurança quando o registro estiver em uso.

---

## 5. Relatório de Execução Pós-Conclusão
- **Aba de Formas & Regras de Pagamento:** Construída com sucesso na Central do Administrador (`administracao-view.js`), contendo tabelas de Meios de Pagamento e Regras Comerciais de Pagamento, com botões de criação, edição e exclusão lógica, respeitando os 0px border-radius e a tipografia técnica do Design System *Industrial Integrity*.
- **CRUD Completo em Dicionários Mestres:** Tabelas de Unidades de Medida (UOM) e Atributos Técnicos evoluídas com coluna de Ações, botões `EDITAR` e `EXCLUIR`, modais de atualização via `PUT` e tratamento gracioso de proteções de integridade referencial via `DELETE`.
- **Mapeamento de Funcionalidades do Backend no `STATUS.md`:** Registradas as entidades `ContaBancaria`, `CategoriaFinanceira`, `CartaoCredito`/`FaturaCartao` e `FichaTecnica` na seção de pendências do `docs/STATUS.md` para planejamento visual futuro.
- **Versionamento PWA:** Cache do Service Worker elevado para `emc-soldas-v3.9` em `frontend/sw.js` e sufixos de cache-busting atualizados para `?v=3.9` em `frontend/index.html`.
- **Bateria de Testes Automatizados:** 49 testes executados e 100% aprovados sem qualquer erro ou regressão (`apps.financeiro`, `apps.catalogo`, `apps.administracao`).
