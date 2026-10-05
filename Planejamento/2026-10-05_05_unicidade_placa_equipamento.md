# Plano de Implementação: Unicidade Mandatória de Placa de Equipamento / Veículo, Validação no Exit da Textbox e Blindagem de Exibição

- **Data:** 05/10/2026
- **Autor:** Antigravity (Pair Programming AI)
- **Status:** Concluído
- **Registro do Proceed:** Aprovado em 05/10/2026 14:23 via instrução:
  > *"Pode executar, garantindo a preocupação de tratamento do GET, para que não seja exibido 'null' quando for consultar um equipamento. Podemos fazer a verificação de duplicidade no exit da textbox também, evitando que o usuario digite tudo e na hora de salvar veja que já existe a placa. Assim, digitando a placa, que já é o primeiro campo, o usuario não perde tempo digitando tudo atoa"*

---

## 1. Contexto e Motivação do Negócio

Durante os testes operacionais no módulo de **Cadastros > Equipamentos e Veículos**, foi constatado que o sistema permitiu cadastrar com sucesso dois equipamentos com a exata mesma placa:
1. Equipamento ID #1: `ESCAVADEIRA` (Cavenge Construções Ltda) - Placa `AAA-1A11`
2. Equipamento ID #2: `LARILARIO` (Laprotec Transportes) - Placa `AAA-1A11`

No mundo real e nas normas de trânsito brasileiras (Contran/Renavam), a placa de um veículo é um identificador único nacional. Dois veículos nunca possuem a mesma placa.
Portanto, a regra do negócio exige:
- O campo `placa` no banco de dados deve ter a restrição estrita `UNIQUE`.
- A API REST e o Serializer devem validar a unicidade antes de tentar persistir, fornecendo mensagens amigáveis e informativas de erro (HTTP 400 Bad Request).
- **Validação Antecipada no Exit da Textbox (`blur`/`change`):** Assim que o usuário termina de preencher a placa no modal de cadastro/edição, o sistema consulta a API e avisa imediatamente se a placa já existe, impedindo que o operador perca tempo digitando descrição, selecionando cliente, etc.
- **Tratamento Blindado de GET:** Garantir que em nenhuma hipótese o valor `null` ou `None` retornado pelo backend seja exibido como a string literal `"null"` no formulário, tabelas, comboboxes ou relatórios.
- Equipamentos e máquinas industriais que não possuem placa (ex: soldadoras industriais, betoneiras, geradores) devem continuar sendo suportados livremente (onde `placa` é `NULL`).

---

## 2. Diagnóstico Técnico

1. **Model `Equipamento` (`backend/apps/cadastros/models.py`):**
   - Atualmente possui: `placa = models.CharField(max_length=10, null=True, blank=True, db_index=True)` sem `unique=True`.
2. **Comportamento do MySQL com `UNIQUE` e `NULL` vs `""` (String Vazia):**
   - No MySQL InnoDB, múltiplos registros com valor `NULL` em uma coluna `UNIQUE` **são permitidos** (pois no padrão SQL ANSI, `NULL != NULL`).
   - Contudo, múltiplos registros com string vazia `""` **são considerados duplicatas** e causam erro `IntegrityError 1062`!
   - Portanto, qualquer placa vazia informada pelo frontend deve ser estritamente normalizada para `None` (`NULL`) tanto no frontend quanto no serializer (`to_internal_value` e `validate_placa`).
3. **Duplicata Pré-existente no Banco Local:**
   - Atualmente existem na base local:
     - ID 1: `AAA-1A11` (`ESCAVADEIRA`)
     - ID 2: `AAA-1A11` (`LARILARIO`)
   - Se gerarmos e aplicarmos a migration `makemigrations` / `migrate` sem tratar o registro ID 2 previamente, o MySQL abortará a migração com `django.db.utils.IntegrityError: (1062, "Duplicate entry 'AAA-1A11' for key 'equipamentos.placa'")`.
   - É obrigatório ajustar a placa de teste do registro ID 2 (ex: para `AAA-1A12`) antes de aplicar o comando `migrate`.
4. **Respeito ao Soft Delete e Lixeira:**
   - O `Equipamento` herda de `BaseModel` (que inclui `SoftDeleteModel`).
   - Se uma placa pertencer a um equipamento ativo, a API deve rejeitar indicando qual equipamento e ID já usam aquela placa.
   - Se a placa pertencer a um equipamento que está na **Lixeira** (`deleted_at IS NOT NULL`), a API deve orientar o usuário a restaurar o registro existente na Lixeira pelo módulo de Administração, impedindo duplicidade física de chave única no MySQL.

---

## 3. Decisões Técnicas e Arquiteturais

### 3.1 Tratamento Pré-Migração do Registro Duplicado no Banco
- Executar um script Django pontual antes da migration:
  ```python
  from apps.cadastros.models import Equipamento
  e2 = Equipamento.all_objects.filter(id=2, placa='AAA-1A11').first()
  if e2:
      e2.placa = 'AAA-1A12'
      e2.save(update_fields=['placa'])
  ```

### 3.2 Modificação no Model `Equipamento` (`backend/apps/cadastros/models.py`)
- Adicionar `unique=True` ao campo `placa`:
  ```python
  placa = models.CharField(
      max_length=10,
      null=True,
      blank=True,
      unique=True,
      db_index=True,
      verbose_name="Placa do Veículo / Equipamento (Antiga ou Mercosul)"
  )
  ```

### 3.3 Blindagem no Serializer (`backend/apps/cadastros/serializers.py`)
1. Implementar `to_internal_value(self, data)` em `EquipamentoSerializer` para normalizar strings vazias ou espaços em branco em `placa` e `identificacao` para `None`.
2. Implementar `to_representation(self, instance)` para garantir que valores vazios de `placa` e `identificacao` sejam serializados estritamente como `None` (JSON `null`), expurgando qualquer string `"null"` ou `"None"`.
3. Em `validate_placa(self, value)`:
   - Se `value` for vazio ou `None`, retornar `None`.
   - Sanitizar e validar formato sintático (padrão antigo ou Mercosul).
   - Formatar a placa com hífen (`ABC-1234` ou `BRA-2E19`).
   - Consultar se a placa já existe em equipamento ativo:
     - `qs_ativo = Equipamento.objects.filter(placa=placa_formatada)` (excluindo `self.instance` se for edição).
     - Se existir, lançar `serializers.ValidationError(f"A placa '{placa_formatada}' já está cadastrada no sistema para o equipamento '{duplicado.descricao}' (ID #{duplicado.id}).")`.
   - Consultar se a placa existe em equipamento inativado na Lixeira:
     - `qs_lixeira = Equipamento.all_objects.filter(placa=placa_formatada, deleted_at__isnull=False)` (excluindo `self.instance`).
     - Se existir, lançar `serializers.ValidationError(f"A placa '{placa_formatada}' pertence ao equipamento '{duplicado.descricao}' (ID #{duplicado.id}) que está na Lixeira. Para utilizá-la novamente, restaure o equipamento através da Lixeira no módulo de Administração.")`.

### 3.4 Endpoint de Checagem Prévia (`backend/apps/cadastros/views.py`)
- Criar a ação `@action(detail=False, methods=['get'], url_path='verificar-placa')` em `EquipamentoViewSet`:
  - Recebe `placa` e opcionalmente `equipamento_id`.
  - Retorna JSON: `{ "valida": bool, "disponivel": bool, "em_lixeira": bool, "placa_formatada": str, "mensagem": str }`.
  - Permite feedback imediato no frontend no evento de `blur` / `change` da caixa de texto da placa.

### 3.5 Frontend (`frontend/assets/js/views/cadastros-view.js` e `utils.js`)
- Em `utils.js`:
  - Reforçar `formatarPlacaVeiculo(valor)` para retornar `''` se o valor for nulo, indefinido, vazio ou as strings `"null"`, `"None"`, `"undefined"`.
- Em `cadastros-view.js`:
  - No modal de equipamento:
    - Adicionar elemento `#equip-placa-feedback` abaixo da caixa de texto da placa.
    - Vincular listeners de `blur` e `change` no `#equip-placa` chamando `/api/equipamentos/verificar-placa/`.
    - Se a placa já existir: borda vermelha no input, aviso textual em vermelho e toast de erro amigável imediato.
    - Se a placa for válida e livre: borda verde e aviso de confirmação.
    - Garantir que `value` do input no formulário de edição nunca preencha a string `"null"` se a placa for nula (`(equip?.placa && equip.placa !== 'null') ? equip.placa : ''`).
    - Enviar `placa: window.EMCUtils.sanitizarTextoEmTempoReal(placa) || null` e `identificacao: window.EMCUtils.sanitizarTextoEmTempoReal(identificacao) || null`.
    - No `onConfirm`: caso a verificação acuse placa duplicada ou a API retorne 400, manter o modal aberto (`return false`) e exibir o toast explicativo.

### 3.6 Política de Cache PWA e Service Worker
- Incrementar versão de cache em `frontend/sw.js` de `emc-soldas-v4.53` para `emc-soldas-v4.54`.
- Atualizar cache-busting nos `<script>` e `<link>` do `frontend/index.html` para `?v=4.54`.

---

## 4. Arquivos Afetados

| Arquivo | Natureza da Modificação |
| :--- | :--- |
| `backend/apps/cadastros/models.py` | Adicionar `unique=True` em `Equipamento.placa` |
| `backend/apps/cadastros/serializers.py` | Implementar `to_internal_value`, `to_representation` e validação anti-duplicação em `validate_placa` |
| `backend/apps/cadastros/views.py` | Adicionar action `verificar-placa` no `EquipamentoViewSet` |
| `backend/apps/cadastros/migrations/0006_alter_equipamento_placa.py` | Nova migration gerada pelo Django para aplicar `UNIQUE` no MySQL |
| `backend/apps/cadastros/tests.py` | Adicionar testes de unicidade, verificação via endpoint, tolerância a nulos e rejeição de placa existente na lixeira |
| `frontend/assets/js/utils.js` | Blindar `formatarPlacaVeiculo` contra string `"null"` |
| `frontend/assets/js/views/cadastros-view.js` | Feedback visual e validação no exit (`blur`) da placa, sanitização de `"null"` e persistência de dados em erro |
| `frontend/sw.js` | Atualizar versão do cache (`v4.54`) |
| `frontend/index.html` | Atualizar sufixos `?v=4.54` para cache-busting |
| `docs/STATUS.md` | Registrar a conclusão da funcionalidade e validação de placa única |

---

## 5. Plano de Verificação e Testes

1. **Resolução de dados pré-existentes:**
   - Executar script para atualizar equipamento ID 2 para `AAA-1A12`.
2. **Execução de Migrations:**
   - `python manage.py makemigrations cadastros`
   - `python manage.py migrate cadastros` (deve aplicar sem erros de integridade).
3. **Testes Automatizados:**
   - Executar `python manage.py test backend/apps/cadastros/` e suíte completa `python manage.py test backend/`.
   - Garantir 100% de sucesso nos cenários de:
     - Endpoint `verificar-placa` com placa disponível e com placa duplicada.
     - Tentativa de cadastrar equipamento com placa já existente via POST -> HTTP 400 com mensagem clara.
     - Atualização do próprio equipamento mantendo a mesma placa via PUT -> HTTP 200 OK.
     - Criação de múltiplos equipamentos industriais sem placa (`placa=None` ou `placa=""`) -> HTTP 201 Created para todos.
     - Rejeição de placa pertencente a equipamento na Lixeira -> HTTP 400 orientando restauração.
4. **Verificação no Navegador:**
   - Recarregar com `Ctrl + Shift + R`.
   - Abrir o modal de novo equipamento, digitar `AAA-1A11` e pressionar TAB / sair do campo: verificar a borda vermelha, mensagem de bloqueio imediato e toast explicativo antes mesmo de preencher a descrição.
   - Digitar uma placa válida livre: verificar borda verde e formatação com hífen.
   - Abrir a edição de um equipamento sem placa e confirmar que o campo permanece limpo, sem exibir `"null"`.

---

## 6. Governança e Commit Semântico

Após a execução e validação de todos os testes, será realizado o commit semântico atômico:
- **Mensagem:** `feat(cadastros): restringir placa de equipamento como campo unico e anti-duplicacao`

---

## 7. Relatório de Execução e Evidências de Validação

1. **Higienização de Registro Duplicado Pré-Existente:**
   - Registro ID 2 (`LARILARIO`) teve sua placa ajustada de `AAA-1A11` para `AAA-1A12` via script Django no banco local.
2. **Model e Migração:**
   - Campo `placa` no model `Equipamento` configurado com `unique=True`.
   - Migration `cadastros.0006_alter_equipamento_placa` gerada e aplicada com sucesso no MySQL.
3. **Serializer e Anti-Duplicação:**
   - Métodos `to_internal_value`, `to_representation` e `validate_placa` implementados em `EquipamentoSerializer`.
   - Normalização estrita de strings vazias ou literais `"null"`/`"None"` para `None` (`NULL`).
   - Bloqueio com HTTP 400 Bad Request detalhado para placas já ativas e placas pertencentes a equipamentos na Lixeira.
4. **Endpoint de Verificação no Exit da Textbox:**
   - Action `@action(detail=False, methods=['get'], url_path='verificar-placa')` implementada em `EquipamentoViewSet`.
   - Frontend configurado com listeners `blur` e `change` no `#equip-placa`:
     - Feedback imediato com borda vermelha e mensagem `[BLOQUEIO]` ao sair do campo com placa duplicada.
     - Feedback com borda verde e mensagem de confirmação para placas livres.
     - Bloqueio preventivo no botão de confirmação (`onConfirm`) e persistência dos dados preenchidos no formulário.
5. **Blindagem de Exibição (GET):**
   - Atualizados `formatarPlacaVeiculo` em `utils.js`, `cadastros-view.js` e `orcamentos-view.js` para garantir que `null` nunca seja renderizado como texto `"null"`.
6. **Versionamento PWA:**
   - `sw.js` e `index.html` atualizados para `v4.54`.
7. **Testes Automatizados:**
   - Suíte de cadastros (`apps.cadastros`): 27/27 testes aprovados.
   - Suíte geral de testes (`python manage.py test`): 202/202 testes aprovados com 100% de sucesso.
