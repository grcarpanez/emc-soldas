# Implementation Plan: Anexo de Comprovantes/NFs e Redesign da Mesa de Triagem (Split-Screen)

**Data:** 2026-09-15  
**Autor:** Antigravity AI  
**Status:** Concluído  
**Proceed do Usuário:** Aprovado explicitamente via comando "Execute o plano. Não se esqueça de documentar o plano" (15/09/2026).

---

## 1. Contexto e Objetivos

O sistema de conciliação bancária por extrato (Split-Screen) opera permitindo cruzamento de dados e geração em lote de lançamentos. O usuário solicitou duas melhorias essenciais:
1. **Anexo de Documentos/Comprovantes no Extrato:** Possibilidade de anexar Notas Fiscais (nas operações de entrada/recebimento) e Comprovantes de Pagamento (nas operações de saída/pagamento) diretamente em cada item da mesa de triagem.
2. **Reorganização Estrutural do Layout (Revisão da View Split-Screen):** Solucionar o desequilíbrio de altura entre a coluna do extrato (cards compactos de ~60px) e a coluna da mesa de triagem (cards "gordos" de ~140px-160px). Adicionar mais uma linha de anexo agravaria esse problema.

---

## 2. Decisões Técnicas e Arquiteturais Propostas

### UX/UI: Redesign para Cards Densos/Ultracompactos (Dense Card Design)
- **Compressão de Altura:** Compactação das informações do card de pré-lançamento de ~150px para ~72px de altura.
- **Linha 1 (Cabeçalho Integrado):**
  - Identificador & Data: `PRÉ-LANÇAMENTO #X • 02/06/2025`
  - Valor Formatado: `+ R$ 474,60` (Verde) / `- R$ 474,60` (Vermelho)
  - **Botão de Anexo Inline Contextual:** `[📎 + NF]` (para Recebimentos) ou `[📎 + RECIBO]` (para Pagamentos).
  - Badge de Confirmação: Quando o arquivo for selecionado, o botão se transforma em `[📎 NF_001.pdf ✕]`, **sem adicionar nenhuma linha vertical ao card**.
  - Botão de Descarte: `[✕]`
- **Linha 2 (Inputs em Grid Horizontal Flexível):**
  - Coluna 1: Input Descrição (Compacto)
  - Coluna 2: Select Meio de Pagamento (Compacto)
  - Coluna 3: Select Categoria DRE (Compacto)

### Backend (Django REST Framework & MySQL)
- **Entidade `LancamentoFinanceiro`:** Adição do campo `comprovante = models.FileField(upload_to='comprovantes/%Y/%m/', null=True, blank=True)` e `nome_arquivo_comprovante = models.CharField(max_length=255, null=True, blank=True)`.
- **Endpoint de Upload Temporário/Direto:** `POST /api/conciliacao/upload-comprovante/` com suporte a multipart/form-data.
- **Importação em Lote:** `POST /api/conciliacao/importacao-lote/` atualizado para receber a referência do arquivo no payload e vincular ao `LancamentoFinanceiro` gerado.

---

## 3. Arquivos Afetados

- `backend/apps/financeiro/models.py`
- `backend/apps/financeiro/serializers.py`
- `backend/apps/conciliacao/serializers.py`
- `backend/apps/conciliacao/views.py`
- `backend/apps/conciliacao/urls.py`
- `backend/apps/conciliacao/services.py`
- `frontend/assets/js/views/conciliacao-view.js`
- `frontend/assets/css/industrial-integrity.css`
- `frontend/sw.js`
- `frontend/index.html`

---

## 4. Relatório de Execução Pós-Conclusão

1. **Migrations:** Aplicada migration `financeiro.0005_lancamentofinanceiro_comprovante_and_more` com sucesso.
2. **Backend Endpoints:** Criado endpoint `POST /api/conciliacao/upload-comprovante/` e atualizado `executar_importacao_lote`.
3. **Frontend Redesign:** Renderização dos cards da mesa de triagem reestruturada para layout ultra-denso de 2 linhas (~72px de altura), alinhando visualmente com o extrato.
4. **Anexos Inline:** Botão micro-inline de anexo `[📎 + NF]` / `[📎 + RECIBO]` funcional, enviando arquivos via FormData e gerando badges verdes neon instantâneos.
5. **Versionamento PWA (Regra 12):** `CACHE_NAME` incrementado para `'emc-soldas-v4.32'` e tags no `index.html` atualizadas com `?v=4.32`.

