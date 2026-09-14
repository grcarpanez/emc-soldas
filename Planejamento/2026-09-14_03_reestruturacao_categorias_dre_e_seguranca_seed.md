# Plano de Implementação: Reestruturação de Categorias DRE, Higienização de Testes (C1) e Segurança do Seeder

**Metadados:**
- **Data de Criação:** 14/09/2026
- **Status:** Concluído
- **Aprovação do Usuário (Proceed):** Aprovado em 14/09/2026 às 15:30:40 pelo usuário via interface de artefatos.

---

## 1. Contexto e Objetivos

1. **Reestruturação das Categorias DRE:**
   - Eliminar a menção a (MAO DE OBRA) em receitas para refletir o faturamento integral da prestação de serviços.
   - Criar categorias distintas para AQUISIÇÃO DE MÁQUINAS E EQUIPAMENTOS (Investimento / Ativo Imobilizado) separada de MANUTENÇÃO DE MÁQUINAS E INSTALAÇÕES (Custo de reparo).
   - Segregar rigorosamente FOLHA DE PAGAMENTO (SALÁRIOS), ENCARGOS TRABALHISTAS (FGTS/INSS), PRÓ-LABORE DOS SÓCIOS e DISTRIBUIÇÃO DE LUCRO / RETIRADA DOS SÓCIOS.
   - Segregar IMPOSTOS E TRIBUTOS (SIMPLES NACIONAL / ISS / TAXAS) de encargos da folha.
2. **Higienização do Banco de Dados:**
   - Excluir definitivamente as categorias residuais C1 (IDs 12 e 13) criadas durante testes do formulário.
   - Atualizar a base de dados com as 20 categorias oficiais.
3. **Segurança de Credenciais no Seeder (seed_initial_data.py):**
   - Eliminar senha e PIN estáticos rígidos no código-fonte, adotando leitura via variáveis de ambiente (INITIAL_ADMIN_PASSWORD e INITIAL_ADMIN_PIN) com fallback seguro para ambiente de desenvolvimento local.
4. **Inteligência de Conciliação Bancária:**
   - Atualizar os motores de classificação heurística em pps/conciliacao/services.py para mapear automaticamente lançamentos do extrato OFX para as novas categorias oficiais.

---

## 2. Decisões Técnicas e Arquiteturais

### 2.1 Grade das 20 Categorias Oficiais (100% Maiúsculas sem Acento)

| # | Nome da Categoria | Tipo | Grupo Contábil / Finalidade |
| :-: | :--- | :---: | :--- |
| **1** | RECEITA DE PRESTACAO DE SERVICOS | RECEITA | Faturamento de soldas, caldeiraria e reformas |
| **2** | RECEITA DE VENDA DE PRODUTOS E MATERIAIS | RECEITA | Venda direta de insumos, peças e sucatas |
| **3** | OUTRAS RECEITAS OPERACIONAIS E RENDIMENTOS | RECEITA | Rendimentos de aplicação, bonificações |
| **4** | INSUMOS E MATERIA-PRIMA | DESPESA | Arames, eletrodos, gases, chapas, discos de corte |
| **5** | SERVICOS DE TERCEIROS NA PRODUCAO | DESPESA | Usinagem externa, tratamento térmico, galvanização |
| **6** | FRETES E TRANSPORTES DE PRODUCAO | DESPESA | Fretes de insumos e entregas de peças |
| **7** | FOLHA DE PAGAMENTO (SALARIOS E BENEFICIOS) | DESPESA | Salários da equipe CLT/operacional, VT, VR |
| **8** | ENCARGOS TRABALHISTAS (FGTS E INSS) | DESPESA | Encargos incidentes sobre a folha de pagamento |
| **9** | PRO-LABORE DOS SOCIOS | DESPESA | Remuneração mensal administrativa dos sócios |
| **10** | IMPOSTOS E TRIBUTOS (SIMPLES NACIONAL / ISS / TAXAS) | DESPESA | DAS Simples Nacional, ISS, taxas municipais |
| **11** | TARIFAS BANCARIAS E TAXAS DE CARTAO | DESPESA | Manutenção de conta, DOC/TED, taxas de maquininha |
| **12** | ALUGUEL, CONDOMINIO E IPTU | DESPESA | Custo de ocupação predial do galpão/oficina |
| **13** | ENERGIA ELETRICA, AGUA E INTERNET | DESPESA | Concessionárias e serviços de utilidade pública |
| **14** | MANUTENCAO DE MAQUINAS E INSTALACOES | DESPESA | Reparos de tochas, compressores, cabos, oficina |
| **15** | COMBUSTIVEL E DESPESAS COM VEICULOS | DESPESA | Abastecimento e manutenção da frota própria |
| **16** | SERVICOS PROFISSIONAIS (CONTABILIDADE, SOFTWARES) | DESPESA | Contador, licenças de software, assessoria |
| **17** | OUTRAS DESPESAS OPERACIONAIS | DESPESA | Limpeza, copa, materiais de escritório |
| **18** | AQUISICAO DE MAQUINAS, EQUIPAMENTOS E FERRAMENTAS | DESPESA | Investimentos em ativo imobilizado (CAPEX) |
| **19** | RETIRADA DE SOCIOS / DISTRIBUICAO DE LUCRO | DESPESA | Dividendos e saques de lucros pelos sócios |
| **20** | TRANSFERENCIA INTER-CONTAS | TRANSFERENCIA | Movimentação neutra entre Caixa Físico e Banco |

### 2.2 Blindagem de Credenciais no Seeder
No seed_initial_data.py:
`python
admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD', 'AdminMaster2026!')
admin_pin = os.environ.get('INITIAL_ADMIN_PIN', '123456')
`

---

## 3. Arquivos Afetados

### Backend
1. ackend/core/management/commands/seed_initial_data.py:
   - Atualizar a lista de categorias padrão com as 20 categorias oficiais.
   - Adicionar limpeza das categorias de teste (C1).
   - Injetar leitura de INITIAL_ADMIN_PASSWORD e INITIAL_ADMIN_PIN via os.environ.
2. ackend/apps/faturamento/services.py:
   - Atualizar categoria padrão de faturamento para RECEITA DE PRESTACAO DE SERVICOS.
3. ackend/apps/faturamento/tests.py:
   - Atualizar nome da categoria usada nos testes de faturamento.
4. ackend/apps/conciliacao/services.py:
   - Atualizar o dicionário heurístico para mapear lançamentos de extrato bancário (tarifas, impostos, combustível, energia) para as novas categorias.
5. ackend/apps/relatorios/services.py:
   - Assegurar que o DRE agrupe devidamente TARIFAS BANCARIAS E TAXAS DE CARTAO nas deduções da receita bruta.

---

## 4. Plano de Verificação e Testes

### 4.1 Execução do Seeder e Higienização do Banco
- Executar python backend/manage.py seed_initial_data.
- Conferir via Django shell se as categorias C1 desapareceram e se as 20 categorias oficiais estão presentes e ativas.

### 4.2 Suíte de Testes Automatizados
- Executar a suíte completa de testes do Django:
  .env\Scripts\python.exe backend/manage.py test backend/
- Validar se todos os 184 testes passam com 100% de sucesso.

### 4.3 Governança
- Salvar o plano aprovado em Planejamento/2026-09-14_03_reestruturacao_categorias_dre_e_seguranca_seed.md.
- Atualizar docs/STATUS.md.
- Realizar commit semântico: eat(financeiro): restructure dre categories, purge test items, and secure admin seed credentials.

---

## 5. Relatório de Execução e Evidências

1. **Atualização do Seeder (seed_initial_data.py):**
   - 20 categorias financeiras oficiais cadastradas e sincronizadas no banco.
   - Rotina de migração inteligente aplicada: categorias legadas renomeadas automaticamente sem quebrar IDs.
   - Exclusão e purga definitiva das categorias de teste 'C1'.
   - Leitura de credenciais do Administrador Geral atualizada para os.environ.get('INITIAL_ADMIN_PASSWORD', 'AdminMaster2026!') e os.environ.get('INITIAL_ADMIN_PIN', '123456').

2. **Integração no Faturamento e Conciliação:**
   - pps/faturamento/services.py: Categoria padrão de receita ajustada para RECEITA DE PRESTACAO DE SERVICOS.
   - pps/faturamento/tests.py: Ajustado nome da categoria de receita padrão.
   - pps/conciliacao/services.py: Heurística de sugestão de categorias no extrato bancário enriquecida com as novas nomenclaturas oficiais (tarifas, encargos trabalhistas, tributos fiscais, energia/água/internet, combustível, pró-labore, folha e receitas).

3. **Validação Automatizada:**
   - Suíte de 184 testes do Django executada e aprovada com 100% de sucesso (Ran 184 tests in 79.917s - OK).
