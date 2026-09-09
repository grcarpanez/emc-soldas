# Planejamento: Correção de Responsividade dos Flip Cards no Mobile (PWA v4.6)

## 1. Metadados
- **Data:** 2026-09-09
- **Autor:** Antigravity AI
- **Status:** Concluído (100%)
- **Registro do Proceed:** Aprovado via Artifact Review em 2026-09-09T19:51:19-03:00 ("The user has approved this document.")

---

## 2. Contexto e Objetivos
Na visualização em smartphones (largura de tela <= 480px) do Dashboard Operacional (/#dashboard), o primeiro card ("OPERAÇÃO DE OFICINA") apresentava vazamento visual do seu rodapé (.flip-card-footer, contendo "Aprovados" e "Ver detalhes ➔"). O rodapé vazava para fora do card, sobrepondo a borda inferior e invadindo o card logo abaixo.

### Causa Raiz
1. Em layout.css e industrial-integrity.css, a media query @media (max-width: 480px) forçava uma altura fixa de height: 155px (ou 160px).
2. O grid mobile é de 2 colunas (1fr 1fr), deixando os cards estreitos (~160px-180px).
3. No Card 1 ("OPERAÇÃO DE OFICINA"), o título ocupava 2 linhas com "GIRE ↻", o subtítulo ocupava 2 linhas, e somado com valor, padding e rodapé, a altura total necessária era de ~185px-190px, estourando a barreira de 155px.

---

## 3. Decisões Técnicas e Arquiteturais Executadas
1. Elevação da altura de .flip-card-wrapper em @media (max-width: 480px) para **195px** em layout.css e industrial-integrity.css.
2. Em @media (max-width: 480px):
   - Padding de .flip-card-front, .flip-card-back: 10px 8px; overflow: hidden;.
   - .flip-card-title: ont-size: 10px; margin-bottom: 4px; line-height: 1.2;.
   - .flip-card-sub: ont-size: 11px; line-height: 1.2;.
   - .flip-card-footer: padding-top: 6px; margin-top: 4px;.
   - .flip-card-btn-detail: ont-size: 10.5px;.
   - No verso (.flip-card-back): listas com ont-size: 11px; line-height: 1.4;.
3. Sincronização e versionamento PWA para 4.6 (rontend/sw.js e rontend/index.html).

---

## 4. Arquivos Modificados
- rontend/assets/css/industrial-integrity.css
- rontend/assets/css/layout.css
- rontend/sw.js
- rontend/index.html
- docs/STATUS.md

---

## 5. Relatório de Execução e Verificação Técnica
- Suíte de testes automatizados do Django (python backend/manage.py test apps.relatorios apps.financeiro): 30 testes aprovados (Ran 30 tests in 9.857s, OK).
- Commit semântico Git executado conforme Regra Mandatória 13 do AGENTS.md.
