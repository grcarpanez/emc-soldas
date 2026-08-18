# Mapeamento Estrutural do Sistema e Comportamento de Permissões (UI/UX)

Este documento atua como um laboratório ("Draft") para mapear exaustivamente quais telas e funcionalidades pertencem a cada um dos 10 módulos da Matriz de Permissões, e definir exatamente como a Interface (PWA) vai reagir caso o usuário não tenha acesso àquela área. Após a revisão e aprovação, este conteúdo será integrado ao **FSD.md**.

---

## 1. Regra Geral de Comportamento Visual (Abordagem Híbrida)

O sistema lidará com o bloqueio de permissões combinando **Ocultação Total** e **Bloqueio Visual**, dependendo do contexto da interface para manter o layout íntegro e a experiência limpa:

- **Menus Laterais (Sidebar) e Abas Inteiras:** Ocultação Total. Se o módulo está bloqueado, o link sequer renderiza no menu.
- **Botões de Ações Críticas (Ex: Lixeira/Excluir):** Ocultação Total. O botão não é desenhado na tela.
- **Flip Cards do Dashboard:** Bloqueio Visual (Mascara e Cadeado). O card renderiza para não quebrar a simetria da tela, mas seus valores ficam censurados (ex: `R$ ***,**`) e o botão de "Ver Detalhes" fica cinza com ícone de cadeado `[🔒]`.
- **Botões Integrados / Atalhos Cruzados:** Bloqueio Visual (Desabilitado). Se um operador está na tela de Faturas e há um atalho de "Ir para Conta Bancária" (da qual ele não tem permissão), o botão fica visível (para manter o layout da tabela), porém cinza/desabilitado com um tooltip: *"Acesso restrito ao módulo de..."*

---

## 2. Mapeamento Módulo a Módulo

Abaixo está a quebra dos 10 módulos (os mutáveis e os fixos, para preparar o sistema caso níveis futuros de administração sejam criados).

### 2.1. Orçamentos, Faturas e Clientes (Módulo Operacional)
- **Telas Pertencentes:** Menu "Operação" (Orçamentos, Faturamento, Clientes, Equipamentos).
- **Funcionalidades Cobertas:** Criar clientes e veículos, gerar orçamentos, inserir itens no orçamento, aprovar orçamento, gerar pré-fatura, aglutinar faturas, aplicar descontos comerciais, gerar PDF para o cliente.
- **Comportamento da UI se Acesso Negado:**
  - *Menu Lateral:* Menu principal "Operação" some.
  - *Dashboard:* Flip Cards de "Operação" e "Faturamento" mascarados e trancados 🔒.
  - *Atalhos Rápidos (Dashboard):* Botões "Novo Orçamento" e "Novo Cliente" somem.

### 2.2. Tesouraria (Caixa, Conciliação, Estornos)
- **Telas Pertencentes:** Menu "Tesouraria" (Contas a Pagar, Contas a Receber, Extrato Real, Conciliação Bancária, Cartões Corporativos).
- **Funcionalidades Cobertas:** Registrar pagamento em faturas, liquidar despesas, transferências entre contas, importar OFX/CSV, realizar match de conciliação, realizar estornos (com justificativa), visualizar linha do tempo de faturas de cartão, e realizar pagamentos totais ou parciais de faturas de cartão.
- **Comportamento da UI se Acesso Negado:**
  - *Menu Lateral:* Menu "Tesouraria" some.
  - *Dashboard:* Flip Card de "Caixa (Saldo Real)" mascarado e trancado 🔒. Botão "Lançar Despesa" some.
  - *Atalhos Cruzados:* Dentro de Faturas (que o operador pode ter acesso pelo módulo 1), o botão "Liquidar Pagamento" fica cinza/desabilitado 🔒.

### 2.3. Compras (Entrada de Notas Fiscais)
- **Telas Pertencentes:** Menu "Compras" (Registro de Notas de Entrada).
- **Funcionalidades Cobertas:** Digitar chave da nota, vincular fornecedor, cadastrar itens comprados, validar inflação de itens, anexar XML/PDF da nota.
- **Comportamento da UI se Acesso Negado:**
  - *Menu Lateral:* Menu "Compras" some.

### 2.4. Catálogo Base (Itens, Produtos e Preços)
- **Telas Pertencentes:** Menu "Catálogo" (Materiais/Itens e Receitas/Produtos).
- **Funcionalidades Cobertas:** Criar novos itens base (com fator de conversão opcional para itens de uso geral não-produtivos), montar ficha técnica (BOM) para novos produtos, editar custo/snapshot manual.
- **Comportamento da UI se Acesso Negado:**
  - *Menu Lateral:* Submenu "Catálogo de Itens" e "Produtos" somem.
  - *Atalhos Cruzados:* Dentro do Orçamento, ao buscar um item, o botão "Cadastrar Novo Item Rápido" fica desabilitado 🔒. Ele só pode usar o que já existe.

### 2.5. Relatórios, Dashboards e DRE
- **Telas Pertencentes:** Menu "Relatórios" (Curvas ABC, Inadimplência, Dossiê Histórico, DRE Simplificado).
- **Funcionalidades Cobertas:** Gerar cruzamentos de dados, emitir relatório de Débitos, exportar planilhas gerenciais em CSV.
- **Comportamento da UI se Acesso Negado:**
  - *Menu Lateral:* Menu "Relatórios" some inteiramente.
  - *Dashboard:* O Gráfico de Barras Duplas (Receitas x Despesas) no rodapé do Dashboard some (fica apenas o Feed de Atividades cobrindo o espaço, ou o espaço fica em branco).

### 2.6. Cadastros Financeiros Estruturais (Contas e Regras)
- **Telas Pertencentes:** Menu "Configurações" -> Abas (Contas Bancárias, Regras de Pagamento, Categorias Financeiras, Cartões Corporativos).
- **Funcionalidades Cobertas:** Criar novas gavetas bancárias (ex: "Itaú", "Caixa Interno"), cadastrar parcelamentos (ex: "3x Sem Juros"), criar categorias (ex: "Luz", "Internet").
- **Comportamento da UI se Acesso Negado:**
  - *Menu Lateral:* Essas abas desaparecem do menu de configurações.
  - *Regra Funcional:* O Operador continua usando as contas e regras (elas aparecem nos dropdowns na hora de fechar orçamentos e pagar contas), ele apenas não pode acessar o painel de criação/edição delas.

### 2.7. Dicionário Central (UOM e Atributos) — *Fixo Admin*
- **Telas Pertencentes:** Menu "Configurações" -> Dicionário UOM.
- **Funcionalidades Cobertas:** Travar a raiz das unidades de medidas (Litros, cm, kg) para o fator de conversão.
- **Comportamento da UI se Acesso Negado:** Abas de configurações somem.

### 2.8. Configurações Globais e Parâmetros — *Fixo Admin*
- **Telas Pertencentes:** Menu "Configurações Globais".
- **Funcionalidades Cobertas:** Mudar margens lógicas, taxa de mão de obra hora, tempo de expiração do JWT (Sessão), retenção de logs.
- **Comportamento da UI se Acesso Negado:** A aba sequer existe.

### 2.9. Equipe, Permissões Dinâmicas e Senhas — *Fixo Admin*
- **Telas Pertencentes:** Menu "Equipe" ou "Controle de Acesso".
- **Funcionalidades Cobertas:** Convidar novos funcionários, alterar Matriz de Permissões (ligar/desligar toggles dos módulos de 1 a 6), forçar desbloqueio de brute-force (Rate Limit).
- **Comportamento da UI se Acesso Negado:** Acesso proibido. Para o operador normal, existirá apenas um botão no canto superior direito "Meu Perfil -> Mudar Senha".

### 2.10. Logs do Servidor e Hard Recovery — *Fixo Admin*
- **Telas Pertencentes:** Menu "Configurações" -> "Auditoria e Logs" / "Lixeira Global".
- **Funcionalidades Cobertas:** Ver log físico de erro do servidor na UI, restaurar orçamentos e faturas apagados por OUTROS funcionários.
- **Comportamento da UI se Acesso Negado:** Acesso restrito. O operador terá acesso apenas à sua própria lixeira pessoal para recuperar itens que ele mesmo apagou (se a regra do sistema permitir apagar).
