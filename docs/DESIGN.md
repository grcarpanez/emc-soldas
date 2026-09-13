---
name: Industrial Integrity
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1b1c1c'
  surface-container: '#1f2020'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353535'
  on-surface: '#e4e2e1'
  on-surface-variant: '#e0c0b5'
  inverse-surface: '#e4e2e1'
  inverse-on-surface: '#303030'
  outline: '#a78a81'
  outline-variant: '#58423a'
  surface-tint: '#ffb59c'
  primary: '#ffb59c'
  on-primary: '#5c1a00'
  primary-container: '#b7410e'
  on-primary-container: '#ffe2d9'
  inverse-primary: '#a93702'
  secondary: '#c0c8cd'
  on-secondary: '#2a3136'
  secondary-container: '#424a4f'
  on-secondary-container: '#b2b9bf'
  tertiary: '#c2c6d2'
  on-tertiary: '#2c3139'
  tertiary-container: '#646872'
  on-tertiary-container: '#e4e8f4'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#ffdbcf'
  primary-fixed-dim: '#ffb59c'
  on-primary-fixed: '#380c00'
  on-primary-fixed-variant: '#822800'
  secondary-fixed: '#dce4e9'
  secondary-fixed-dim: '#c0c8cd'
  on-secondary-fixed: '#151d21'
  on-secondary-fixed-variant: '#40484c'
  tertiary-fixed: '#dfe2ee'
  tertiary-fixed-dim: '#c2c6d2'
  on-tertiary-fixed: '#171c24'
  on-tertiary-fixed-variant: '#424750'
  background: '#131313'
  on-background: '#e4e2e1'
  surface-variant: '#353535'
typography:
  headline-xl:
    fontFamily: IBM Plex Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: IBM Plex Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: IBM Plex Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 14px
spacing:
  unit: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  container-max: 1440px
---

## Brand & Style
The design system is engineered for the heavy-duty world of welding and machine maintenance. It prioritizes reliability, structural strength, and technical precision. The visual language is inspired by industrial environments: steel workshops, blueprints, and high-performance machinery.

The style is a fusion of **Corporate Modern** and **Soft Brutalism**. It utilizes clean grid lines and sharp geometry to convey a sense of "built-to-last" engineering. Subtle metallic gradients and micro-textures provide a tactile, high-quality finish without sacrificing the functional clarity required for data-heavy management interfaces. The emotional response is one of absolute trust, safety, and professional competence.

## Colors
The palette is rooted in the materials of the trade. **Dark Iron (#2B2B2B)** serves as the primary canvas, providing a high-contrast, low-glare background suitable for industrial environments. **Steel Gray (#71797E)** and **Brushed Metal (#A5A9B4)** are used for structural elements, borders, and secondary surfaces to create depth through tonal layering.

**Rust Orange (#B7410E)** is the high-visibility accent color. It is used strategically for primary actions, critical status indicators, and highlights, echoing the heat of a weld or the importance of safety equipment. High-contrast white is reserved strictly for maximum readability of data and labels against the dark surfaces.

## Typography
The typography system uses a tiered technical approach. **IBM Plex Sans** is used for headlines to provide a structured, engineered feel with its unique terminals and technical curves. **Inter** handles the bulk of data and body text, chosen for its exceptional legibility in complex interfaces. 

For technical data, serial numbers, and machine specifications, **JetBrains Mono** is employed. The monospaced nature of the label font ensures that numerical data aligns perfectly in tables and technical readouts. High-weight headlines and uppercase labels create a clear information hierarchy that remains readable even in low-light or high-stress situations.

## Layout & Spacing
The layout follows a **Fixed Grid** philosophy with a rigorous 4px baseline shift. This "blueprint" precision ensures that all elements feel intentionally placed and structurally sound. 

On desktop, a 12-column grid is used with 16px gutters to maximize data density while maintaining scanability. Margins are generous at 32px to frame the content. On mobile devices, the system collapses to a 4-column grid with reduced margins. Elements should favor vertical stacking to maintain large tap targets, essential for users who may be operating in a mobile workshop environment.

## Elevation & Depth
Depth is communicated through **Tonal Layers and Bold Borders** rather than traditional soft shadows. This design system avoids "floating" elements, preferring a "bolted-down" look.

1.  **Base Layer:** Dark Iron (#2B2B2B) background.
2.  **Surface Layer:** Steel Gray (#71797E) for cards and containers, using a 1px solid border in Brushed Metal (#A5A9B4) to define edges.
3.  **Active Layer:** Elements that require interaction use a subtle vertical linear gradient (Light to Dark) to simulate a physical brushed-metal texture.

Instead of shadows, use "Inset" borders or 2px solid offsets to indicate depth and depression (e.g., when a button is pressed). This reinforces the heavy-duty, tactile nature of the UI.

## Shapes
The shape language is strictly **Sharp (0px roundedness)**. Every container, button, and input field features 90-degree corners to reflect the precision of metal cutting and machine fabrication. This lack of rounding emphasizes a serious, industrial-grade toolset. Structural integrity is visualised through thickness; use 1px or 2px borders consistently to frame content areas.

## Components
- **Buttons:** Primary buttons use a solid Rust Orange (#B7410E) fill with white uppercase JetBrains Mono text. Secondary buttons are "Ghost" style with a 1px Steel Gray border. All buttons have a hover state that increases the border thickness to 2px, simulating a mechanical engagement.
- **Input Fields:** Dark backgrounds with a 1px bottom-border only (Blueprint style) or a full 1px border. Focus states must use the Rust Orange color for the border and the caret.
- **Cards:** Sharp corners, Steel Gray background, with a subtle top-border highlight in Brushed Metal (#A5A9B4) to simulate light hitting a metal edge.
- **Lists & Tables:** High-density rows separated by 1px Dark Iron borders. Use JetBrains Mono for all numerical data within tables.
- **Status Chips:** Rectangular with no rounding. Use high-saturation colors (Safety Red, Caution Yellow, Success Green) but keep them within the industrial tonal range (slightly desaturated/darkened).
- **Maintenance Logs:** Use vertical "timeline" lines that look like structural beams to connect historical data points.

---

## Interactive Controls & Dimensional Consistency

Para garantir harmonia visual absoluta e alinhamento milimétrico em barras de controle, filtros e formulários em todo o sistema, os seguintes padrões de layout e dimensionamento são **normativos e mandatórios**:

### 1. Altura Canônica Universal dos Campos de Interação
Todos os controles interativos de nível padrão possuem altura externa total estritamente fixada em **42px**:
- **Altura Padrão:** `height: 42px; box-sizing: border-box !important;`
  - Textboxes / Inputs de texto (`.form-control`)
  - Seletores nativos (`select.form-control`)
  - Comboboxes pesquisáveis com autocomplete (`.emc-combobox-trigger`)
  - Comboboxes multi-seleção com flags (`.emc-multiselect-trigger`)
  - Botões primários, secundários e de ação (`.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`)
- **Controles Compactos / Small:** `height: 32px; box-sizing: border-box;` (utilizados em paginação, ações de tabela e modais de leitura densa: `.btn-sm`, `.form-control-sm`).
- **Chips Contadores e Badges de Barra:** Devem utilizar `height: 42px; box-sizing: border-box; display: inline-flex; align-items: center; padding: 0 12px;` quando posicionados em barras de filtros horizontais para acompanhar o alinhamento central.

### 2. Tipografia dos Controles
- **Entrada de Dados e Textos (Inputs, Selects e Comboboxes):**
  - Família tipográfica: `var(--font-body)` (`Inter`, sans-serif)
  - Tamanho da fonte: `14px`
  - Peso: `400` (inputs e selects) e `500` (triggers de combobox)
  - `line-height: normal` (evita distorções de altura vertical entre navegadores)
- **Ações, Rótulos Técnicos e Botões:**
  - Família tipográfica: `var(--font-mono)` (`JetBrains Mono`, monospace)
  - Tamanho da fonte: `13px` a `14px`
  - Peso: `600`
  - Transformação: `text-transform: uppercase;`
  - Espaçamento entre letras: `letter-spacing: 0.05em;`

### 3. Cores e Estados de Superfície
- **Estado Neutro / Repouso:**
  - Fundo: `var(--color-surface-container-low)` (`#1b1c1c`)
  - Borda: `1px solid var(--color-steel-gray)` (`#71797E`)
  - Texto / Ícone: `var(--color-on-surface)` (`#e4e2e1`)
  - Texto Placeholder / Vazio: `var(--color-on-surface-variant)` (`#e0c0b5`)
- **Estado de Foco / Aberto:**
  - Fundo: `var(--color-surface-container)` (`#1f2020`)
  - Borda: `2px solid var(--color-rust-orange)` (`#b7410e`)
  - Compensação interna: `padding: 0 13px;` para manter exatamente os `42px` externos sem saltos visuais no DOM
- **Estado Selecionado / Destaque de Múltiplos Itens:**
  - Trigger com múltiplos itens: `color: var(--color-rust-orange-bright)` (`#ff6b35;`), peso `600`
  - Item ativo no dropdown: `background-color: rgba(183, 65, 14, 0.25);`
  - Botões de cabeçalho da combobox (`[✓ TODOS]` e `[✕ LIMPAR]`): tipografia `JetBrains Mono` 11px, borda cinza e hover em Rust Orange

### 4. Barras de Ação e Filtros (Flex Container)
- **Estrutura padrão de barra de controle:**
  ```css
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
  width: 100%;
  ```
- **Campos elásticos:** O campo principal de pesquisa textual deve receber `flex: 1; min-width: 200px;` para preencher organicamente o espaço central livre.
- **Wrappers e Comboboxes:** Devem ter largura fixa ou controlada (ex: `width: 220px; min-width: 180px; flex-shrink: 0;`), garantindo que o texto nunca empurre ou quebre o alinhamento da linha em resoluções desktop normais.

---

## 5. Engenharia e Cálculo de Espaços para Modais e Formulários (Modal Spatial Budget)

Para eliminar transbordos, cortes de botões e deformações em janelas modais, todo modal construído no sistema obedece rigorosamente às seguintes diretrizes matemáticas e de engenharia de layout:

### 5.1 Regra do Teto Vertical (Vertical Budget Rule)
Todo modal opera com uma restrição máxima de **`max-height: 88vh`** (e `max-height: 94vh` em resoluções móveis/tablets), segregado em três camadas verticais invioláveis:
1. **Cabeçalho Fixo (`.modal-header`):**
   - Altura máxima: **52px** (`padding: 12px 20px;`).
   - Alinhamento vertical centralizado.
   - Botão de fechar (`.modal-close-btn`): **32px × 32px**, retangular rígido (`0px border-radius`), `display: inline-flex; align-items: center; justify-content: center;`, sem quebra de margem.
2. **Rodapé Fixo de Ações (`.modal-footer`):**
   - Altura máxima: **60px** (`padding: 12px 20px; gap: 10px;`).
   - `flex-shrink: 0;`: os botões de ação ("CANCELAR" e "CONFIRMAR/SALVAR") **jamais** podem ser empurrados para fora da viewport visível.
3. **Corpo com Rolagem Suave Autocontida (`.modal-body`):**
   - `flex: 1 1 auto; min-height: 0; overflow-y: auto; overflow-x: hidden;`
   - O scrollbar só se manifesta se o conteúdo ultrapassar a área útil interna, preservando o cabeçalho e os botões de rodapé sempre visíveis e operacionais.
   - Padding interno: **16px 20px**.

### 5.2 Densidade e Compactação de Formulários em Modais
- Em modais, o `.form-group` adota espaçamento compacto:
  - `margin-bottom: 10px;` (em vez dos 16px das telas abertas).
  - `gap: 4px;` entre o `.form-label` e o `.form-control`.
- **Proibição de Margens Redundantes:** É terminantemente proibido adicionar `margin-top` inline em wrappers de linha ou formulários dentro de modais. O distanciamento é governado exclusivamente pelas classes estruturais de grid (`.form-grid-2`, `.form-grid-3`, `.form-grid-compact`) com `gap: 10px; margin-bottom: 10px;`.
- **Banners Explicativos e Avisos:** Devem ter padding compacto (`padding: 8px 12px; margin-bottom: 12px; font-size: 11.5px; line-height: 1.4;`).

### 5.3 Proporções Funcionais de Grids em Modais
- Campos com dados curtos (Data, Hora, CEP, UF, Número de endereço, Valor) **nunca** devem receber partição `1fr` simétrica com campos de texto extenso (Categoria, Cliente, Descrição, Conta Bancária).
- Exemplos de proporções mandatórias:
  - `Categoria DRE` + `Data`: `grid-template-columns: 1fr 150px;`
  - `Conta Bancária` + `Meio de Pagamento`: `grid-template-columns: 1.2fr 1fr;`
  - `Documento/Tipo` + `Email`: `grid-template-columns: 1fr 2fr;`
  - `CEP` + `Logradouro` + `Número`: `grid-template-columns: 140px 1fr 100px;`

### 5.4 Obrigatoriedade de Responsividade Universal
- **Mandato Inegociável:** Todo componente, tela, tabela e modal construído no sistema **deve ser 100% responsivo**.
- **Colapso Automático de Grids:** Em larguras de tela de **768px ou menores**, todos os formulários e grids (`.form-grid-2`, `.form-grid-3`, `div[style*="grid-template-columns"]`) colapsam compulsoriamente para coluna única (`grid-template-columns: 1fr !important; gap: 10px !important;`).
- **Dimensões Fluidas de Modais:** Em dispositivos móveis e tablets (`<= 768px`), o `.modal-card` assume `width: 96vw; max-width: 96vw; max-height: 94vh; margin: auto;` com `overflow-x: hidden;`, garantindo que nenhum elemento transborde lateralmente.