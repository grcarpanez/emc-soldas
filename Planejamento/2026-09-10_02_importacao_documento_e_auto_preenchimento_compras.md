# 2026-09-10_02 - Importação Inteligente de Documento Fiscal (DANFE/XML) com Pré-Preenchimento Automático em Compras

## Metadados
- **Data:** 2026-09-10
- **Autor:** Antigravity (Google DeepMind)
- **Status:** Concluído
- **Registro do Proceed:** Aprovado pelo usuário em 2026-09-10 com as diretrizes mandatórias:
  1. Extrair estritamente os campos existentes no formulário (CNPJ emitente, num_nota, data_compra, chave_acesso, valor_total e razao_social se não cadastrado).
  2. Limpar caracteres tanto do banco quanto do arquivo para comparar somente os dígitos do CNPJ (\d{14}).
  3. Se existir, retornar o ID do parceiro para selecionar na combobox.
  4. Descartar campos inexistentes na modelagem (como série da nota).

---

## 1. Contexto e Objetivos

Transformar o lançamento de compras em um fluxo ágil, inteligente e com preenchimento assistido a partir do arquivo importado (DANFE em PDF ou XML da NF-e).
Ao abrir o modal de compras:
1. O primeiro campo em destaque é a importação do documento fiscal (PDF/XML).
2. O sistema faz a leitura e extração estruturada dos dados:
   - Chave de Acesso (44 dígitos);
   - CNPJ do Emitente;
   - Número da Nota Fiscal;
   - Data de Emissão;
   - Valor Total da Nota;
   - Insumos/Itens comprados (no caso de XML).
3. O sistema verifica a situação cadastral do CNPJ:
   - **Se já cadastrado como Fornecedor (ou Ambos):** seleciona automaticamente o fornecedor na combobox e preenche todos os campos.
   - **Se já cadastrado apenas como Cliente:** questiona se deseja habilitá-lo também como Fornecedor. Em caso afirmativo, atualiza o tipo para 'Ambos' sem duplicar o cadastro e preenche a nota.
   - **Se não cadastrado:** oferece cadastrar agora. Em caso afirmativo, abre o modal de cadastro empilhado com os dados já preenchidos e consulta pública automática para conferência; ao salvar, seleciona o novo fornecedor e preenche a compra.
   - **Se o usuário recusar em qualquer etapa:** o arquivo permanece anexado e o modal é liberado para edição manual livre.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Dependência Python para Leitura de PDF:**
   - Adicionar pypdf>=4.0.0 ao ackend/requirements.txt (licença BSD 3-Clause, 100% gratuita para uso comercial e vendas).
2. **Endpoint Seguro de Análise Prévia de Documento:**
   - Criar POST /api/documentos-fiscais-compra/analisar-documento/ recebendo o arquivo via multipart/form-data.
   - Executa inspeção rigorosa de Magic Bytes, proteção anti-XXE e limites de tamanho.
   - Faz o parse de PDF ou XML e retorna JSON com:
     - chave_acesso, cnpj_emitente, 
um_nota, data_emissao, alor_total, azao_social_emitente, itens_extraidos e parceiro_existente (id, nome_razao, tipo).
3. **Endpoint Rápido para Habilitar Fornecedor:**
   - Criar POST /api/clientes-fornecedores/{id}/habilitar-fornecedor/ que altera o tipo para 'Ambos' caso o parceiro seja 'Cliente', disparando log de auditoria.
4. **Interface no Frontend (compras-view.js):**
   - Mover a área de importação de arquivo para o topo absoluto do modal com visual destacado e feedback de carregamento.
   - Integração com fluxo de modais empilhados e diálogos de confirmação usando EMCUtils.openModal.
5. **Versionamento PWA (Regra 12):**
   - Atualizar versão no sw.js para 'emc-soldas-v4.11'.
   - Atualizar sufixos ?v=4.11 em index.html.
