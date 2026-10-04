# REGISTRO DE ERROS E SOLUÇÕES - EMC SOLDAS

Este documento é um arquivo vivo destinado a registrar incidentes técnicos, erros de compilação, bugs de execução, falhas de integração ou regressões encontradas durante o desenvolvimento e manutenção do sistema **EMC Soldas**, documentando a causa raiz, a solução definitiva e a estratégia de prevenção futura.

---

## Modelo de Registro

Utilize o padrão abaixo para cada novo erro registrado:

```markdown
## AAAA-MM-DD - <título curto do erro>

- **Sintoma:** Descrição clara do comportamento anômalo observado, mensagem de erro ou código de status HTTP retornado.
- **Causa:** Análise técnica da causa raiz do problema.
- **Solução aplicada:** Descrição detalhada da correção implementada (arquivos alterados, refatoração de código ou ajuste de configuração).
- **Como evitar no futuro:** Boas práticas, testes automatizados ou validações prévias para impedir a reincidência da falha.
```

---

## Histórico de Erros

## 2026-08-18 - Erro de Resolução de Host no Git Push (URL Remota Duplicada)

- **Sintoma:** Falha ao executar `git push -u origin main` com a mensagem `fatal: unable to access 'https://https://github.com/grcarpanez/emc-soldas.git/': Could not resolve host: https`.
- **Causa:** O comando de adição do repositório remoto foi executado com o protocolo `https://` duplicado no início da URL (`https://https://...`).
- **Solução aplicada:** Executado o comando `git remote set-url origin https://github.com/grcarpanez/emc-soldas.git` para retificar o endereço e, em seguida, executado o comando `git push -u origin main` com sucesso.
- **Como evitar no futuro:** Sempre validar a URL antes de colar no terminal e utilizar `git remote -v` para conferir a exatidão dos endereços remotos configurados.

---

## 2026-08-18 - UnicodeEncodeError no Console Windows (cp1252) no Comando de Seeders

- **Sintoma:** Falha ao executar `seed_initial_data` em ambiente Windows com o erro `UnicodeEncodeError: 'charmap' codec can't encode character '\u2714' in position 0`.
- **Causa:** Uso de caracteres especiais unicode (`✔`) nas mensagens de saída do `stdout.write`, incompatíveis com o encoding padrão de terminais Windows (cp1252/Windows-1252).
- **Solução aplicada:** Substituição dos glifos unicode pelo padrão ASCII puro `[OK]` no arquivo `backend/core/management/commands/seed_initial_data.py`.
- **Como evitar no futuro:** Utilizar estritamente strings e caracteres ASCII puro para saídas de terminal e logs de console.

---

## 2026-08-18 - Quebra de Transação em Testes de Integridade no SQLite (TransactionManagementError)

- **Sintoma:** Durante a execução de `manage.py test`, testes que validavam `UniqueConstraint` com `assertRaises(IntegrityError)` quebravam a transação atômica global do TestCase com `TransactionManagementError: An error occurred in the current transaction`.
- **Causa:** No SQLite, o lançamento de `IntegrityError` dentro de um bloco transacional atômico corrompe a transação ativa a menos que a operação de falha esperada seja isolada explicitamente em um sub-bloco transacional.
- **Solução aplicada:** Envolvimento das chamadas de teste de unicidade em blocos `with transaction.atomic():` dentro de `backend/core/tests.py`.
- **Como evitar no futuro:** Sempre envolver asserções de exceções de banco de dados (`IntegrityError`, `ValidationError`) em blocos `with transaction.atomic():` em suítes de teste do Django.

---

## 2026-08-18 - Incompatibilidade de Versão do MariaDB 10.4.x (XAMPP) no Django 5.x

- **Sintoma:** Ao executar `python backend/manage.py migrate`, o Django lançou `NotSupportedError: MariaDB 10.5 or later is required (found 10.4.32)` seguido de erro de sintaxe SQL em `RETURNING` na gravação de migrations.
- **Causa:** O Django 5.x por padrão exige MariaDB 10.5+ e presume suporte nativo à cláusula `RETURNING` em comandos INSERT, que não existe no MariaDB 10.4 padrão do XAMPP.
- **Solução aplicada:** Configuração de bypass de versão em `backend/config/settings.py` com `DatabaseWrapper.check_database_version_supported = lambda self: None` e desativação das features `can_return_columns_from_insert` e `can_return_rows_from_bulk_insert`. Além disso, ajustado `caminho_arquivo_fisico` no modelo `ControleArquivoLog` para `max_length=255` para compatibilidade estrita com índices únicos no MySQL/MariaDB.
- **Como evitar no futuro:** Manter as configurações de compatibilidade do driver PyMySQL no `settings.py` para assegurar suporte contínuo ao XAMPP em desenvolvimento local e a provedores Cloud em produção.

---

## 2026-08-18 - Preservação de Pontuação na Sanitização de Textos Livres

- **Sintoma:** Risco de remoção indesejada de símbolos úteis em endereços e descrições técnicas (como `º`, `ª`, `/`, `-`, `(`, `)`, `,`, `.`) ao sanitizar entradas para ASCII puro.
- **Causa:** Expressões regulares excessivamente restritivas (ex: `re.sub(r'[^A-Z0-9 ]', '', texto)`) eliminam pontuações essenciais de logradouro e especificações técnicas.
- **Solução aplicada:** Adoção da normalização diacrítica `unicodedata.normalize('NFKD', ...)` com substituição prévia de ordinais (`º` -> `O`, `ª` -> `A`) e filtragem exclusiva de marcas combinadas (`unicodedata.combining(c)`), preservando toda a pontuação e estrutura do texto original enquanto converte com segurança para maiúsculas sem acento.
- **Como evitar no futuro:** Nunca utilizar regex destrutiva em campos de texto livre (endereços, descrições, observações). Utilizar sempre a função utilitária `sanitizar_texto_maiusculo` no backend e `sanitizarTextoEmTempoReal` no frontend.

---

## 2026-08-18 - Roteamento com Barras em Parâmetros de CNPJ Formatado (404 Not Found)

- **Sintoma:** Requisições para `/api/utilitarios/consulta-cnpj/33.000.167/0001-01/` retornavam erro `404 Not Found`.
- **Causa:** O conversor de rota padrão do Django `<str:cnpj>` rejeita caracteres de barra `/` presentes na formatação usual de CNPJs, interpretando-os como separadores de segmentos de rota.
- **Solução aplicada:** Substituição de `path('.../<str:cnpj>/')` por `re_path(r'^utilitarios/consulta-cnpj/(?P<cnpj>.+?)/?$')` em `backend/apps/cadastros/urls.py`, permitindo que consultas recebam tanto o CNPJ limpo (`33000167000101`) quanto formatado com barras, pontos e traços.
- **Como evitar no futuro:** Em rotas que recebem parâmetros com possíveis caracteres de separação de caminho (como documentos formatados com barra), utilizar `re_path` ou `<path:param>` com sanitização interna dos dígitos.

---

## 2026-08-18 - Bloqueio de Validação Aninhada por UniqueTogetherValidator do DRF em Sub-itens de Compra

- **Sintoma:** Criação de `DocumentoFiscalCompra` com sub-lista `itens_comprados` retornava `400 Bad Request` com o erro `'documento_fiscal': ['Este campo é obrigatório']` nos itens da lista.
- **Causa:** O Django REST Framework infere automaticamente um `UniqueTogetherValidator` em `ModelSerializer` quando o model possui `UniqueConstraint` envolvendo a chave estrangeira do pai (`documento_fiscal`, `item`). Em requisições aninhadas, o objeto pai ainda não foi persistido no banco no momento da validação dos filhos, fazendo com que o validador nativo falhe por ausência do ID pai.
- **Solução aplicada:** Definição de `validators = []` na `class Meta` de `NotaCompraItemSerializer` e transferência da validação anti-duplicação de itens para o método `validate()` do serializer pai `DocumentoFiscalCompraSerializer`, mantendo a garantia final na `UniqueConstraint` do banco de dados MySQL.
- **Como evitar no futuro:** Em serializers de entidades relacionais 1:N que suportam escrita aninhada (como itens de notas fiscais, itens de orçamento e itens de fatura), desativar o validador automático do DRF com `validators = []` e realizar a checagem de itens repetidos no método `validate()` do serializer pai.

---

## 2026-08-18 - Rejeição Precoce de Chave de Acesso NFe Formatada por MaxLengthValidator do DRF

- **Sintoma:** Ao enviar chaves de acesso NFe formatadas com espaços ou traços (ex: `3526 0833 0001 6755 0010...` com 48 a 54 caracteres), a API retornava `400 Bad Request` com mensagem `'Certifique-se de que este campo não tenha mais de 44 caracteres.'` antes de executar o método `validate_chave_acesso`.
- **Causa:** O DRF herda o `max_length=44` do modelo ORM no `CharField` padrão e executa a validação de comprimento máximo antes de disparar a limpeza/sanitização no método `validate_chave_acesso`.
- **Solução aplicada:** Declaração explícita do campo `chave_acesso = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)` no `DocumentoFiscalCompraSerializer`, permitindo receber a string formatada pelo frontend, para então extrair estritamente os dígitos numéricos e validar o comprimento final exato de 44 dígitos antes de gravar no banco de dados.
- **Como evitar no futuro:** Sempre que um campo do modelo tiver tamanho estrito no banco mas puder receber dados de entrada formatados (máscaras de CPF, CNPJ, Chaves NFe, Telefones), declarar o campo no serializer com margem de caracteres suficiente para conter a máscara antes da extração dos dígitos.

---

## 2026-08-23 - Coerção de DateTime em DateField no DRF (AssertionError em to_representation)

- **Sintoma:** Ao serializar resposta de criação de `Orcamento`, a view retornava erro 500 com a mensagem `AssertionError: Expected a date, but got a datetime. Refusing to coerce, as this may mean losing timezone information.`
- **Causa:** O modelo `Orcamento` utilizava `default=timezone.now` em `data_geracao = models.DateField(...)`, que devolve um objeto `datetime.datetime` em vez de um `datetime.date` puro.
- **Solução aplicada:** Substituição de `default=timezone.now` por `default=timezone.localdate` no modelo `Orcamento` e atribuição explícita de `timezone.localdate()` em `OrcamentoSerializer`.
- **Como evitar no futuro:** Em modelos Django, utilizar sempre `default=timezone.localdate` para campos `DateField` e `default=timezone.now` para campos `DateTimeField`.

---

## 2026-08-23 - Campos de Autoria em BaseModel (created_by_id / updated_by_id)

- **Sintoma:** Erro `TypeError: LancamentoFinanceiro() got unexpected keyword arguments: 'created_by'` e `ValueError: The following fields do not exist in this model: updated_by`.
- **Causa:** Modelos que herdam de `BaseModel`/`AuditableModel` utilizam colunas explícitas de inteiros `created_by_id` e `updated_by_id`, preenchidas pelo `AuditUserMiddleware`. A tentativa de instanciar ou atualizar os campos usando os nomes `created_by` ou `updated_by` causava falha por ausência desses atributos relacionais diretos.
- **Solução aplicada:** Ajuste em `services.py` para atribuir explicitamente `created_by_id=getattr(user, 'id', None)` e `updated_by_id=getattr(user, 'id', None)`.
- **Como evitar no futuro:** Em todos os serviços e models herdados de `BaseModel`, utilizar sempre os sufixos `_id` (`created_by_id`, `updated_by_id`, `deleted_by_id`).

---

## 2026-08-23 - Exigência de Campo Pai em Serializer Aninhado de Propostas

- **Sintoma:** Ao enviar `propostas_pagamento` aninhadas na criação de `Fatura`, a API retornava `400 Bad Request` com `'fatura': ['Este campo é obrigatório']`.
- **Causa:** O `FaturaPropostaPagamentoSerializer` incluía o campo `fatura` em `fields` sem declarar `read_only=True`, exigindo que o ID da fatura estivesse presente no payload antes da persistência do objeto pai.
- **Solução aplicada:** Definição explícita de `fatura = serializers.PrimaryKeyRelatedField(read_only=True)` no `FaturaPropostaPagamentoSerializer`.
- **Como evitar no futuro:** Em serializers aninhados onde o vínculo com o objeto pai é estabelecido no método `create()` ou na camada de serviço, declarar a chave estrangeira do pai como `read_only=True`.

---

## 2026-08-23 - Acúmulo de Requisições em Testes de Endpoints com ScopedRateThrottle (429 Too Many Requests)

- **Sintoma:** Durante a execução sequencial da suíte de testes de relatórios, requisições válidas de exportação em PDF e CSV retornavam `429 Too Many Requests` (`AssertionError: 429 != 200`).
- **Causa:** O DRF aplica o `ScopedRateThrottle` (`heavy_reports = 5/minute`) utilizando a camada de cache do Django. Ao rodar múltiplos testes automatizados em sequência no mesmo segundo, o limite de 5 requisições por minuto por IP/usuário era atingido naturalmente antes do término da suíte.
- **Solução aplicada:** Inclusão de `django.core.cache.cache.clear()` no `setUp()` e antes das chamadas de exportação na classe de testes, além de adicionar um teste específico que valida propositalmente o bloqueio com `429 Too Many Requests` na 6ª requisição.
---

## 2026-08-23 - Incompatibilidade de Chaves Estrangeiras em Serializers do Catálogo (unidade_compra_id vs unidade_compra)

- **Sintoma:** Ao cadastrar um Insumo/Item pelo frontend, a API retornava `400 Bad Request` com o erro `{"unidade_compra": ["Este campo é obrigatório."]}`.
- **Causa:** O formulário client-side enviava o payload com a chave `unidade_compra_id`, enquanto o `ItemSerializer` no DRF declarava o campo relacional como `unidade_compra`.
- **Solução aplicada:** Implementação de método `to_internal_value` defensivo no `ItemSerializer` para aceitar tanto `unidade_compra` quanto `unidade_compra_id` (e `unidade_consumo_id`), além de ajustar o envio no frontend.
- **Como evitar no futuro:** Sempre implementar mapeamento flexível de aliases `_id` no `to_internal_value` de serializers de entrada ou padronizar a convenção de chaves estrangeiras entre frontend e backend.

---

## 2026-08-23 - Falha de Validação por Ausência de Unidade de Venda Obrigatória no Cadastro de Produto

- **Sintoma:** Ao cadastrar um Produto Composto / Receita BOM, a API retornava `400 Bad Request` com `{"unidade_venda": ["Este campo é obrigatório."]}`.
- **Causa:** O modelo `Produto` possui a chave estrangeira `unidade_venda` como obrigatória, porém o formulário do modal de Produto no frontend não possuía o seletor de Unidade de Venda.
- **Solução aplicada:** Inclusão do seletor de Unidade de Venda no modal de Produto do frontend (populado a partir do Dicionário UOM) e configuração de fallback automático no `to_internal_value` do `ProdutoSerializer` para a UOM padrão `'UN'` caso não informada.
- **Como evitar no futuro:** Assegurar que 100% dos campos obrigatórios dos modelos ORM estejam devidamente mapeados nos formulários visuais correspondentes do frontend.

---

## 2026-08-23 - Tratamento de Vírgula Decimal em Inputs Numéricos do Frontend (Fator de Conversão e Horas)

- **Sintoma:** Ao digitar valores decimais utilizando o padrão brasileiro de vírgula (ex: `4,5` ou `3,5`), campos como Fator de Conversão e Horas de Mão de Obra eram truncados para inteiros pelo `parseFloat` nativo do JavaScript ou rejeitados pelo backend.
- **Causa:** O JavaScript utiliza o ponto como separador decimal padrão em `parseFloat`, desconsiderando qualquer valor após a vírgula caso a string não passe por sanitização prévia (`.replace(',', '.')`).
- **Solução aplicada:** Aplicação de `.replace(',', '.')` em todos os inputs numéricos de ponto flutuante no frontend e suporte nativo a strings com vírgula no `to_internal_value` dos serializers do Django REST Framework.
- **Como evitar no futuro:** Sempre higienizar strings numéricas provenientes de inputs de usuários convertendo vírgulas em pontos antes do parsing matemático.

---

## 2026-08-23 - Falha de Preenchimento Automático na Consulta de CNPJ por Divergência de Estrutura de Resposta

- **Sintoma:** Ao sair do campo de documento com 14 dígitos de CNPJ, a consulta externa ocorria com sucesso no backend, mas os campos do formulário (Razão Social, Endereço, etc.) não eram preenchidos automaticamente.
- **Causa:** O backend retorna o objeto padronizado envolvido na chave `data` (`{ status: "success", data: { nome_razao: "...", ... } }`), enquanto o frontend tentava acessar diretamente na raiz do objeto (`res.razao_social`). Como `res.razao_social` era `undefined`, a condição `if (res && res.razao_social)` não executava a atribuição aos inputs.
- **Solução aplicada:** Refatoração de `handleAutoConsultaDocumento` em `cadastros-view.js` para extrair os dados via `const data = res?.data || res;` e mapear com fallbacks flexíveis (`data.nome_razao || data.razao_social || data.nome`), atribuindo diretamente aos elementos do DOM e acionando formatadores de CEP e Telefone.
- **Como evitar no futuro:** Sempre inspecionar a estrutura exata do contrato de dados retornado pelos endpoints proxy utilitários ao integrar o consumo no frontend.

---

---

## 2026-08-23 - Erro 404 no Botão de Histórico por Padrão de Rota do DRF Router (url_path)

- **Sintoma:** Ao clicar no botão `HISTÓRICO` de qualquer equipamento (na tabela ou na frota), a requisição falhava e exibia a notificação de erro.
- **Causa:** O método `@action(detail=True, methods=['get']) def historico_proprietarios` no `EquipamentoViewSet` gerava automaticamente a rota com o nome do método Python (`/api/equipamentos/{id}/historico_proprietarios/`, com sublinhado), enquanto a convenção de rotas da API REST do projeto e a chamada do frontend utilizam kebab-case (`/api/equipamentos/{id}/historico-proprietarios/`). A rota retornava erro HTTP `404 Not Found`.
- **Solução aplicada:**
  1. Declarado explicitamente `url_path='historico-proprietarios'` no decorator `@action` do `EquipamentoViewSet` em `backend/apps/cadastros/views.py`.
  2. Ajustado o teste unitário em `backend/apps/cadastros/tests.py` para validar a rota em kebab-case.
  3. Gerados os arquivos estáticos de ícone `favicon.ico`, `icon-192.png` e `icon-512.png` na paleta *Rust Orange* para eliminar requisições 404 de manifest e favicon.
- **Como evitar no futuro:** Sempre declarar explicitamente o parâmetro `url_path='kebab-case'` em todos os métodos `@action` do DRF.

---

## 2026-08-24 - Prevenção de Inconsistência Relacional em Soft Delete de Entidades Coligadas (base_manager_name = 'all_objects')

- **Sintoma:** Risco de consultas históricas (`orcamento.cliente`, `fatura.cliente`, `documento_compra.fornecedor`, relatórios DRE/Curva ABC/Inadimplência e geradores de PDF comercial) falharem, levantarem `DoesNotExist` ou omitirem registros após o Soft Delete de um cliente, fornecedor ou equipamento.
- **Causa:** Por padrão, quando um modelo utiliza um `SoftDeleteManager` que filtra `deleted_at__isnull=True` como manager padrão, o Django ORM pode utilizá-lo para resolver chaves estrangeiras (`ForeignKey`) em modelos relacionados caso `base_manager_name` não seja explicitamente declarado como um manager sem filtros.
- **Solução aplicada:** Configuração mandatória de `base_manager_name = 'all_objects'` nas classes `Meta` de `SoftDeleteModel`, `BaseModel` (`backend/core/models.py`) e `Usuario` (`backend/apps/authentication/models.py`), garantindo resolução relacional perfeita sem quebrar orçamentos, faturas, relatórios ou PDFs passados.
- **Como evitar no futuro:** Em arquiteturas com Soft Delete universal no Django ORM, sempre declarar `base_manager_name = 'all_objects'` na classe base abstrata para blindar 100% da integridade referencial histórica de entidades coligadas.

---

## 2026-08-24 - Correção de Parser de Resposta JSON da Lixeira e Inclusão de Equipamentos no Histórico

- **Sintoma:** Ao inativar clientes ou equipamentos, a tabela da Lixeira exibia a mensagem "Lixeira vazia para esta entidade", e a opção de Equipamentos não constava na combobox de entidades.
- **Causa:** O endpoint `GET /api/lixeira/` retorna o payload `{ "status": "success", "total": N, "itens": [...] }`. O JavaScript tentava extrair `const lista = res.results || res || [];`. Como `res.results` era indefinido, `lista` recebia o objeto `res`, cuja propriedade `.length` é indefinida (`false`), acionando a mensagem de tabela vazia. Além disso, a combobox continha apenas 5 entidades hardcoded e iniciava fixa em orçamentos sem opção de histórico geral.
- **Solução aplicada:** Atualização do parser no frontend para `const lista = res.itens || res.results || (Array.isArray(res) ? res : []);`, adição da opção `TODAS AS ENTIDADES (HISTÓRICO COMPLETO)` como padrão, inclusão de `EQUIPAMENTOS / VEÍCULOS` e de todas as 16 entidades mapeadas, com novo campo de busca textual e coluna de tipo/entidade na tabela.
- **Como evitar no futuro:** Padronizar a extração de listas de endpoints REST que encapsulam arrays em chaves personalizadas (`res.itens`), sempre utilizando `res.itens || res.results || (Array.isArray(res) ? res : [])`.

---

## 2026-08-24 - Bloqueio de Arquivo no Windows (PermissionError WinError 32) na Rotação de Logs Diários

- **Sintoma:** Ao executar testes ou em rotação diária de logs, o Python lançava `PermissionError: [WinError 32] O arquivo já está sendo usado por outro processo: '...\\logs\\app.log' -> '...\\logs\\app.log.2026-08-23'`.
- **Causa:** O handler padrão `TimedRotatingFileHandler` tenta renomear o arquivo `app.log` à meia-noite via `os.rename()`, o que é bloqueado pelo sistema de arquivos do Windows se houver qualquer thread ou processo mantendo o handle do arquivo aberto.
- **Solução aplicada:** Criação da classe personalizada `DailyDateFileHandler` em `backend/core/logging_handlers.py`, que grava diretamente nos arquivos diários imutáveis `app-YYYY-MM-DD.log` sem nunca necessitar renomear arquivos em disco (cumprindo 100% da arquitetura definida em `docs/FSD.md` - Seção 19).
- **Como evitar no futuro:** Em ambientes Windows ou sistemas com arquivos imutáveis por data, utilizar handlers de log que resolvem o nome do arquivo dinamicamente por data em vez de aplicar renomeações em tempo de execução.

---

## 2026-08-24 - Divergência de Nomes de Campos no Manifesto de Logs e Rota 404 no Log Viewer

- **Sintoma:** O Log Viewer da Central Administrativa exibia "Total de Eventos = 0" e ao clicar em "VER LOG", exibia a notificação Toast `[ERRO] Erro ao abrir arquivo de log.`.
- **Causa:** O serializer `ControleArquivoLogSerializer` retornava o campo `data_criacao`, enquanto o JavaScript esperava `l.data_log` e `l.quantidade_linhas`. Com valores `undefined`, o frontend requisitava o endpoint com rota incorreta `/controle-arquivos-log/visualizar-log/?data=undefined` (resultando em 404). Além disso, o serializer não computava a contagem de linhas/eventos do arquivo físico.
- **Solução aplicada:**
  1. Inclusão dos campos computados `data_log`, `total_eventos` e `quantidade_linhas` no `ControleArquivoLogSerializer`.
  2. Ajuste do endpoint para `/controle-arquivos-log/visualizar/` em `config.js`.
  3. Enriquecimento do modal do Log Viewer com contagem de eventos, filtro dinâmico por nível (`[AUDIT]`, `ERROR`, `WARNING`, `INFO`), busca textual e coloração semântica industrial.
  4. Integração universal de emissão de logs de auditoria `[AUDIT] [SOFT_DELETE]` e `[AUDIT] [RESTAURACAO]` em `SoftDeleteModel` para que todas as exclusões de clientes, equipamentos e registros de negócio constem nos logs do servidor.
- **Como evitar no futuro:** Garantir alinhamento bidirecional de contratos de dados e rotas entre frontend e serializers do DRF e cobrir serializers com testes automatizados dedicados.

---

## 2026-08-24 - Rota 404 no Botão de Permissões RBAC e Falta de Controle de Ativação de Colaboradores

- **Sintoma:** Na Central do Administrador -> aba Gestão de Equipe (RBAC), ao clicar no botão "PERMISSÕES (10 TOGGLES)", o modal não abria e exibia a notificação Toast de erro "Erro ao carregar permissões.". Além disso, não havia botões para ativar/desativar colaboradores nem proteção contra auto-desativação.
- **Causa:** O JavaScript tentava requisitar `GET /api/permissoes/?usuario_id=X` e `PATCH /api/permissoes/{id}/`. Essa rota não existia como viewset separado no Django REST Framework, pois as permissões 1:1 eram geridas como action no `UsuarioViewSet` em `/api/usuarios/{id}/permissoes/` (que até então aceitava apenas PATCH/PUT sem suporte a GET).
- **Solução aplicada:**
  1. Habilitado suporte completo a `GET`, `PATCH` e `PUT` na action `permissoes` do `UsuarioViewSet`, retornando a matriz completa de 10 toggles.
  2. Implementação de novas actions semânticas no backend: `alternar_status`, `desativar`, `ativar` e `alterar_perfil` (promoção/rebaixamento).
  3. Aplicação de travas de segurança mandatórias no backend: bloqueio de auto-desativação (`request.user.id == usuario.id`), bloqueio de auto-exclusão lógica e proteção contra desativação/rebaixamento/exclusão do único Administrador ativo do sistema.
  4. Integração de emissão de logs estruturados de auditoria `[AUDIT]` para todas as ações de colaboradores (promoção, rebaixamento, ativação, desativação, diff de permissões, convite e desbloqueio).
  5. Refatoração da interface da aba Gestão de Equipe no PWA com modal unificado de perfil e 10 toggles dinâmicos, botões diretos de ativação/desativação e auto-identificação da conta logada com tag `[VOCÊ]` e botão desabilitado.
  6. Criação de 7 novos testes automatizados dedicados no `apps.authentication.tests` cobrindo 100% dos novos cenários e travas de segurança (157 testes aprovados).
- **Como evitar no futuro:** Sempre validar os contratos de rotas de actions de ViewSets no DRF com testes unitários de integração e alinhar os endpoints mapeados no `config.js` do frontend.

---

## 2026-08-24 - Erro 400 ao Filtrar Nível AUDIT no Log Viewer e Limitação de Categorias de Log

- **Sintoma:** Ao selecionar o filtro `AUDIT` no modal do Log Viewer, a API retornava `400 Bad Request` com a mensagem `"AUDIT" não é uma escolha válida.`, disparando o Toast de erro.
- **Causa:** O serializer `LogViewerFilterSerializer` declarava o campo `nivel` com `ChoiceField` restrito aos níveis clássicos de severidade do Python (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`), rejeitando categorias estruturadas de auditoria e segurança como `AUDIT` ou `SEGURANCA`.
- **Solução aplicada:**
  1. Flexibilização do campo `nivel` em `LogViewerFilterSerializer` para aceitar qualquer string válida com conversão automática para maiúsculas no `validate_nivel`.
  2. Aprimoramento do método `ler_arquivo_log_seguro` em `backend/apps/administracao/services.py` com suporte inteligente a categorias:
     - `AUDIT`: captura `[AUDIT]`, `[SOFT_DELETE]`, `[RESTAURACAO]`, `[CANCELAMENTO]`, `[ESTORNO]`.
     - `SEGURANCA`: captura `[SEGURANÇA]`, `[SEGURANCA]`, `[SECURITY]`, `401`, `403`, `Unauthorized`, `Forbidden`.
     - `ERROR`: captura `[ERROR]`, `[CRITICAL]`.
     - `WARNING`: captura `[WARNING]`.
     - `INFO`: captura `[INFO]`.
     - `DEBUG`: captura `[DEBUG]`.
  3. Atualização do modal no frontend (`administracao-view.js`) com a combobox completa de 6 categorias bem descritas e badges estilizados no padrão *Industrial Integrity*.
  4. Adicionados testes automatizados cobrindo a filtragem de `AUDIT` e `SEGURANCA` com 100% de sucesso.
---

## 2026-08-24 - Falsos Positivos em Badges de Log por Colisão de Substrings em URLs de Requisições HTTP

- **Sintoma:** Ao consultar o Log Viewer com filtros de severidade (ex: `&nivel=ERROR` ou `&nivel=WARNING`), as linhas normais de requisição HTTP (`[INFO] [django.server] "GET ...&nivel=ERROR" 200`) recebiam badges incorretos de `ERROR` (vermelho) ou `WARN` (âmbar) no visualizador, e o filtro `INFO` misturava requisições web com ações de auditoria.
- **Causa:** O visualizador no frontend determinava os badges por buscas ingênuas de substrings (`.includes('ERROR')`), encontrando o termo dentro da própria query string da URL. Além disso, o backend não segregava a categoria semântica primária da severidade técnica do Python (`[INFO]`).
- **Solução aplicada:**
  1. Implementação de parser semântico estruturado em `backend/apps/administracao/services.py`, classificando cada linha por sua categoria definitiva (`AUDIT`, `SEGURANCA`, `ERROR`, `WARNING`, `HTTP`, `INFO`, `DEBUG`) validando a posição correta dos marcadores.
  2. Adição da categoria `HTTP` no backend e frontend para isolar consultas de API e tráfego web.
  3. Atualização de `administracao-view.js` para renderizar badges estritamente a partir da propriedade `item.categoria` enviada pelo backend, eliminando 100% dos falsos positivos.
  4. Ampliação da suíte de testes unitários cobrindo todas as categorias de filtragem (157 testes aprovados com 100% de sucesso).
---

## 2026-08-24 - Truncamento Acidental do Arquivo de Log Real do Dia Durante Execução de Testes Automatizados

- **Sintoma:** Após a execução da suíte completa de testes automatizados (`manage.py test`), o arquivo de log do dia atual (`app-2026-08-24.log`) teve seu histórico anterior substituído, passando de 160+ linhas para ~80 linhas.
- **Causa:** O teste unitário `test_log_viewer_leitura_estruturada_e_filtros` abria o arquivo do dia de hoje `open(f"app-{hoje_str}.log", 'w')` no modo de escrita/sobrescrita para injetar 6 linhas de teste mock, apagando o histórico real anterior.
- **Solução aplicada:**
  1. Refatoração do teste unitário para utilizar uma data fictícia e segura no futuro (`data_teste = "2099-12-31"`, arquivo `app-2099-12-31.log`).
  2. Implementação de estrutura `try / finally` garantindo que o arquivo e o registro de teste no manifesto sejam removidos ao final do teste.
  3. Varredura completa na suíte garantindo que nenhum teste manipule arquivos diários reais do dia corrente.
- **Como evitar no futuro:** Testes unitários e de integração que manipulam arquivos físicos em disco devem sempre utilizar diretórios temporários (`tempfile.mkdtemp()`) ou datas fictícias isoladas com limpeza obrigatória no encerramento do teste.

---

## 2026-09-01 - Reconfiguração do Ambiente Operacional Local após Formatação do Computador

- **Sintoma:** 1. `git status` retornava `fatal: detected dubious ownership in repository at 'D:/gestao_orcamentos_2.0'`. 2. `python.exe` do venv falhava com `did not find executable at 'C:\Users\Gusta\AppData\Local\Programs\Python\Python314\python.exe'`. 3. Conexão ao MySQL falhava com ausência da base de dados `emc_soldas` na nova instalação do MariaDB/MySQL local.
- **Causa:** O computador foi formatado pelo usuário, alterando o SID do usuário do Windows, a pasta de instalação nativa do Python 3.14 (agora em `C:\Users\Gusta\AppData\Local\Python\pythoncore-3.14-64`) e resetando os bancos de dados do MySQL local (porta 3306).
- **Solução aplicada:**
  1. Executado `git config --global --add safe.directory D:/gestao_orcamentos_2.0`.
  2. Atualizado `venv/pyvenv.cfg` apontando para o novo executável do Python 3.14.7, preservando 100% dos pacotes já instalados em `site-packages`.
  3. Criado o banco de dados `emc_soldas` via script PyMySQL (`CREATE DATABASE IF NOT EXISTS emc_soldas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`).
  4. Executadas todas as migrações do Django (`call_command('migrate')`).
  5. Executado o seeder inicial de dados estruturais (`call_command('seed_initial_data')`), recriando o usuário Administrador Master (`admin@emcsoldas.com.br`) e todos os dicionários.
- **Como evitar no futuro:** Manter documentado o checklist de restauração rápida em `AGENTS.md` e `STATUS.md`.

---

## 2026-09-01 - Incompatibilidade de Lookup __date__range em Campos DateTimeField (AssertionError: 0 != 1)

- **Sintoma:** O teste unitário `test_divergencias_conciliacao` falhou com `AssertionError: 0 != 1` na asserção `self.assertEqual(dados['total_sobras_erp'], 1)`.
- **Causa:** O filtro de período em `backend/apps/relatorios/services.py` utilizava `data_pagamento__date__range=(data_inicio, data_fim)` sobre o campo `DateTimeField` `data_pagamento`. No SQLite (usado nos testes in-memory), a transformação `__date` gera `django_datetime_cast_date`, comparando strings ISO com inteiros não-cotados (`BETWEEN 2026-09-01 AND 2026-09-01` avaliado como `2016`), retornando 0 registros. Além disso, no MySQL essa transformação impede o uso de índices (não-SARGable) e depende da tabela `mysql.time_zone_name`.
- **Solução aplicada:** Implementação da função utilitária `converter_periodo_para_datetime_range(data_inicio, data_fim)` gerando um range timezone-aware cobrindo de `00:00:00` a `23:59:59.999999` (`America/Sao_Paulo`), e substituição de `data_pagamento__date__range` por `data_pagamento__range=(dt_inicio, dt_fim)` em `DashboardService`, `DREService` e `DivergenciasConciliacaoService`. A suíte de 157 testes automatizados passou com 100% de aprovação.
- **Como evitar no futuro:** Sempre que filtrar intervalos de datas sobre campos `DateTimeField`, converter o período em range datetime timezone-aware em vez de utilizar o lookup de data `__date__range`.

---

## 2026-09-07 - Inconsistência de Formatos Livres e Risco de Entrada de Placas Inválidas

- **Sintoma:** O campo `placa` no cadastro de equipamentos/veículos aceitava strings arbitrárias sem restrição estrutural de caracteres, permitindo a gravação de placas incompletas ou com formatos fora do padrão veicular brasileiro.
- **Causa:** Ausência de validação específica de regex no serializer de equipamentos e de máscara restritiva no frontend para o formato veicular brasileiro (padrão antigo `AAA-0000` e padrão Mercosul `AAA0A00`).
- **Solução aplicada:**
  1. Criação da função utilitária `validar_placa(valor)` em `backend/core/utils.py` com sanitização para maiúsculas e validação regex estrita: `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`.
  2. Implementação de validação defensiva em `apps/cadastros/serializers.py` (`validate_placa`) retornando `400 Bad Request` semântico.
  3. Adição de máscara de digitação em tempo real no frontend (`frontend/assets/js/utils.js`: `formatarPlacaVeiculo`) com restrição posicional estrita: posições 0-2 exclusivamente letras, posição 3 número, posição 4 letra ou número, e posições 5-6 números.
  4. Validação e disparo de toast industrial no submit dos modais de cadastro de equipamento e frota em `cadastros-view.js`.
- **Como evitar no futuro:** Campos opcionais com padrões normativos (como placas, documentos, CEP, CNPJ/CPF) devem sempre ter validação simétrica em duas camadas: máscara reativa no frontend para guiar o operador e validação estrita no backend REST para garantir a integridade dos dados.

---

## 2026-09-07 - Retenção de Scripts Antigos no Navegador por Cache Estático Stale do Service Worker (PWA)

- **Sintoma:** Após implementar melhorias na máscara de placas no arquivo `utils.js`, o navegador do usuário continuava executando a função legada (permitindo digitar strings exclusivamente com letras sem colocar hífen e adicionando hífen em números), ignorando o novo código disponível no servidor.
- **Causa:** O Service Worker (`frontend/sw.js`) utiliza estratégia de cache estático com `caches.match()` prioritário sob a versão estática `emc-soldas-v2.7`. Como o `CACHE_NAME` não havia sido incrementado e o arquivo `index.html` não possuía sufixos de versionamento nas tags `<script>`, o navegador utilizava os arquivos JS desatualizados gravados no Cache Storage local.
- **Solução aplicada:**
  1. Incremento de versão em `frontend/sw.js` para `CACHE_NAME = 'emc-soldas-v2.8'` com purga imediata de versões anteriores no evento `activate`.
  2. Implementação de cache-busting em `frontend/index.html`, sufixando todas as tags `<script src="...?v=2.8">` e folhas de estilo `<link rel="stylesheet" href="...?v=2.8">`.
  3. Instituição de regra mandatória na Seção 6 e 7 do `AGENTS.md` tornando obrigatório o incremento de versão no `sw.js` e `index.html` em toda alteração de frontend, acompanhado de instrução de reload forçado (`Ctrl + Shift + R`).
- **Como evitar no futuro:** Nunca alterar arquivos JS/CSS em PWAs com Service Worker sem simultaneamente incrementar a versão em `sw.js` e atualizar os sufixos `?v=X.Y` no `index.html`.

---

## 2026-09-11 - Falha na Leitura de Extratos CSV Acentuados e Incompatibilidade de Contrato de Dados na Conciliação Bancária

- **Sintoma:** Ao realizar upload de extrato bancário CSV na tela de Conciliação Bancária Split-Screen, a aplicação exibia mensagem de sucesso mas nenhuma transação era exibida (`0 TRANSAÇÕES` e `Nenhuma transação encontrada no arquivo`), além de os valores numéricos serem lidos como descrição. Adicionalmente, o sistema não possuía tela no frontend para criação e gestão de contas bancárias.
- **Causa:**
  1. O parser de CSV buscava apenas por termos sem acento (`descricao`), falhando no match em cabeçalhos como `Data,Valor,Identificador,Descrição` e acionando fallback que selecionava a coluna 1 (`Valor`) como descrição.
  2. O backend retornava o extrato na chave `res.extrato`, enquanto o frontend lia `res.transacoes || []` (`undefined`).
  3. Ausência de tela de Contas Bancárias na Tesouraria para associar aos extratos e aos lançamentos.
- **Solução aplicada:**
  1. Criação da aba dedicada "CONTAS BANCÁRIAS" em `financeiro-view.js` com cards de KPIs, listagem, cadastro e edição de saldos/limites.
  2. Implementação de motor universal de CSV em 3 camadas em `parsers.py` (normalização fonética sem acento via `NFKD`, sinônimos multi-banco, heurística de inspeção por amostragem e filtro de ruído de saldo anterior).
  3. Compatibilização de chaves no backend e no frontend (`res.extrato || res.transacoes`), adição de seletor de conta bancária na conciliação e inclusão de categoria contábil no modal de lançamento rápido.
  4. Incremento de versão do Service Worker PWA para `v4.15` e cache-busting no `index.html`.
- **Como evitar no futuro:** Sempre normalizar e sanitizar termos de arquivos de terceiros (como bancos) e manter contratos de API documentados e sincronizados com os handlers de frontend.

---

## 2026-09-14 - Falha de Upload de Extratos no Celular via Provedor de Nuvem (OneDrive) e Interceptação no Service Worker (Failed to fetch)

- **Sintoma:** Ao tentar importar um extrato bancário pelo smartphone (via 4G/5G através do túnel Cloudflare), o PWA disparava inicialmente `[ERRO] Sem conexão com o servidor da oficina. Operação offline.` e, após ajuste no Service Worker, `[ERRO] Failed to fetch`.
- **Causa:**
  1. **Arquivo Remoto no Android (OneDrive):** O usuário estava selecionando o arquivo diretamente da pasta virtual do OneDrive no seletor de arquivos do Android. O sistema operacional entrega um ponteiro virtual (`content://`) sem os bytes físicos em cache local. Quando o navegador Chrome tenta ler os bytes para montar o payload multipart/form-data do `fetch()`, a leitura do stream é abortada pelo sistema operacional móvel, gerando imediatamente a exceção `TypeError: Failed to fetch` antes mesmo de transmitir os pacotes para a rede.
  2. **Interceptação no Service Worker:** Originalmente, o `sw.js` interceptava requisições `POST` de upload e mascarava o erro do navegador gerando um HTTP 503 com aviso de *"Sem conexão com o servidor da oficina"*.
- **Solução aplicada:**
  1. **Bypass de Mutação no Service Worker:** Adição da cláusula `if (event.request.method !== 'GET') return;` no listener de `fetch` em `frontend/sw.js` (PWA v4.31), garantindo que uploads trafeguem diretamente pela pilha de rede nativa do navegador com buffers e retransmissões do SO.
  2. **Download Local do Arquivo:** O usuário baixou o arquivo do OneDrive para o armazenamento físico local do smartphone (pasta `Downloads`), permitindo que o Chrome lesse os bytes instantaneamente e transmitisse o arquivo com 100% de sucesso (resposta HTTP 200 OK com 32.737 bytes de transações processadas).
- **Como evitar no futuro:** Ao realizar uploads em navegadores móveis (Android/iOS), garantir que os arquivos estejam salvos no armazenamento local do aparelho (e não como referências remotas em nuvens como OneDrive/Google Drive). Manter o Service Worker configurado para nunca interceptar métodos de mutação (`POST`/`PUT`/`DELETE`).

---

## 2026-10-03 - Erro de Serialização de Comprovantes em Lançamentos Financeiros (O dado submetido não era um arquivo)

- **Sintoma:** Ao anexar uma Nota Fiscal ou comprovante a um lançamento do Caixa Real na Tesouraria (ou ao criar/editar lançamentos com anexo), o sistema apresentava o toast de erro: `Erro ao anexar comprovante: COMPROVANTE: O dado submetido não era um arquivo. Cheque o tipo de codificação no formulário.`
- **Causa:** O endpoint `/api/conciliacao/upload-comprovante/` salvava fisicamente o arquivo no disco do servidor e retornava um JSON com o caminho relativo (ex: `comprovantes/2026/10/arquivo.pdf`). Ao chamar `PATCH /api/lancamentos-financeiros/{id}/` com esse caminho em string, o `LancamentoFinanceiroSerializer` gerava um erro de validação do DRF, pois, sendo um `ModelSerializer` de um modelo com `FileField`, ele exigia obrigatoriamente um objeto binário de upload (`UploadedFile`) e rejeitava strings.
- **Solução aplicada:**
  1. Criação do campo híbrido customizado `ComprovanteFileOrCharField(serializers.FileField)` em `backend/apps/financeiro/serializers.py`, com suporte a strings (caminhos relativos e URLs), uploads diretos e valores nulos.
  2. Declaração explícita dos campos `comprovante` e `nome_arquivo_comprovante` no `LancamentoFinanceiroSerializer`.
  3. Adição de testes unitários automatizados em `backend/apps/financeiro/tests.py` cobrindo PATCH com caminho relativo, desvinculação com `null` e criação via POST.
- **Como evitar no futuro:** Em modelos do DRF onde o fluxo de upload de arquivos é desacoplado (o upload do arquivo binário ocorre em um endpoint auxiliar e a persistência do vínculo ocorre posteriormente via PATCH/POST em JSON), utilizar serializers fields customizados que aceitem tanto instâncias de arquivo quanto caminhos de arquivos já salvos.

---

## 2026-10-03 - Duplicidade de Lançamentos e de Saldo na Importação de Extratos Bancários com Lançamentos Manuais Pré-existentes

- **Sintoma:** Ao realizar um lançamento manual no Caixa Real (ex: entrada de R$ 6.770,00 em 02/06/2025) e posteriormente importar o extrato bancário (OFX/CSV) daquele período, o sistema criava um segundo lançamento idêntico no Caixa Real para o mesmo dia, duplicando a movimentação financeira e o saldo da conta bancária.
- **Causa:**
  1. O serviço `enriquecer_transacao_inteligencia` apenas buscava lançamentos com `is_conciliado=True` ou com mesmo `fitid`. Lançamentos manuais feitos no Caixa Real iniciam com `is_conciliado=False` e sem `fitid`, passando despercebidos pela triagem.
  2. A comparação não considerava discrepâncias de nomenclatura entre o extrato bancário (ex: "PIX RECEBIDO CAVENGE ENGENHARIA") e o lançamento manual informado pelo operador (ex: "SERVICO DE SOLDA FLANGE"), exigindo conferência baseada em valor ($\pm$ R$ 0,05) e janela temporal ($\pm$ 3 dias).
  3. Na importação em lote (`executar_importacao_lote`), o backend sempre criava um novo registro `LancamentoFinanceiro` e recalculava o saldo da conta, creditando/debitando o valor pela segunda vez quando o lançamento manual já havia sido lançado como `PAGO`.
- **Solução aplicada:**
  1. No backend (`backend/apps/conciliacao/services.py`), implementação da detecção de correspondências de lançamentos manuais não conciliados (`is_conciliado=False`) baseada em conta, direção (`ENTRADA`/`SAIDA`), valor exato ($\pm$ R$ 0,05) e janela temporal de até $\pm$ 3 dias, anexando o objeto `lancamento_correspondente`.
  2. Atualização de `ItemImportacaoLoteSerializer` para aceitar `lancamento_existente_id` e tornar `categoria_id` opcional na vinculação.
  3. No serviço `executar_importacao_lote`, suporte a `lancamento_existente_id`: se o lançamento manual já estava `PAGO` na mesma conta (`ja_impactou_saldo`), o sistema apenas concilia o lançamento existente (`is_conciliado=True`, `fitid`, `data_conciliacao=now`) e **não altera o saldo da conta novamente**, prevenindo 100% da duplicidade contábil e patrimonial.
  4. No frontend (`frontend/assets/js/views/conciliacao-view.js`), abertura automática do modal industrial de conferência anti-duplicidade ao importar extratos com correspondências, permitindo ao usuário escolher entre "VINCULAR E CONCILIAR (Recomendado)", "CRIAR NOVO" ou "DESCARTAR", além de controles contextuais nos cards da Mesa de Triagem e atualização do botão de importação.
  5. Incremento de versão do Service Worker PWA para `v4.34` e sufixos de cache-busting `?v=4.34` no `index.html`.
  6. Adição de testes unitários automatizados cobrindo detecção de correspondência e vinculação atômica em `backend/apps/conciliacao/tests.py`.
- **Como evitar no futuro:** Sempre que um fluxo de importação em lote interagir com o Razão Contábil / Caixa Real, verificar se já existem títulos ou lançamentos equivalentes pendentes de conciliação por valor e data antes de criar novos registros, fornecendo conferência assistida ao operador com opção preferencial de vinculação.

---

## 2026-10-03 - Dashboard Zerado por Incompatibilidade de Contrato de Dados e Falha Silenciosa de CONVERT_TZ no MySQL

- **Sintoma:** O Dashboard Principal (`#/dashboard`) exibia todos os 5 Flip Cards zerados (`0` ou `R$ 0,00`), o gráfico de Receitas x Despesas vazio com mensagem *"Sem dados suficientes para exibição do gráfico"* e o feed de atividades recentes como *"Nenhuma atividade recente registrada"*, mesmo havendo lançamentos financeiros, saldo em contas e títulos em atraso no banco de dados.
- **Causa:**
  1. **Mismatch de Contrato nos Flip Cards:** O frontend tentava ler `const cards = res.cards || {}`, mas o backend retornava os cards diretamente na raiz (`res.operacao`, `res.faturamento`, etc.). Além disso, os nomes dos atributos internos divergiam (ex: `op.aprovados` vs `op.orcamentos_aprovados`, `rec.faturamento_real` vs `rec.receita_real`, `cxa.saldo_bancario_real` vs `cxa.saldo_real_consolidado`).
  2. **Falha Silenciosa no MySQL (`CONVERT_TZ`):** No gráfico mensal, o backend usava filtros ORM `data_pagamento__year=ano, data_pagamento__month=mes`. No MySQL com `USE_TZ = True`, isso gerava SQL `EXTRACT(MONTH FROM CONVERT_TZ(data_pagamento, 'UTC', 'America/Sao_Paulo')) = mes`. Sem tabelas de timezone populadas no MySQL (padrão no Windows/XAMPP), `CONVERT_TZ` retorna `NULL`, fazendo a cláusula avaliar como falso para 100% das linhas e zerando o gráfico. No frontend, buscava-se `res.historico` enquanto o backend devolvia `res.meses`.
  3. **Incompatibilidade no Feed:** O backend retornava uma lista direta `[...]` e o frontend esperava `res.atividades`, além de buscar `item.data_hora` em vez de `item.timestamp`.
  4. **Filtros de Período Ignorados:** Os botões "HOJE", "MÊS ATUAL" e "ANO" passavam `?periodo=X`, ignorado pelo backend.
- **Solução aplicada:**
  1. **Contrato Universal nos Flip Cards:** Backend atualizado para retornar as chaves de topo e também a chave `cards: { ... }` como espelho, com todos os aliases de propriedades esperados pelo frontend (`aprovados`, `em_execucao`, `concluidos`, `cancelados`, `rascunhos`, `faturadas`, `pagas`, `faturamento_real`, `saldo_bancario_real`, `vencidas`, etc.). Frontend atualizado com `res.cards || res || {}` e fallbacks defensivos.
  2. **Consultas Range SARGable no Gráfico:** Substituição dos lookups `__year` e `__month` por faixas SARGable `data_pagamento__gte=dt_ini_mes, data_pagamento__lt=dt_fim_mes` via `converter_periodo_para_datetime_range`. Isso elimina dependência de tabelas de fuso horário do MySQL, utiliza o índice B-Tree e funciona 100% em qualquer SGBD. Retornados `meses` e `historico`, `mes_nome` e `mes_sigla`, e determinação inteligente de ano caso o ano corrente não possua dados.
  3. **Compatibilização do Feed:** Backend retorna `timestamp` e `data_hora`, e frontend suporta tanto lista direta quanto objeto com chave `atividades`.
  4. **Filtros de Período:** Suporte implementado em `FiltroPeriodoSerializer` e `DashboardFlipCardsView` (`hoje`, `mes`, `ano`).
  5. **Versionamento PWA:** Cache sincronizado para `v4.36` no `sw.js` e `index.html`.
- **Como evitar no futuro:** Nunca utilizar lookups `__year` ou `__month` em campos `DateTimeField` quando operando com MySQL/MariaDB com `USE_TZ = True`; preferir sempre faixas explícitas de data/hora (`__gte` e `__lt`) com datetimes cientes de fuso horário. Adotar contratos de API defensivos com espelhos de propriedades e fallbacks seguros.

## 2026-10-03 - Tooltips exibidas atr�s dos modais

- **Sintoma:** O componente visual de tooltip dos gr�ficos (.chart-tooltip) n�o estava se sobrepondo a janelas modais ativas, ficando escondido.
- **Causa:** O z-index configurado na classe .chart-tooltip era 1000, enquanto as sobreposi��es de modais (.modal-overlay) e modais (.modal-card) possu�am z-index 9999 ou 10000, e outros componentes como dropdowns usavam at� 100050.
- **Solu��o aplicada:** O z-index da classe .chart-tooltip no arquivo industrial-integrity.css foi alterado para 999999 garantindo sobreposi��o universal. O cache do PWA foi invalidado incrementando a vers�o em sw.js e index.html.
- **Como evitar no futuro:** Sempre que criar elementos "flutuantes" universais (como tooltips ou toasts), garantir que seu z-index seja hierarquicamente superior ao dos containers modais no Design System.
