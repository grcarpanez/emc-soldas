# Planejamento: Calibração do Modal, Máscara da Chave NF-e e Extração Garantida de Nº da Nota

- **Data:** 2026-09-10
- **Autor:** Antigravity (Pair Programming)
- **Status:** Concluído
- **Registro do Proceed do Usuário:** 2026-09-10 12:30:48-03:00 - "The user has approved this document."

---

## 1. Contexto e Objetivos

Após a implementação da extração determinística de dados de DANFE (PDF e XML) e cruzamento cadastral prévio, testes com documentos reais evidenciaram três pontos de melhoria:
1. **Layout e Padding do Modal de Confirmação:** O modal de confirmação ("FORNECEDOR NÃO ENCONTRADO" e "HABILITAR PARCEIRO") usava `size: 'sm'` (420px), fazendo com que os botões "DEIXAR PARA DEPOIS" e "CADASTRAR FORNECEDOR" ficassem colados nas margens sem respiro suficiente.
2. **Preenchimento de Nº da Nota e Chave após Cadastro:** Em arquivos como NFS-e municipais ou recibos (ex.: `NFSe 10 Associação.pdf`), a ausência de chave de 44 dígitos impedia a extração do número da nota. Além disso, ao abrir o modal de cadastro de fornecedor e concluí-lo com sucesso, os dados extraídos precisavam ser reaplicados nos campos do formulário da nota.
3. **Máscara da Chave de Acesso NF-e:** A chave extraída de arquivos XML era inserida como uma sequência contínua de 44 dígitos devido à chamada de um método com nome incorreto (`formatarChaveNFe` em vez de `formatarChaveAcessoNfe`), necessitando de formatação em grupos de 4 dígitos.
4. **Escopo Futuro (Itens da Nota / BOM):** Registrar formalmente que a conciliação automática de itens da nota com o catálogo fica adiada para versão futura.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Modal e Estilos:**
   - Ampliar o tamanho padrão de `.modal-size-sm` de `420px` para `480px` para respiro geral.
   - Ajustar `.modal-footer` com `padding: 16px 24px`, `flex-wrap: wrap` e `align-items: center`.
   - Modificar os modais de diálogo em `compras-view.js` de `size: 'sm'` para `size: 'md'` (640px).
2. **Extração de Nº de Nota em PDFs:**
   - Adicionar regex específico para NFS-e e notas sem DANFE 55 padrão:
     `r'(?:NFS-e\s*N[º°\.\s]*|N[º°\.\s]+|Número\s*(?:da\s*Nota)?\s*[:º°\.\s]*|NOTA\s+FISCAL[^\d\n\r]*)\s*(\d{1,9})\b'`
   - Adicionar fallback para extrair número do nome do arquivo (`arquivo.name`).
3. **Frontend Compras:**
   - Corrigir a chamada para `window.EMCUtils.formatarChaveAcessoNfe(dados.chave_acesso)` e disparar o evento `input`.
   - Salvar `this.dadosExtraidosTemp = dados` e reaplicar no `onSuccess` do cadastro de novo fornecedor.
4. **Versionamento do PWA:**
   - Atualizar `CACHE_NAME` para `'emc-soldas-v4.12'` em `frontend/sw.js` e atualizar os sufixos em `frontend/index.html` para `?v=4.12`.

---

## 3. Arquivos Afetados

- `backend/apps/compras/services.py`
- `frontend/assets/css/industrial-integrity.css`
- `frontend/assets/js/views/compras-view.js`
- `frontend/sw.js`
- `frontend/index.html`
- `docs/STATUS.md`

---

## 4. Plano de Verificação

- Testes automatizados do Django via `python backend/manage.py test backend/`.
- Verificação do layout visual e formatação de chave no navegador.

---

## 5. Relatório de Execução (Pós-Conclusão)

- **Extração em Services:** Adicionadas regras determinísticas de extração de número de nota fiscal para documentos sem chave de 44 dígitos e fallback pelo nome do arquivo.
- **Design System:** `.modal-size-sm` calibrado para 480px e `.modal-footer` enriquecido com respiro amplo de 24px nas laterais e wrap flexível.
- **Frontend Compras:** Modais de diálogo passaram para tamanho `md` (640px); chave de acesso NFe agora formatada com `formatarChaveAcessoNfe` (blocos de 4 dígitos); preenchimento dos campos re-executado com sucesso após o fechamento do modal de cadastro de parceiro.
- **Suíte de Testes:** 165 testes automatizados do Django executados com 100% de aprovação (OK).
- **Versionamento PWA:** Sincronizado para `v4.12` em `sw.js` e `index.html`.