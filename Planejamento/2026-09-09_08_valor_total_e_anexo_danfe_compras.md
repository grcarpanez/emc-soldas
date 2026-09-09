# 2026-09-09_08 - Envio Automático de Valor Total e Upload da DANFE em Compras

## Metadados
- **Data:** 2026-09-09
- **Autor:** Antigravity (Google DeepMind)
- **Status:** Concluído
- **Registro do Proceed:** Aprovado pelo usuário em 2026-09-09T20:31:25-03:00 com ênfase em segurança no header e validações rigorosas de upload.

---

## 1. Contexto e Diagnóstico

1. **Erro no Salvamento da Nota de Compra:** O frontend calculava visualmente o total, mas não injetava o campo alor_total no payload JSON em compras-view.js. O DRF rejeitava a chamada com erro VALOR_TOTAL: Este campo é obrigatório.
2. **Anexo da DANFE no FSD e no Backend:** O docs/FSD.md (Seção 6 e Tabela 24) e o PRD.md especificam o arquivamento da DANFE (PDF) ou XML da NFe nas compras. O modelo DocumentoFiscalCompra possui o campo caminho_arquivo_anexo. Faltava expor a interface no modal e o botão de download na listagem.

---

## 2. Decisões Técnicas e Arquiteturais de Segurança

1. **Blindagem Dupla do alor_total:**
   - Frontend: calcular a soma dos subtotais dos itens e enviar alor_total no payload.
   - Backend: tornar alor_total opcional no serializer; se omitido, calcular automaticamente via sum(quantidade_comprada * valor_unitario).
2. **Hardening Rigoroso de Upload de Arquivos (Regra 10 do AGENTS.md):**
   - **Verificação de Magic Bytes / File Header:** Validação dos primeiros bytes do arquivo (ex: %PDF para PDF, \x89PNG para PNG, \xff\xd8\xff para JPG).
   - **Proteção contra XML External Entity (XXE) e Billion Laughs:** Parser seguro de XML proibindo DTDs externos e entidades recursivas.
   - **Sanitização Estrita de Nome de Arquivo (Path Traversal & Null Bytes):** Remoção de caracteres fora de [a-zA-Z0-9_.-], impedindo travessia de diretório (../) ou injeção de byte nulo (\x00).
   - **Isolamento NoExec e Hash de Nome Único:** Armazenamento em diretório NoExec com timestamp + sanitized filename.
   - **Limite de Tamanho:** Restrição estrita de 20MB.
   - **Content-Type e Content-Disposition forçados no download:** ttachment; filename=... com X-Content-Type-Options: nosniff para evitar ataques de MIME-sniffing.
3. **Interface e Versionamento PWA (Regra 12):**
   - Campo de anexo da DANFE no modal de compra.
   - Botão de download na tabela principal (📄 DANFE) e nos detalhes da nota.
   - Versão PWA elevada para 4.9 em sw.js e index.html.

---

## 3. Relatório de Execução e Evidências

1. **Backend (pps/compras/serializers.py & services.py):**
   - Campo alor_total tornado opcional no serializer e auto-calculado com base nos itens da nota.
   - Função alidar_arquivo_anexo_compra com inspeção de cabeçalhos binários (magic bytes), proteção anti-path traversal/null-bytes e bloqueio estrito de XXE/DTD em XMLs.
2. **Frontend (compras-view.js):**
   - Inclusão do cálculo automático do alor_total no payload JSON do modal.
   - Campo de seleção de arquivo da DANFE/XML no formulário.
   - Upload automático via FormData para o endpoint seguro /anexar-arquivo/.
   - Botão 📄 DANFE na listagem de notas e nos detalhes da compra disparando download seguro via Blob.
3. **Versionamento PWA:**
   - Cache elevado para emc-soldas-v4.9 em sw.js e sufixos de cache-busting ?v=4.9 em index.html.
4. **Suíte de Testes Automatizados Django:**
   - 163 testes executados e **100% aprovados (OK em 65.1s)**, incluindo 2 novos testes específicos de segurança e auto-cálculo.
