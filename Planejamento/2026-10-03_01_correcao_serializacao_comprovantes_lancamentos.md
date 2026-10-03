# Plano de Implementação - Correção da Serialização de Comprovantes em Lançamentos Financeiros

**Data:** 2026-10-03  
**Autor:** Antigravity  
**Status:** Concluído  
**Registro de Aprovação (Proceed):** Aprovado pelo usuário em 2026-10-03 00:24:57 com a mensagem: *"Ficou claro sim. Obrigado. Pode executar o plano"*

---

## 1. Contexto e Objetivos

Ao tentar anexar um comprovante ou Nota Fiscal (ex: NFS-e de serviços prestados para a Cavenge Construções Ltda) a um lançamento de recebimento no Caixa Real / Extrato da Tesouraria, o sistema disparou o seguinte erro:
`"Erro ao anexar comprovante: COMPROVANTE: O dado submetido não era um arquivo. Cheque o tipo de codificação no formulário."`

O objetivo desta tarefa é permitir que o `LancamentoFinanceiroSerializer` receba e valide perfeitamente tanto arquivos físicos diretos quanto caminhos relativos de arquivos já persistidos pelo endpoint de upload (`/api/conciliacao/upload-comprovante/`), bem como valores nulos para desvinculação, garantindo que o vínculo seja salvo no MySQL com integridade e a URL seja entregue pronta para consumo do frontend.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Criação do Campo `ComprovanteFileOrCharField`:**
   - Subclasse de `serializers.FileField` em `backend/apps/financeiro/serializers.py`.
   - Em `to_internal_value(data)`:
     - Aceita `None` ou string vazia (retorna `None`).
     - Aceita `str`: remove prefixos desnecessários (como `/media/` ou URLs completas) e retorna o caminho relativo limpo (ex: `comprovantes/2026/10/nota_fiscal.pdf`).
     - Para outros tipos (ex: `UploadedFile` binário), delega para `super().to_internal_value(data)`.
   - Em `to_representation(value)`:
     - Se o valor salvo no banco for uma string pura sem protocolo/prefixo, adiciona `/media/` garantindo URL pronta para navegação.

2. **Declaração Explícita no `LancamentoFinanceiroSerializer`:**
   - Declarar explicitamente os campos `comprovante` e `nome_arquivo_comprovante` na classe do serializer com `required=False` e `allow_null=True`.

3. **Testes Automatizados:**
   - Implementar testes no `backend/apps/financeiro/tests.py` cobrindo PATCH com caminho de comprovante, remoção com valor nulo, criação com comprovante e serialização de URL na saída.

---

## 3. Arquivos Afetados

- `backend/apps/financeiro/serializers.py`
- `backend/apps/financeiro/tests.py`
- `Planejamento/2026-10-03_01_correcao_serializacao_comprovantes_lancamentos.md`
- `docs/STATUS.md`
- `docs/ERROS.md`

---

## 4. Plano de Verificação e Testes

1. Executar os testes automatizados do app financeiro:
   `python backend/manage.py test apps.financeiro`
2. Executar os testes automatizados da conciliação:
   `python backend/manage.py test apps.conciliacao`
3. Executar a suíte completa de testes:
   `python backend/manage.py test backend/`

---

## 5. Relatório de Execução

- **Implementação do Campo Híbrido:**
  - Implementado `ComprovanteFileOrCharField(serializers.FileField)` em `backend/apps/financeiro/serializers.py`.
  - Declarado explicitamente `comprovante` e `nome_arquivo_comprovante` no `LancamentoFinanceiroSerializer`.
- **Validação com Testes Automatizados:**
  - Adicionados testes `test_anexo_e_remocao_comprovante_via_patch_lancamento` e `test_criacao_lancamento_com_comprovante` em `backend/apps/financeiro/tests.py`.
  - Testes do app financeiro: 27 testes aprovados (100%).
  - Testes do app conciliação: 13 testes aprovados (100%).
  - Suíte completa do backend: 188 testes executados e aprovados com 0 falhas e 0 erros.
- **Evidência de Resolução do Incidente:**
  - A requisição `PATCH /api/lancamentos-financeiros/{id}/` aceita agora perfeitamente o payload `{ "comprovante": "comprovantes/...", "nome_arquivo_comprovante": "..." }`, eliminando o erro de validação `"O dado submetido não era um arquivo"`.

