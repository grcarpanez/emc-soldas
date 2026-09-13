# Planejamento: Normatização de Espaços e Responsividade Mandatória de Modais (Industrial Integrity) e Reestruturação do Modal de Lançamento no Extrato Real

- **Data:** 2026-09-13
- **Autor:** Antigravity AI
- **Status:** Concluído
- **Registro do Proceed do Usuário:** Aprovado em 13/09/2026 11:54:43 (Perfeito. Plano aprovado. Adiciona o DESIGN.md também, a obrigatoriedade da responsividade.)

---

## 1. Contexto e Objetivos

1. **Problema Reportado:** No modal de "Novo Lançamento Avulso no Extrato (Caixa Real)", os elementos transbordaram a tela e ficaram cortados (campos de conta bancária, meio de pagamento cortado na lateral direita e base oculta). O botão X de fechar ficou desalinhado na moldura superior direita.
2. **Diretriz do Usuário:** Instituir regra mandatória de cálculo de espaços para criação de qualquer modal e registrar no docs/DESIGN.md a obrigatoriedade de responsividade para todos os componentes e modais, evitando correções manuais pontuais e garantindo encaixe visual perfeito em qualquer resolução.
3. **Escopo da Entrega:**
   - Atualização do docs/DESIGN.md com a Seção 5: "Engenharia e Cálculo de Espaços para Modais e Formulários (Modal Spatial Budget)" e a regra de "Obrigatoriedade de Responsividade Universal".
   - Atualização do CSS (`frontend/assets/css/industrial-integrity.css`) com isolamento de altura do modal (`max-height: 88vh; overflow: hidden;`), modal-body com `min-height: 0; flex: 1 1 auto; overflow-y: auto;`, compactação de margens verticais (`.modal-body .form-group { margin-bottom: 10px; gap: 4px; }`), alinhamento do botão de fechar e correção da classe `.modal-card` na media query `@media (max-width: 768px)`.
   - Reestruturação do modal em `frontend/assets/js/views/financeiro-view.js` com proporções funcionais de grid (`size: 'lg'`, eliminação de `margin-top` redundantes, data com largura intrínseca e distribuição equilibrada de conta e meio de pagamento).
   - Ajuste estrutural do botão de fechar em `frontend/assets/js/utils.js`.
   - Atualização de cache PWA (`sw.js` para `v4.17` e `index.html` para `?v=4.17`).
   - Execução de testes automatizados e atualização de `docs/STATUS.md`.

---

## 2. Decisões Técnicas e Arquiteturais

1. **Teto Vertical Mandatório (Vertical Budget Rule):**
   - Todo modal possui altura visível contida em `max-height: 88vh` (notebooks e desktops) e `max-height: 94vh` (telas <= 768px).
   - Três camadas rígidas:
     - `modal-header`: Fixo, altura max 52px, padding `12px 20px`, botão fechar com `32px x 32px` e centralização flex.
     - `modal-footer`: Fixo, altura max 60px, padding `12px 20px`, `flex-shrink: 0`, botões sempre visíveis.
     - `modal-body`: Rolagem independente com `flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden; padding: 16px 20px;`.
2. **Compactação Vertical em Modais:**
   - `.modal-body .form-group` recebe `margin-bottom: 10px; gap: 4px;` (em vez dos 16px e 6px da página aberta).
   - Proibição de `margin-top` inline em wrappers de linha.
3. **Proporções Funcionais de Grid:**
   - Campos curtos (Data, Hora, CEP, UF, Valor monetário curto) usam larguras nominais (`140px` - `160px`) ou frações menores em vez de `1fr` simétrico com campos de texto longo.
4. **Responsividade Universal Obrigatória:**
   - Todos os modais e formulários devem colapsar de 2/3/4 colunas para coluna única (`1fr`) abaixo de 768px, sem quebra lateral ou transbordo horizontal (`overflow-x: hidden`).

---

## 3. Arquivos Modificados

- `docs/DESIGN.md` [MODIFY]
- `frontend/assets/css/industrial-integrity.css` [MODIFY]
- `frontend/assets/js/utils.js` [MODIFY]
- `frontend/assets/js/views/financeiro-view.js` [MODIFY]
- `frontend/assets/js/views/administracao-view.js` [MODIFY]
- `frontend/sw.js` [MODIFY]
- `frontend/index.html` [MODIFY]
- `docs/STATUS.md` [MODIFY]

---

## 4. Relatório de Execução e Evidências

1. **Design System & Normatização:**
   - Criada a Seção 5 no `docs/DESIGN.md`: Engenharia e Cálculo de Espaços para Modais e Formulários (Modal Spatial Budget), estipulando alturas máximas, densidade compacta de campos e o mandato de Responsividade Universal Obrigatória.
2. **Engenharia de CSS:**
   - `.modal-card` blindado com `max-height: 88vh; min-height: 0; overflow: hidden;`.
   - `.modal-body` com `flex: 1 1 auto; min-height: 0; overflow-y: auto;` eliminando qualquer transbordo do rodapé para fora da viewport.
   - `.modal-close-btn` padronizado em 32x32px com ícone centralizado `✕`, cantos retos (0px border-radius) e sem colisão visual na moldura.
   - Media query `@media (max-width: 768px)` corrigida de `.modal-dialog` para `.modal-card` com `width: 96vw; max-width: 96vw; max-height: 92vh; margin: auto;` e colapso compulsório de grids para coluna única (`1fr !important; gap: 10px !important;`).
3. **Reestruturação dos Modais no Frontend:**
   - Modal de Novo Lançamento no Extrato (`financeiro-view.js`): configurado com `size: 'lg'`, grid funcional `1fr 160px` para Categoria + Data, `1.2fr 1fr` para Conta + Meio de Pagamento, eliminação de `margin-top` inline e banner de Regime de Caixa compacto.
   - Modal de Edição de Lançamento (`financeiro-view.js`) e Modal de Categoria Financeira (`administracao-view.js`): ajustados e compactados conforme o novo padrão.
4. **Bateria de Testes Automatizados:**
   - Executada a suíte completa de 175 testes do Django (`manage.py test backend/`): 100% de aprovação (`Ran 175 tests in 66.431s. OK`).
5. **Versionamento e Cache PWA:**
   - `frontend/sw.js` atualizado para `emc-soldas-v4.17`.
   - `frontend/index.html` atualizado com query strings `?v=4.17`.
