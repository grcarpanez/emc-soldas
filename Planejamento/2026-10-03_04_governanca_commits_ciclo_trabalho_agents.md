# Registro de Planejamento: Governança de Commits Semânticos Mandatórios por Implementation Plan no Ciclo de Trabalho Operacional (AGENTS.md)

- **Identificador:** `Planejamento/2026-10-03_04_governanca_commits_ciclo_trabalho_agents.md`
- **Data:** 2026-10-03
- **Autor:** Antigravity (Pair Programming com o Usuário)
- **Status:** Concluído
- **Registro do Proceed:**
  - **Data/Hora:** 2026-10-03T01:31:09-03:00
  - **Aprovação:** Usuário autorizou a execução imediata com a mensagem "Execute".

---

## 1. Contexto e Objetivos

O usuário solicitou:
> *"inclui na sessão '### 7.3 Ciclo de Trabalho Operacional (Passo a Passo)' do agents.md a obrigatoriedade de commits a cada alteração exeutada por um implementation plan, de acordo com as especificações da sessão '## 30. Norma Operacional de Versionamento: Boas Práticas, Convenções e Prefixos no Git' do fsd.md"*

### Objetivos Concretizados:
1. Atualizar e expandir a subseção `### 7.3 Ciclo de Trabalho Operacional (Passo a Passo)` do `AGENTS.md`.
2. Consagrar a obrigatoriedade inegociável de commits no Git por cada Implementation Plan concluído (sem aglutinação de planos).
3. Detalhar as convenções de commit da Seção 30 do `docs/FSD.md` (formato canônico, tabela de prefixos, regras de ouro e proibições de versionamento de segredos).
4. Atualizar a documentação viva em `docs/STATUS.md` e formalizar o commit semântico atômico desta tarefa.

---

## 2. Decisões Técnicas e Arquiteturais

- **Edição no `AGENTS.md` (Subseção 7.3):**
  - Adicionado bloco de alerta `[!IMPORTANT]` no topo de 7.3 enfatizando a obrigatoriedade de commit ao final de cada Implementation Plan aprovado como critério de encerramento da entrega.
  - Expandido o item 4 da FASE 3 (`Executar Commit Semântico Mandatório por Plano (Regra 13 & FSD Seção 30)`), especificando:
    - Critério de saída inegociável.
    - Commits atômicos (FSD 30.5.1).
    - Estrutura canônica `<tipo>[escopo]: <descrição no imperativo e em pt-BR>` (FSD 30.1).
    - Tabela resumida de prefixos válidos (`feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`, `revert`, `security`).
    - 7 Regras de ouro para redação da mensagem (FSD 30.4).
    - Proibição absoluta de versionar credenciais, segredos e arquivos `.env` (FSD 30.5.3).
    - Exigência de informar o commit realizado no relatório de conclusão ao usuário.

---

## 3. Arquivos Afetados

- `AGENTS.md`: Atualizada subseção 7.3 com as normas de commit por plano e convenções da Seção 30 do FSD.
- `Planejamento/2026-10-03_04_governanca_commits_ciclo_trabalho_agents.md`: Criação do registro formal do plano aprovado e executado.
- `docs/STATUS.md`: Atualizado checklist e registros de governança do projeto.

---

## 4. Plano de Verificação e Resultados

1. **Validação Textual:**
   - Conferido alinhamento estrito com a Seção 30 do `docs/FSD.md`.
   - Garantido que caminhos relativos ao projeto são utilizados, sem caminhos absolutos locais ou links `file:///` no corpo da documentação permanente.
2. **Testes Automatizados:**
   - Execução dos testes automatizados backend (`python backend/manage.py test core`) para assegurar integridade do ambiente.
3. **Commit Semântico Atômico:**
   - Commit realizado conforme a norma: `docs(governanca): incluir obrigatoriedade de commits por plano no ciclo operacional`.
