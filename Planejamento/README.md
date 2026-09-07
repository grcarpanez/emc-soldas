# Diretório de Planejamento - EMC Soldas

Este diretório armazena o histórico perpétuo de todos os **Planos de Implementação (Implementation Plans)** elaborados e suas respectivas **aprovações do usuário (Proceed)**.

---

## Protocolo Obrigatório de Governança

1. **Antes de Qualquer Alteração no Código:**
   - A IA/desenvolvedor deve **obrigatoriamente e inevitavelmente** redigir um *Implementation Plan* completo antes de tocar em qualquer linha de código ou configuração.
   - O plano deve ser apresentado para que o usuário avalie e aprove formalmente.
   - Nenhuma linha de código ou arquivo de configuração pode ser modificado antes da aprovação explícita do usuário (`Proceed`).

2. **Registro e Salvamento na Pasta `Planejamento/`:**
   - Todo plano criado e aprovado deve ser arquivado neste diretório.
   - **Padrão de nomenclatura:** `YYYY-MM-DD_NN_nome_da_tarefa.md`
     - Exemplo: `2026-09-07_01_validacao_placas_e_governanca.md`
   - O documento arquivado deve conter:
     - **Objetivo / Descrição da Demanda**
     - **Decisões Técnicas e Arquiteturais**
     - **Arquivos a Modificar ou Criar**
     - **Plano de Verificação / Testes**
     - **Registro de Aprovação (Data, Hora e Feedback/Proceed do Usuário)**
     - **Status de Execução (Pendente, Em Andamento, Concluído)**

3. **Arquivos Vivos de Apoio:**
   - Ao término da execução, atualizar imediatamente:
     - `docs/STATUS.md` com a entrega detalhada na fase correspondente.
     - `docs/ERROS.md` caso ocorra qualquer imprevisto técnico, documentando sintoma, causa raiz, solução e prevenção.
