# Plano de Implementação: Validação Estrita de Placas e Governança de Planejamento

- **Data de Elaboração:** 2026-09-07
- **Autor:** IA Antigravity & Gustavo Carpanez
- **Status:** Concluído
- **Proceed do Usuário:** 
  1. Aprovado em 2026-09-07 ("Eu gostaria que no cadastro de equipamentos, se eu for preencher a placa, ele aceite apenas o padrao antigo e mercosul...")
  2. Aprovado com refinamento de máscara em 2026-09-07 ("Plano aprovado mas em ambos os modelos, antigos ou mercosul, a mascara deve ser a mesma ###-####. Aprovado. Apenas uma dúvida, a inserção do - é automática, certo? o usuario não precisa digitar o -. Se estiver assim, pode executar...")

---

## 1. Contexto e Objetivos

1. **Validação e Máscara Universal de Placas (###-####):**
   - No cadastro de equipamentos/veículos da frota, a placa é opcional, mas quando preenchida, deve seguir estritamente as regras oficiais brasileiras com **máscara universal com hífen `###-####` em ambos os modelos**:
     - Padrão Antigo: `AAA-0000`
     - Padrão Mercosul: `AAA-0A00` (ex: `ABC-1D23`)
   - Regra universal de caracteres:
     - Dígitos 1 a 3: estritamente letras maiúsculas (`[A-Z]`).
     - Hífen `-`: inserido **100% automaticamente** logo após a 3ª letra, sem que o operador precise digitá-lo.
     - Dígito 4: estritamente número (`[0-9]`).
     - Dígito 5: letra ou número (`[A-Z0-9]`).
     - Dígitos 6 e 7: estritamente números (`[0-9]`).
   - Bloqueio reativo de digitação inválida no frontend em tempo real e validação defensiva com resposta 400 Bad Request no backend Django REST.
   - O backend normaliza a gravação no banco de dados padronizada com hífen `f"{placa[:3]}-{placa[3:]}"`.

2. **Governança de Planejamento Mandatória (`AGENTS.md` e pasta `Planejamento/`):**
   - Instituir no `AGENTS.md` a regra inegociável de que **SEMPRE e INEVITAVELMENTE** deve ser elaborado um *Implementation Plan* completo e detalhado antes de qualquer alteração no código ou arquitetura.
   - O plano deve aguardar a aprovação explícita do usuário (`Proceed`).
   - Criar e manter a pasta `Planejamento/` na raiz do repositório para versionamento perpétuo de todos os planos e aprovações.
   - Manter atualizados os arquivos vivos `docs/STATUS.md` e `docs/ERROS.md`.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Backend (`backend/core/utils.py` & `apps/cadastros/serializers.py`):**
   - Função `validar_placa(valor)` implementada em `core/utils.py`.
   - Remoção de pontuações (`-`, espaços) e conversão para maiúsculas.
   - Expressão regular rigorosa: `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`.
   - Método `validate_placa` no `EquipamentoSerializer` levantando `serializers.ValidationError` com mensagem semântica quando inválido e retornando formatado com hífen `f"{placa_limpa[:3]}-{placa_limpa[3:]}"`.
   - Testes unitários cobrindo placas válidas (antiga `ABC-1234`, Mercosul `BRA-2E19`) e inválidas (menos/mais dígitos, posições incorretas).

2. **Frontend (`frontend/assets/js/utils.js` & `views/cadastros-view.js`):**
   - Função utilitária `formatarPlacaVeiculo(valor)` com restrição caractere a caractere no evento `input`:
     - Posições 0, 1, 2: aceita apenas letras maiúsculas.
     - Posição 3: aceita apenas dígitos numéricos.
     - Posição 4: aceita letra ou número.
     - Posições 5 e 6: aceita apenas dígitos numéricos.
     - Inserção automática de `-` após a 3ª letra (máximo de 8 caracteres formatados).
   - Placeholders padronizados: `placeholder="ABC-1234 ou ABC-1D23"`.
   - Validação pré-submit em `cadastros-view.js` disparando Toast de erro industrial caso o usuário informe placa incompleta.

3. **Governança e Versionamento:**
   - Pasta `Planejamento/` criada na raiz com `README.md`.
   - Atualização de `AGENTS.md` com protocolo detalhado e mandatório.
   - Atualização de `docs/STATUS.md` e `docs/ERROS.md`.

---

## 3. Arquivos Modificados / Criados

- `backend/core/utils.py` (Função `validar_placa`)
- `backend/apps/cadastros/serializers.py` (`validate_placa` com persistência normalizada em `###-####`)
- `backend/apps/cadastros/tests.py` (Casos de teste unitário e asserções contra envelope padronizado)
- `frontend/assets/js/utils.js` (`formatarPlacaVeiculo` com hífen automático e `validarPlacaVeiculo`)
- `frontend/assets/js/views/cadastros-view.js` (Máscara, placeholders e toasts nos modais de equipamento e frota)
- `Planejamento/README.md` (Protocolo de governança de planejamento)
- `Planejamento/2026-09-07_01_validacao_placas_e_governanca.md` (Este documento)
- `AGENTS.md` (Regra de ouro e governança)
- `docs/STATUS.md` (Registro na Fase 14.5)
- `docs/ERROS.md` (Registro técnico da validação simétrica de placas)

---

## 4. Plano de Verificação e Resultados

- [x] Testes unitários do Django executados: **157 testes aprovados com 100% de sucesso (`OK`)**.
- [x] Testes de cadastros específicos: **16 testes aprovados com 100% de sucesso**.
- [x] Verificação no frontend dos padrões `AAA-1234` e `ABC-1D23` com inserção automática do hífen.
