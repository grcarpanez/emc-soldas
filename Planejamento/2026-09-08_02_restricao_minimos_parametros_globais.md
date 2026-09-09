# Planejamento: Restrição de Mínimos nos Campos de Validade, Soft Lock e Retenção de Logs

## Metadados
- **Data:** 2026-09-08
- **Autor:** Antigravity / EMC Soldas
- **Status:** Pendente de Aprovação (Aguardando Proceed)
- **Registro do Proceed:** Pendente.

---

## 1. Contexto e Objetivos
Na aba **Parâmetros Globais** da Central Administrativa (`administracao-view.js`), os campos de entrada numérica possuem botões nativos de incremento/decremento (steppers) do tipo `type="number"`.
Atualmente eles permitem navegar para valores negativos.
Conforme especificação do usuário:
- **Validade Padrão Orçamento (Dias):** no mínimo **1**.
- **Tempo Soft Lock (Minutos):** no mínimo **1**.
- **Retenção de Logs (Dias):** no mínimo **0** (zero).

---

## 2. Decisões Técnicas e Arquiteturais
- **Frontend (`administracao-view.js`):**
  - Adição do atributo `min="1"` em `#cfg-validade` e `#cfg-ociosidade`.
  - Adição do atributo `min="0"` em `#cfg-retencao-logs`.
  - Tratamento defensivo no evento `input`/`change` para impedir digitação ou colagem de valores inferiores ao mínimo permitido.
- **Backend (`apps/administracao/serializers.py`):**
  - `validate_validade_orcamento_dias`: garantir `value >= 1`.
  - `validate_tempo_ociosidade_minutos`: nova validação garantindo `value >= 1`.
  - `validate_retencao_logs_dias`: ajuste para permitir `value >= 0` (rejeitando apenas valores `< 0`).
- **Versionamento PWA:**
  - `CACHE_NAME = 'emc-soldas-v3.7'` em `frontend/sw.js`.
  - Sufixos `?v=3.7` em `frontend/index.html`.

---

## 3. Arquivos a Modificar
- `frontend/assets/js/views/administracao-view.js`
- `backend/apps/administracao/serializers.py`
- `backend/apps/administracao/tests.py`
- `frontend/sw.js`
- `frontend/index.html`

---

## 4. Verificação e Testes
- Bateria de testes automatizados do Django (`apps.administracao`).
- Testes manuais na interface com os botões de incremento/decremento e digitação manual de valores inválidos.

---

## 5. Relatório de Execução
- **Frontend:** Atualizado rontend/assets/js/views/administracao-view.js com min="1" para validade e soft lock, min="0" para logs, e sanitização ativa contra negativos nos eventos input e change.
- **Backend:** Atualizado ConfiguracaoGlobalSerializer em ackend/apps/administracao/serializers.py com validação de 	empo_ociosidade_minutos >= 1, alidade_orcamento_dias >= 1 e etencao_logs_dias >= 0.
- **Versionamento PWA:** CACHE_NAME = 'emc-soldas-v3.7' em rontend/sw.js e tags atualizadas com ?v=3.7 em rontend/index.html.
- **Testes Automatizados:** 37 testes executados via python backend/manage.py test apps.authentication apps.administracao com 100% de sucesso.
