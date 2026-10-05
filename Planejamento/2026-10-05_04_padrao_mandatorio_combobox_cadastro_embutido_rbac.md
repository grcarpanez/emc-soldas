# Plano de Implementação: Padrão Mandatório de Combobox Pesquisável com Ação Embutida e Governança RBAC

**Data:** 05/10/2026  
**Autor:** Antigravity (AI Pair Programmer)  
**Status:** Concluído  
**Registro de Aprovação:** Aprovado pelo usuário via manifestação "Proceed" em 05/10/2026 às 13:27:44-03:00.

---

## 1. Contexto e Motivação

Durante os refinamentos na tela de orçamentos e compras, identificou-se a necessidade de consolidar um padrão definitivo para seleção de entidades dependentes em modais e formulários:
1. **Localização Estrita da Ação Rápida:** O botão de cadastro rápido deve residir **exclusivamente dentro do dropdown da combobox pesquisável** (`.emc-combobox-action`), logo abaixo da caixa de busca (`DIGITE PARA FILTRAR...`). Botões externos soltos posicionados nos rótulos (`<label>`) ou ao lado dos inputs devem ser eliminados para preservar o alinhamento de grid, evitar poluição visual e manter a densidade técnica do Design System *Industrial Integrity*.
2. **Governança e Blindagem RBAC Inegociável:** A opção de cadastro rápido embutida na combobox **não pode ser exibida de forma indiscriminada**. Ela deve ser dinamicamente avaliada e condicionada ao papel e permissões do usuário logado (`window.auth`). 
   - Exemplo concreto: A seleção de unidades de medida (UOM) nos cadastros de insumo e produto só deve exibir o botão `+ CADASTRAR NOVA UNIDADE (UOM)` para usuários Administradores (ou com `gestao_dicionario_uom`). Usuários Operadores comuns não devem visualizar essa opção.
   - De forma análoga, se no futuro ou em perfis restritos um usuário não possuir autorização para cadastrar clientes (`acesso_comercial`), a opção `+ CADASTRAR NOVO CLIENTE` deve sumir automaticamente da combobox de clientes.
3. **Consagração em Documentação de Governança:** O usuário solicitou que essa regra seja formalizada em todos os arquivos centrais do projeto (`AGENTS.md`, `docs/DESIGN.md` e `docs/FSD.md`) para que atue como uma diretriz perpétua e inegociável em desenvolvimentos futuros.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Suporte Nativo a RBAC no Componente Combobox (`initSearchableSelect`)
Em `frontend/assets/js/utils.js`, o helper `initSearchableSelect(selectEl, opts)` receberá lógica de checagem de permissão através da função interna `isActionPermitida()`:
```javascript
function isActionPermitida() {
  if (!opts.action || !opts.action.label) return false;
  let permitido = true;
  // 1. Checagem de Administrador estrito
  if (opts.action.adminOnly) {
    permitido = window.auth ? window.auth.isAdmin() : false;
  }
  // 2. Checagem de Toggle RBAC dinâmico
  else if (opts.action.permission) {
    permitido = window.auth ? window.auth.hasPermission(opts.action.permission) : false;
  }
  // 3. Condição funcional arbitrária complementar
  if (permitido && typeof opts.action.condition === 'function') {
    try {
      permitido = !!opts.action.condition();
    } catch (e) {
      console.warn('Erro ao avaliar condition da ação da combobox:', e);
      permitido = false;
    }
  }
  return permitido;
}
```
- Se `isActionPermitida()` for `true`, o elemento `.emc-combobox-action` é gerado e anexado ao dropdown, e no caso de nenhum resultado ser encontrado (`encontrados === 0`), o botão `.emc-combobox-no-res-btn` é oferecido.
- Se `isActionPermitida()` for `false`, nenhum botão de cadastro é renderizado, exibindo apenas o texto padrão `"NENHUM RESULTADO ENCONTRADO"`.

### 2.2 Método `isAdmin()` em `AuthManager` (`frontend/assets/js/auth.js`)
Garantir o método canônico `window.auth.isAdmin()`:
```javascript
isAdmin() {
  if (!this.user) return false;
  const roleUpper = (this.user.role || '').toUpperCase();
  return roleUpper === 'ADMIN' || !!this.user.is_admin;
}
```

### 2.3 Matriz de Associação RBAC por Entidade
| Entidade | Ação Rápida Embutida na Combobox | Permissão RBAC Exigida |
| :--- | :--- | :--- |
| **Cliente** | `+ CADASTRAR NOVO CLIENTE` | `acesso_comercial` |
| **Equipamento** | `+ CADASTRAR NOVO EQUIPAMENTO` | `acesso_comercial` |
| **Fornecedor** | `+ CADASTRAR NOVO FORNECEDOR` | `acesso_compras` |
| **Insumo / Item** | `+ CADASTRAR NOVO INSUMO` | `gestao_catalogo` |
| **Produto BOM** | `+ CADASTRAR NOVO PRODUTO BOM` | `gestao_catalogo` |
| **Unidade de Medida (UOM)** | `+ CADASTRAR NOVA UNIDADE (UOM)` | `gestao_dicionario_uom` (ou `adminOnly: true`) |
| **Categoria Financeira** | `+ CADASTRAR NOVA CATEGORIA` | `cadastros_financeiros` |
| **Conta Bancária** | `+ CADASTRAR NOVA CONTA` | `cadastros_financeiros` |

### 2.4 Modal Universal e Reutilizável de UOM (`window.EMCUtils.abrirModalCadastroRapidoUom`)
Implementar utilitário reutilizável em `utils.js` para criação rápida de UOM (Sigla + Descrição), permitindo que qualquer seletor de UOM no sistema chame o modal sobreposto com z-index seguro e atualize automaticamente o select chamador.

### 2.5 Limpeza de Botões Externos em Orçamentos e Compras
- Em `frontend/assets/js/views/orcamentos-view.js`:
  - Remover o botão `<button id="btn-orc-novo-equip">` do cabeçalho da label de Equipamentos.
  - A combobox `orc-equipamento` já dispõe de `action: { label: '+ CADASTRAR NOVO EQUIPAMENTO', permission: 'acesso_comercial', ... }`.
  - A combobox `orc-cliente` receberá `action: { label: '+ CADASTRAR NOVO CLIENTE', permission: 'acesso_comercial', ... }`.
  - A combobox `sel-produto-id` receberá `action: { label: '+ CADASTRAR NOVO PRODUTO BOM', permission: 'gestao_catalogo', ... }`.
  - A combobox `sel-item-id` receberá `action: { label: '+ CADASTRAR NOVO INSUMO', permission: 'gestao_catalogo', ... }`.
- Em `frontend/assets/js/views/compras-view.js`:
  - Remover botões externos residuais nos `<label>` se houver.
  - Garantir `permission: 'acesso_compras'` em `selForn` e `permission: 'gestao_catalogo'` em `selItem`.
  - No modal de cadastro rápido de insumo, transformar `novo-item-uom-compra` e `novo-item-uom-consumo` em comboboxes com `action: { label: '+ NOVA UNIDADE (UOM)', adminOnly: true, ... }`.
- Em `frontend/assets/js/views/catalogo-view.js`:
  - No modal de produto e item, transformar selects de UOM em comboboxes com ação rápida restrita a Administrador.
  - Na ficha técnica BOM, vincular `permission: 'gestao_catalogo'` para adicionar insumo.
- Em `frontend/assets/js/views/cadastros-view.js`:
  - Em `abrirModalEquipamento`, vincular `permission: 'acesso_comercial'` para seleção de cliente proprietário.

### 2.6 Registro Normativo em Documentos Vivos
1. **`AGENTS.md` (Regra 14):**
   - Definir a regra mandatória de que toda seleção de entidade em modal deve ser combobox pesquisável com botão de ação embutido no dropdown.
   - Proibir botões soltos em labels.
   - Exigir checagem estrita de RBAC antes de renderizar qualquer ação rápida na combobox.
2. **`docs/DESIGN.md`:**
   - Adicionar subseção específica sobre o componente `.emc-combobox-action`: visual industrial, comportamento no hover, e regra de visibilidade condicionada a permissões.
3. **`docs/FSD.md` (Seção 29):**
   - Registrar o capítulo "UX Não-Interruptiva: Comboboxes Pesquisáveis com Cadastro Rápido Embutido e Blindagem RBAC", com a tabela de mapeamento entre entidades e permissões do sistema.

---

## 3. Arquivos Afetados

| Arquivo | Ação | Descrição das Modificações |
| :--- | :--- | :--- |
| `frontend/assets/js/auth.js` | Modificar | Adicionar método `isAdmin()` em `AuthManager`. |
| `frontend/assets/js/utils.js` | Modificar | Atualizar `initSearchableSelect` com suporte a `adminOnly`, `permission` e `condition`. Implementar `abrirModalCadastroRapidoUom`. |
| `frontend/assets/js/views/orcamentos-view.js` | Modificar | Remover botão avulso do label de equipamentos. Configurar ações embutidas com RBAC para Cliente, Equipamento, Produto BOM e Insumo. |
| `frontend/assets/js/views/compras-view.js` | Modificar | Ajustar comboboxes de Fornecedor e Insumo com RBAC; adicionar combobox de UOM com ação para Admin no modal rápido de insumo. |
| `frontend/assets/js/views/catalogo-view.js` | Modificar | Adicionar ação de criação de UOM para Admin nos selects de UOM de itens e produtos. Adicionar ação de novo insumo na ficha BOM. |
| `frontend/assets/js/views/cadastros-view.js` | Modificar | Adicionar ação rápida de cliente na combobox de proprietário de equipamento com RBAC. |
| `AGENTS.md` | Modificar | Inserir Regra 14 sobre padrão de combobox embutida e governança RBAC. |
| `docs/DESIGN.md` | Modificar | Documentar o componente `.emc-combobox-action` e a regra de RBAC. |
| `docs/FSD.md` | Modificar | Inserir Seção 29 com o padrão de UX não-interruptiva e a matriz RBAC. |
| `docs/STATUS.md` | Modificar | Atualizar checklist e status do projeto. |
| `frontend/sw.js` | Modificar | Incrementar `CACHE_NAME` para `'emc-soldas-v4.53'`. |
| `frontend/index.html` | Modificar | Atualizar sufixos de cache-busting para `?v=4.53`. |

---

## 4. Plano de Verificação e Testes

1. **Testes Automatizados de Backend:**
   - Executar `python backend/manage.py test backend/` para certificar integridade das permissões e endpoints.
2. **Validação Manual de UI e Permissões:**
   - Autenticar como Administrador:
     - Abrir modal de novo orçamento: verificar que a combobox de cliente exibe `+ CADASTRAR NOVO CLIENTE`, equipamento exibe `+ CADASTRAR NOVO EQUIPAMENTO`, produto exibe `+ CADASTRAR NOVO PRODUTO BOM` e insumo exibe `+ CADASTRAR NOVO INSUMO`.
     - Verificar que não há botão avulso no label de equipamento.
     - Abrir modal de cadastro de insumo: verificar que os campos de UOM exibem `+ CADASTRAR NOVA UNIDADE (UOM)`.
   - Autenticar ou simular Operador restrito (sem `gestao_dicionario_uom` ou sem `acesso_comercial`):
     - Confirmar que o botão de UOM NÃO aparece na combobox.
     - Confirmar que a combobox funciona perfeitamente como filtro/busca sem o botão.
3. **Validação de Sobreposição de Modais e Z-Index:**
   - Acionar cadastro rápido dentro de um modal já aberto e certificar que o modal filho abre perfeitamente sobreposto e os toasts continuam no topo absoluto (`z-index: 999999`).

---

## 5. Próximo Passo

Concluir e submeter para verificação do usuário.

---

## 6. Relatório de Execução e Homologação (Pós-Conclusão)

### 6.1 Resultados Obtidos
1. **Remoção de Botões Externos nos Rótulos:**
   - Eliminados com sucesso os botões avulsos `btn-orc-novo-equip`, `btn-compras-novo-forn` e `btn-compras-novo-item` posicionados nos `<label>`. As grids e rótulos agora seguem 100% o Spatial Budget e estética limpa industrial.
2. **Combobox com Ação Rápida Embutida e Governança RBAC:**
   - O utilitário `initSearchableSelect` foi atualizado para suportar `adminOnly`, `permission` e `condition` através do verificador `isActionPermitida()`.
   - Adicionada a função reutilizável `window.EMCUtils.abrirModalCadastroRapidoUom` e o método `window.auth.isAdmin()`.
   - Comboboxes nos módulos de Orçamentos, Compras, Catálogo e Cadastros foram devidamente configuradas com as permissões dinâmicas:
     - Clientes: `acesso_comercial`
     - Equipamentos: `acesso_comercial`
     - Fornecedores: `acesso_compras`
     - Insumos: `gestao_catalogo`
     - Produtos BOM: `gestao_catalogo`
     - Unidades de Medida (UOM): `gestao_dicionario_uom` / Administrador (`adminOnly: true`)
3. **Consagração Normativa em Documentos Vivos:**
   - **`AGENTS.md`:** Inserida a **Regra 14** formalizando o padrão obrigatório de combobox pesquisável com ação embutida e exigência de controle RBAC.
   - **`docs/DESIGN.md`:** Documentada a subseção 3.1 com o Design System para `.emc-combobox-action` (cores, contraste, hover e supressão quando sem permissão).
   - **`docs/FSD.md`:** Criada a **Seção 29** estabelecendo os princípios de UX Não-Interruptiva e a Matriz Oficial de RBAC.
   - **`docs/STATUS.md`:** Checklist atualizado com a versão v4.53.
4. **Versionamento e PWA:**
   - Service Worker atualizado para `CACHE_NAME = 'emc-soldas-v4.53'`.
   - `index.html` sincronizado com sufixo `?v=4.53` em todos os scripts e links CSS.

### 6.2 Evidências dos Testes Automatizados
- **Suíte de Testes do Backend:** `.\venv\Scripts\python backend/manage.py test backend/`
- **Resultado:**
  ```text
  Ran 201 tests in 82.059s
  OK
  Destroying test database for alias 'default'...
  Found 201 test(s).
  System check identified no issues (0 silenced).
  === Semeamento e sincronizacao de dados estruturais concluidos com sucesso! ===
  ```
- **Taxa de Aprovação:** 100% (201/201 testes aprovados).
