# Inventário de Insumos do Projeto

Este documento registra o inventário de todos os arquivos e insumos disponíveis na pasta `docs/` para o desenvolvimento do sistema **EMC Soldas**.

> **Nota de Governança:** A pasta `docs/` é estritamente destinada a documentação, apoio e referência técnica. Nenhum arquivo contido nesta pasta deve ser servido diretamente como pasta pública do sistema em execução. Durante a construção do sistema, arquivos que precisem ser servidos pelo frontend (como ícones PWA, logos ou fontes) serão devidamente incorporados à pasta de assets estáticos do Frontend PWA conforme definido no FSD.

---

## Tabela de Insumos

| Arquivo | O que é | Usado pelo sistema em execução? | Onde será usado | Observações |
|---|---|---|---|---|
| `docs/FSD.md` | Documento de Especificação Funcional e Técnica (FSD) consolidado | Não | Documentação / Guia da IA Codificadora | Contém a especificação completa de requisitos, arquitetura desacoplada (Django + DRF / PWA Vanilla), 29 tabelas MySQL, regras de negócio, endpoints REST e critérios de aceite. |
| `docs/DESIGN.md` | Guia de Identidade Visual e Design System (*Industrial Integrity*) | Não | Documentação / Referência visual para o CSS | Define tokens de cores (Dark Iron, Steel Gray, Rust Orange), tipografia técnica (IBM Plex Sans, Inter, JetBrains Mono), geometria sem cantos arredondados (0px border-radius) e estilo de componentes. |

---

## Observações sobre Insumos Complementares Futuros (Assets de Execução)

- **Logomarca da Empresa:** Na V1, a URL/caminho da logo da oficina é configurável pelo Administrador através do painel de Configurações Globais (`Configuracoes_Globais.logo_empresa_url`) e armazenada na entidade correspondente.
- **Ícones do PWA e Manifest:** Para o funcionamento como Progressive Web App (PWA), serão gerados e alocados no diretório estático do Frontend PWA os arquivos `manifest.json`, `service-worker.js` e os ícones padronizados para instalação (ex: `icon-192.png`, `icon-512.png`).
- **Fontes Tipográficas:** As fontes definidas no Design System (**IBM Plex Sans**, **Inter** e **JetBrains Mono**) serão consumidas via Google Fonts ou importadas no CSS do Frontend PWA.
