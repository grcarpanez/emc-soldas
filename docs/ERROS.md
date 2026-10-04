# REGISTRO DE ERROS E SOLUÃ‡Ã•ES - EMC SOLDAS

Este documento Ã© um arquivo vivo destinado a registrar incidentes tÃ©cnicos, erros de compilaÃ§Ã£o, bugs de execuÃ§Ã£o, falhas de integraÃ§Ã£o ou regressÃµes encontradas durante o desenvolvimento e manutenÃ§Ã£o do sistema **EMC Soldas**, documentando a causa raiz, a soluÃ§Ã£o definitiva e a estratÃ©gia de prevenÃ§Ã£o futura.

---

## Modelo de Registro

Utilize o padrÃ£o abaixo para cada novo erro registrado:

```markdown
## AAAA-MM-DD - <tÃ­tulo curto do erro>

- **Sintoma:** DescriÃ§Ã£o clara do comportamento anÃ´malo observado, mensagem de erro ou cÃ³digo de status HTTP retornado.
- **Causa:** AnÃ¡lise tÃ©cnica da causa raiz do problema.
- **SoluÃ§Ã£o aplicada:** DescriÃ§Ã£o detalhada da correÃ§Ã£o implementada (arquivos alterados, refatoraÃ§Ã£o de cÃ³digo ou ajuste de configuraÃ§Ã£o).
- **Como evitar no futuro:** Boas prÃ¡ticas, testes automatizados ou validaÃ§Ãµes prÃ©vias para impedir a reincidÃªncia da falha.
```

---

## HistÃ³rico de Erros

## 2026-08-18 - Erro de ResoluÃ§Ã£o de Host no Git Push (URL Remota Duplicada)

- **Sintoma:** Falha ao executar `git push -u origin main` com a mensagem `fatal: unable to access 'https://https://github.com/grcarpanez/emc-soldas.git/': Could not resolve host: https`.
- **Causa:** O comando de adiÃ§Ã£o do repositÃ³rio remoto foi executado com o protocolo `https://` duplicado no inÃ­cio da URL (`https://https://...`).
- **SoluÃ§Ã£o aplicada:** Executado o comando `git remote set-url origin https://github.com/grcarpanez/emc-soldas.git` para retificar o endereÃ§o e, em seguida, executado o comando `git push -u origin main` com sucesso.
- **Como evitar no futuro:** Sempre validar a URL antes de colar no terminal e utilizar `git remote -v` para conferir a exatidÃ£o dos endereÃ§os remotos configurados.

---

## 2026-08-18 - UnicodeEncodeError no Console Windows (cp1252) no Comando de Seeders

- **Sintoma:** Falha ao executar `seed_initial_data` em ambiente Windows com o erro `UnicodeEncodeError: 'charmap' codec can't encode character '\u2714' in position 0`.
- **Causa:** Uso de caracteres especiais unicode (`âœ”`) nas mensagens de saÃ­da do `stdout.write`, incompatÃ­veis com o encoding padrÃ£o de terminais Windows (cp1252/Windows-1252).
- **SoluÃ§Ã£o aplicada:** SubstituiÃ§Ã£o dos glifos unicode pelo padrÃ£o ASCII puro `[OK]` no arquivo `backend/core/management/commands/seed_initial_data.py`.
- **Como evitar no futuro:** Utilizar estritamente strings e caracteres ASCII puro para saÃ­das de terminal e logs de console.

---

## 2026-08-18 - Quebra de TransaÃ§Ã£o em Testes de Integridade no SQLite (TransactionManagementError)

- **Sintoma:** Durante a execuÃ§Ã£o de `manage.py test`, testes que validavam `UniqueConstraint` com `assertRaises(IntegrityError)` quebravam a transaÃ§Ã£o atÃ´mica global do TestCase com `TransactionManagementError: An error occurred in the current transaction`.
- **Causa:** No SQLite, o lanÃ§amento de `IntegrityError` dentro de um bloco transacional atÃ´mico corrompe a transaÃ§Ã£o ativa a menos que a operaÃ§Ã£o de falha esperada seja isolada explicitamente em um sub-bloco transacional.
- **SoluÃ§Ã£o aplicada:** Envolvimento das chamadas de teste de unicidade em blocos `with transaction.atomic():` dentro de `backend/core/tests.py`.
- **Como evitar no futuro:** Sempre envolver asserÃ§Ãµes de exceÃ§Ãµes de banco de dados (`IntegrityError`, `ValidationError`) em blocos `with transaction.atomic():` em suÃ­tes de teste do Django.

---

## 2026-08-18 - Incompatibilidade de VersÃ£o do MariaDB 10.4.x (XAMPP) no Django 5.x

- **Sintoma:** Ao executar `python backend/manage.py migrate`, o Django lanÃ§ou `NotSupportedError: MariaDB 10.5 or later is required (found 10.4.32)` seguido de erro de sintaxe SQL em `RETURNING` na gravaÃ§Ã£o de migrations.
- **Causa:** O Django 5.x por padrÃ£o exige MariaDB 10.5+ e presume suporte nativo Ã  clÃ¡usula `RETURNING` em comandos INSERT, que nÃ£o existe no MariaDB 10.4 padrÃ£o do XAMPP.
- **SoluÃ§Ã£o aplicada:** ConfiguraÃ§Ã£o de bypass de versÃ£o em `backend/config/settings.py` com `DatabaseWrapper.check_database_version_supported = lambda self: None` e desativaÃ§Ã£o das features `can_return_columns_from_insert` e `can_return_rows_from_bulk_insert`. AlÃ©m disso, ajustado `caminho_arquivo_fisico` no modelo `ControleArquivoLog` para `max_length=255` para compatibilidade estrita com Ã­ndices Ãºnicos no MySQL/MariaDB.
- **Como evitar no futuro:** Manter as configuraÃ§Ãµes de compatibilidade do driver PyMySQL no `settings.py` para assegurar suporte contÃ­nuo ao XAMPP em desenvolvimento local e a provedores Cloud em produÃ§Ã£o.

---

## 2026-08-18 - PreservaÃ§Ã£o de PontuaÃ§Ã£o na SanitizaÃ§Ã£o de Textos Livres

- **Sintoma:** Risco de remoÃ§Ã£o indesejada de sÃ­mbolos Ãºteis em endereÃ§os e descriÃ§Ãµes tÃ©cnicas (como `Âº`, `Âª`, `/`, `-`, `(`, `)`, `,`, `.`) ao sanitizar entradas para ASCII puro.
- **Causa:** ExpressÃµes regulares excessivamente restritivas (ex: `re.sub(r'[^A-Z0-9 ]', '', texto)`) eliminam pontuaÃ§Ãµes essenciais de logradouro e especificaÃ§Ãµes tÃ©cnicas.
- **SoluÃ§Ã£o aplicada:** AdoÃ§Ã£o da normalizaÃ§Ã£o diacrÃ­tica `unicodedata.normalize('NFKD', ...)` com substituiÃ§Ã£o prÃ©via de ordinais (`Âº` -> `O`, `Âª` -> `A`) e filtragem exclusiva de marcas combinadas (`unicodedata.combining(c)`), preservando toda a pontuaÃ§Ã£o e estrutura do texto original enquanto converte com seguranÃ§a para maiÃºsculas sem acento.
- **Como evitar no futuro:** Nunca utilizar regex destrutiva em campos de texto livre (endereÃ§os, descriÃ§Ãµes, observaÃ§Ãµes). Utilizar sempre a funÃ§Ã£o utilitÃ¡ria `sanitizar_texto_maiusculo` no backend e `sanitizarTextoEmTempoReal` no frontend.

---

## 2026-08-18 - Roteamento com Barras em ParÃ¢metros de CNPJ Formatado (404 Not Found)

- **Sintoma:** RequisiÃ§Ãµes para `/api/utilitarios/consulta-cnpj/33.000.167/0001-01/` retornavam erro `404 Not Found`.
- **Causa:** O conversor de rota padrÃ£o do Django `<str:cnpj>` rejeita caracteres de barra `/` presentes na formataÃ§Ã£o usual de CNPJs, interpretando-os como separadores de segmentos de rota.
- **SoluÃ§Ã£o aplicada:** SubstituiÃ§Ã£o de `path('.../<str:cnpj>/')` por `re_path(r'^utilitarios/consulta-cnpj/(?P<cnpj>.+?)/?$')` em `backend/apps/cadastros/urls.py`, permitindo que consultas recebam tanto o CNPJ limpo (`33000167000101`) quanto formatado com barras, pontos e traÃ§os.
- **Como evitar no futuro:** Em rotas que recebem parÃ¢metros com possÃ­veis caracteres de separaÃ§Ã£o de caminho (como documentos formatados com barra), utilizar `re_path` ou `<path:param>` com sanitizaÃ§Ã£o interna dos dÃ­gitos.

---

## 2026-08-18 - Bloqueio de ValidaÃ§Ã£o Aninhada por UniqueTogetherValidator do DRF em Sub-itens de Compra

- **Sintoma:** CriaÃ§Ã£o de `DocumentoFiscalCompra` com sub-lista `itens_comprados` retornava `400 Bad Request` com o erro `'documento_fiscal': ['Este campo Ã© obrigatÃ³rio']` nos itens da lista.
- **Causa:** O Django REST Framework infere automaticamente um `UniqueTogetherValidator` em `ModelSerializer` quando o model possui `UniqueConstraint` envolvendo a chave estrangeira do pai (`documento_fiscal`, `item`). Em requisiÃ§Ãµes aninhadas, o objeto pai ainda nÃ£o foi persistido no banco no momento da validaÃ§Ã£o dos filhos, fazendo com que o validador nativo falhe por ausÃªncia do ID pai.
- **SoluÃ§Ã£o aplicada:** DefiniÃ§Ã£o de `validators = []` na `class Meta` de `NotaCompraItemSerializer` e transferÃªncia da validaÃ§Ã£o anti-duplicaÃ§Ã£o de itens para o mÃ©todo `validate()` do serializer pai `DocumentoFiscalCompraSerializer`, mantendo a garantia final na `UniqueConstraint` do banco de dados MySQL.
- **Como evitar no futuro:** Em serializers de entidades relacionais 1:N que suportam escrita aninhada (como itens de notas fiscais, itens de orÃ§amento e itens de fatura), desativar o validador automÃ¡tico do DRF com `validators = []` e realizar a checagem de itens repetidos no mÃ©todo `validate()` do serializer pai.

---

## 2026-08-18 - RejeiÃ§Ã£o Precoce de Chave de Acesso NFe Formatada por MaxLengthValidator do DRF

- **Sintoma:** Ao enviar chaves de acesso NFe formatadas com espaÃ§os ou traÃ§os (ex: `3526 0833 0001 6755 0010...` com 48 a 54 caracteres), a API retornava `400 Bad Request` com mensagem `'Certifique-se de que este campo nÃ£o tenha mais de 44 caracteres.'` antes de executar o mÃ©todo `validate_chave_acesso`.
- **Causa:** O DRF herda o `max_length=44` do modelo ORM no `CharField` padrÃ£o e executa a validaÃ§Ã£o de comprimento mÃ¡ximo antes de disparar a limpeza/sanitizaÃ§Ã£o no mÃ©todo `validate_chave_acesso`.
- **SoluÃ§Ã£o aplicada:** DeclaraÃ§Ã£o explÃ­cita do campo `chave_acesso = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)` no `DocumentoFiscalCompraSerializer`, permitindo receber a string formatada pelo frontend, para entÃ£o extrair estritamente os dÃ­gitos numÃ©ricos e validar o comprimento final exato de 44 dÃ­gitos antes de gravar no banco de dados.
- **Como evitar no futuro:** Sempre que um campo do modelo tiver tamanho estrito no banco mas puder receber dados de entrada formatados (mÃ¡scaras de CPF, CNPJ, Chaves NFe, Telefones), declarar o campo no serializer com margem de caracteres suficiente para conter a mÃ¡scara antes da extraÃ§Ã£o dos dÃ­gitos.

---

## 2026-08-23 - CoerÃ§Ã£o de DateTime em DateField no DRF (AssertionError em to_representation)

- **Sintoma:** Ao serializar resposta de criaÃ§Ã£o de `Orcamento`, a view retornava erro 500 com a mensagem `AssertionError: Expected a date, but got a datetime. Refusing to coerce, as this may mean losing timezone information.`
- **Causa:** O modelo `Orcamento` utilizava `default=timezone.now` em `data_geracao = models.DateField(...)`, que devolve um objeto `datetime.datetime` em vez de um `datetime.date` puro.
- **SoluÃ§Ã£o aplicada:** SubstituiÃ§Ã£o de `default=timezone.now` por `default=timezone.localdate` no modelo `Orcamento` e atribuiÃ§Ã£o explÃ­cita de `timezone.localdate()` em `OrcamentoSerializer`.
- **Como evitar no futuro:** Em modelos Django, utilizar sempre `default=timezone.localdate` para campos `DateField` e `default=timezone.now` para campos `DateTimeField`.

---

## 2026-08-23 - Campos de Autoria em BaseModel (created_by_id / updated_by_id)

- **Sintoma:** Erro `TypeError: LancamentoFinanceiro() got unexpected keyword arguments: 'created_by'` e `ValueError: The following fields do not exist in this model: updated_by`.
- **Causa:** Modelos que herdam de `BaseModel`/`AuditableModel` utilizam colunas explÃ­citas de inteiros `created_by_id` e `updated_by_id`, preenchidas pelo `AuditUserMiddleware`. A tentativa de instanciar ou atualizar os campos usando os nomes `created_by` ou `updated_by` causava falha por ausÃªncia desses atributos relacionais diretos.
- **SoluÃ§Ã£o aplicada:** Ajuste em `services.py` para atribuir explicitamente `created_by_id=getattr(user, 'id', None)` e `updated_by_id=getattr(user, 'id', None)`.
- **Como evitar no futuro:** Em todos os serviÃ§os e models herdados de `BaseModel`, utilizar sempre os sufixos `_id` (`created_by_id`, `updated_by_id`, `deleted_by_id`).

---

## 2026-08-23 - ExigÃªncia de Campo Pai em Serializer Aninhado de Propostas

- **Sintoma:** Ao enviar `propostas_pagamento` aninhadas na criaÃ§Ã£o de `Fatura`, a API retornava `400 Bad Request` com `'fatura': ['Este campo Ã© obrigatÃ³rio']`.
- **Causa:** O `FaturaPropostaPagamentoSerializer` incluÃ­a o campo `fatura` em `fields` sem declarar `read_only=True`, exigindo que o ID da fatura estivesse presente no payload antes da persistÃªncia do objeto pai.
- **SoluÃ§Ã£o aplicada:** DefiniÃ§Ã£o explÃ­cita de `fatura = serializers.PrimaryKeyRelatedField(read_only=True)` no `FaturaPropostaPagamentoSerializer`.
- **Como evitar no futuro:** Em serializers aninhados onde o vÃ­nculo com o objeto pai Ã© estabelecido no mÃ©todo `create()` ou na camada de serviÃ§o, declarar a chave estrangeira do pai como `read_only=True`.

---

## 2026-08-23 - AcÃºmulo de RequisiÃ§Ãµes em Testes de Endpoints com ScopedRateThrottle (429 Too Many Requests)

- **Sintoma:** Durante a execuÃ§Ã£o sequencial da suÃ­te de testes de relatÃ³rios, requisiÃ§Ãµes vÃ¡lidas de exportaÃ§Ã£o em PDF e CSV retornavam `429 Too Many Requests` (`AssertionError: 429 != 200`).
- **Causa:** O DRF aplica o `ScopedRateThrottle` (`heavy_reports = 5/minute`) utilizando a camada de cache do Django. Ao rodar mÃºltiplos testes automatizados em sequÃªncia no mesmo segundo, o limite de 5 requisiÃ§Ãµes por minuto por IP/usuÃ¡rio era atingido naturalmente antes do tÃ©rmino da suÃ­te.
- **SoluÃ§Ã£o aplicada:** InclusÃ£o de `django.core.cache.cache.clear()` no `setUp()` e antes das chamadas de exportaÃ§Ã£o na classe de testes, alÃ©m de adicionar um teste especÃ­fico que valida propositalmente o bloqueio com `429 Too Many Requests` na 6Âª requisiÃ§Ã£o.
---

## 2026-08-23 - Incompatibilidade de Chaves Estrangeiras em Serializers do CatÃ¡logo (unidade_compra_id vs unidade_compra)

- **Sintoma:** Ao cadastrar um Insumo/Item pelo frontend, a API retornava `400 Bad Request` com o erro `{"unidade_compra": ["Este campo Ã© obrigatÃ³rio."]}`.
- **Causa:** O formulÃ¡rio client-side enviava o payload com a chave `unidade_compra_id`, enquanto o `ItemSerializer` no DRF declarava o campo relacional como `unidade_compra`.
- **SoluÃ§Ã£o aplicada:** ImplementaÃ§Ã£o de mÃ©todo `to_internal_value` defensivo no `ItemSerializer` para aceitar tanto `unidade_compra` quanto `unidade_compra_id` (e `unidade_consumo_id`), alÃ©m de ajustar o envio no frontend.
- **Como evitar no futuro:** Sempre implementar mapeamento flexÃ­vel de aliases `_id` no `to_internal_value` de serializers de entrada ou padronizar a convenÃ§Ã£o de chaves estrangeiras entre frontend e backend.

---

## 2026-08-23 - Falha de ValidaÃ§Ã£o por AusÃªncia de Unidade de Venda ObrigatÃ³ria no Cadastro de Produto

- **Sintoma:** Ao cadastrar um Produto Composto / Receita BOM, a API retornava `400 Bad Request` com `{"unidade_venda": ["Este campo Ã© obrigatÃ³rio."]}`.
- **Causa:** O modelo `Produto` possui a chave estrangeira `unidade_venda` como obrigatÃ³ria, porÃ©m o formulÃ¡rio do modal de Produto no frontend nÃ£o possuÃ­a o seletor de Unidade de Venda.
- **SoluÃ§Ã£o aplicada:** InclusÃ£o do seletor de Unidade de Venda no modal de Produto do frontend (populado a partir do DicionÃ¡rio UOM) e configuraÃ§Ã£o de fallback automÃ¡tico no `to_internal_value` do `ProdutoSerializer` para a UOM padrÃ£o `'UN'` caso nÃ£o informada.
- **Como evitar no futuro:** Assegurar que 100% dos campos obrigatÃ³rios dos modelos ORM estejam devidamente mapeados nos formulÃ¡rios visuais correspondentes do frontend.

---

## 2026-08-23 - Tratamento de VÃ­rgula Decimal em Inputs NumÃ©ricos do Frontend (Fator de ConversÃ£o e Horas)

- **Sintoma:** Ao digitar valores decimais utilizando o padrÃ£o brasileiro de vÃ­rgula (ex: `4,5` ou `3,5`), campos como Fator de ConversÃ£o e Horas de MÃ£o de Obra eram truncados para inteiros pelo `parseFloat` nativo do JavaScript ou rejeitados pelo backend.
- **Causa:** O JavaScript utiliza o ponto como separador decimal padrÃ£o em `parseFloat`, desconsiderando qualquer valor apÃ³s a vÃ­rgula caso a string nÃ£o passe por sanitizaÃ§Ã£o prÃ©via (`.replace(',', '.')`).
- **SoluÃ§Ã£o aplicada:** AplicaÃ§Ã£o de `.replace(',', '.')` em todos os inputs numÃ©ricos de ponto flutuante no frontend e suporte nativo a strings com vÃ­rgula no `to_internal_value` dos serializers do Django REST Framework.
- **Como evitar no futuro:** Sempre higienizar strings numÃ©ricas provenientes de inputs de usuÃ¡rios convertendo vÃ­rgulas em pontos antes do parsing matemÃ¡tico.

---

## 2026-08-23 - Falha de Preenchimento AutomÃ¡tico na Consulta de CNPJ por DivergÃªncia de Estrutura de Resposta

- **Sintoma:** Ao sair do campo de documento com 14 dÃ­gitos de CNPJ, a consulta externa ocorria com sucesso no backend, mas os campos do formulÃ¡rio (RazÃ£o Social, EndereÃ§o, etc.) nÃ£o eram preenchidos automaticamente.
- **Causa:** O backend retorna o objeto padronizado envolvido na chave `data` (`{ status: "success", data: { nome_razao: "...", ... } }`), enquanto o frontend tentava acessar diretamente na raiz do objeto (`res.razao_social`). Como `res.razao_social` era `undefined`, a condiÃ§Ã£o `if (res && res.razao_social)` nÃ£o executava a atribuiÃ§Ã£o aos inputs.
- **SoluÃ§Ã£o aplicada:** RefatoraÃ§Ã£o de `handleAutoConsultaDocumento` em `cadastros-view.js` para extrair os dados via `const data = res?.data || res;` e mapear com fallbacks flexÃ­veis (`data.nome_razao || data.razao_social || data.nome`), atribuindo diretamente aos elementos do DOM e acionando formatadores de CEP e Telefone.
- **Como evitar no futuro:** Sempre inspecionar a estrutura exata do contrato de dados retornado pelos endpoints proxy utilitÃ¡rios ao integrar o consumo no frontend.

---

---

## 2026-08-23 - Erro 404 no BotÃ£o de HistÃ³rico por PadrÃ£o de Rota do DRF Router (url_path)

- **Sintoma:** Ao clicar no botÃ£o `HISTÃ“RICO` de qualquer equipamento (na tabela ou na frota), a requisiÃ§Ã£o falhava e exibia a notificaÃ§Ã£o de erro.
- **Causa:** O mÃ©todo `@action(detail=True, methods=['get']) def historico_proprietarios` no `EquipamentoViewSet` gerava automaticamente a rota com o nome do mÃ©todo Python (`/api/equipamentos/{id}/historico_proprietarios/`, com sublinhado), enquanto a convenÃ§Ã£o de rotas da API REST do projeto e a chamada do frontend utilizam kebab-case (`/api/equipamentos/{id}/historico-proprietarios/`). A rota retornava erro HTTP `404 Not Found`.
- **SoluÃ§Ã£o aplicada:**
  1. Declarado explicitamente `url_path='historico-proprietarios'` no decorator `@action` do `EquipamentoViewSet` em `backend/apps/cadastros/views.py`.
  2. Ajustado o teste unitÃ¡rio em `backend/apps/cadastros/tests.py` para validar a rota em kebab-case.
  3. Gerados os arquivos estÃ¡ticos de Ã­cone `favicon.ico`, `icon-192.png` e `icon-512.png` na paleta *Rust Orange* para eliminar requisiÃ§Ãµes 404 de manifest e favicon.
- **Como evitar no futuro:** Sempre declarar explicitamente o parÃ¢metro `url_path='kebab-case'` em todos os mÃ©todos `@action` do DRF.

---

## 2026-08-24 - PrevenÃ§Ã£o de InconsistÃªncia Relacional em Soft Delete de Entidades Coligadas (base_manager_name = 'all_objects')

- **Sintoma:** Risco de consultas histÃ³ricas (`orcamento.cliente`, `fatura.cliente`, `documento_compra.fornecedor`, relatÃ³rios DRE/Curva ABC/InadimplÃªncia e geradores de PDF comercial) falharem, levantarem `DoesNotExist` ou omitirem registros apÃ³s o Soft Delete de um cliente, fornecedor ou equipamento.
- **Causa:** Por padrÃ£o, quando um modelo utiliza um `SoftDeleteManager` que filtra `deleted_at__isnull=True` como manager padrÃ£o, o Django ORM pode utilizÃ¡-lo para resolver chaves estrangeiras (`ForeignKey`) em modelos relacionados caso `base_manager_name` nÃ£o seja explicitamente declarado como um manager sem filtros.
- **SoluÃ§Ã£o aplicada:** ConfiguraÃ§Ã£o mandatÃ³ria de `base_manager_name = 'all_objects'` nas classes `Meta` de `SoftDeleteModel`, `BaseModel` (`backend/core/models.py`) e `Usuario` (`backend/apps/authentication/models.py`), garantindo resoluÃ§Ã£o relacional perfeita sem quebrar orÃ§amentos, faturas, relatÃ³rios ou PDFs passados.
- **Como evitar no futuro:** Em arquiteturas com Soft Delete universal no Django ORM, sempre declarar `base_manager_name = 'all_objects'` na classe base abstrata para blindar 100% da integridade referencial histÃ³rica de entidades coligadas.

---

## 2026-08-24 - CorreÃ§Ã£o de Parser de Resposta JSON da Lixeira e InclusÃ£o de Equipamentos no HistÃ³rico

- **Sintoma:** Ao inativar clientes ou equipamentos, a tabela da Lixeira exibia a mensagem "Lixeira vazia para esta entidade", e a opÃ§Ã£o de Equipamentos nÃ£o constava na combobox de entidades.
- **Causa:** O endpoint `GET /api/lixeira/` retorna o payload `{ "status": "success", "total": N, "itens": [...] }`. O JavaScript tentava extrair `const lista = res.results || res || [];`. Como `res.results` era indefinido, `lista` recebia o objeto `res`, cuja propriedade `.length` Ã© indefinida (`false`), acionando a mensagem de tabela vazia. AlÃ©m disso, a combobox continha apenas 5 entidades hardcoded e iniciava fixa em orÃ§amentos sem opÃ§Ã£o de histÃ³rico geral.
- **SoluÃ§Ã£o aplicada:** AtualizaÃ§Ã£o do parser no frontend para `const lista = res.itens || res.results || (Array.isArray(res) ? res : []);`, adiÃ§Ã£o da opÃ§Ã£o `TODAS AS ENTIDADES (HISTÃ“RICO COMPLETO)` como padrÃ£o, inclusÃ£o de `EQUIPAMENTOS / VEÃ�CULOS` e de todas as 16 entidades mapeadas, com novo campo de busca textual e coluna de tipo/entidade na tabela.
- **Como evitar no futuro:** Padronizar a extraÃ§Ã£o de listas de endpoints REST que encapsulam arrays em chaves personalizadas (`res.itens`), sempre utilizando `res.itens || res.results || (Array.isArray(res) ? res : [])`.

---

## 2026-08-24 - Bloqueio de Arquivo no Windows (PermissionError WinError 32) na RotaÃ§Ã£o de Logs DiÃ¡rios

- **Sintoma:** Ao executar testes ou em rotaÃ§Ã£o diÃ¡ria de logs, o Python lanÃ§ava `PermissionError: [WinError 32] O arquivo jÃ¡ estÃ¡ sendo usado por outro processo: '...\\logs\\app.log' -> '...\\logs\\app.log.2026-08-23'`.
- **Causa:** O handler padrÃ£o `TimedRotatingFileHandler` tenta renomear o arquivo `app.log` Ã  meia-noite via `os.rename()`, o que Ã© bloqueado pelo sistema de arquivos do Windows se houver qualquer thread ou processo mantendo o handle do arquivo aberto.
- **SoluÃ§Ã£o aplicada:** CriaÃ§Ã£o da classe personalizada `DailyDateFileHandler` em `backend/core/logging_handlers.py`, que grava diretamente nos arquivos diÃ¡rios imutÃ¡veis `app-YYYY-MM-DD.log` sem nunca necessitar renomear arquivos em disco (cumprindo 100% da arquitetura definida em `docs/FSD.md` - SeÃ§Ã£o 19).
- **Como evitar no futuro:** Em ambientes Windows ou sistemas com arquivos imutÃ¡veis por data, utilizar handlers de log que resolvem o nome do arquivo dinamicamente por data em vez de aplicar renomeaÃ§Ãµes em tempo de execuÃ§Ã£o.

---

## 2026-08-24 - DivergÃªncia de Nomes de Campos no Manifesto de Logs e Rota 404 no Log Viewer

- **Sintoma:** O Log Viewer da Central Administrativa exibia "Total de Eventos = 0" e ao clicar em "VER LOG", exibia a notificaÃ§Ã£o Toast `[ERRO] Erro ao abrir arquivo de log.`.
- **Causa:** O serializer `ControleArquivoLogSerializer` retornava o campo `data_criacao`, enquanto o JavaScript esperava `l.data_log` e `l.quantidade_linhas`. Com valores `undefined`, o frontend requisitava o endpoint com rota incorreta `/controle-arquivos-log/visualizar-log/?data=undefined` (resultando em 404). AlÃ©m disso, o serializer nÃ£o computava a contagem de linhas/eventos do arquivo fÃ­sico.
- **SoluÃ§Ã£o aplicada:**
  1. InclusÃ£o dos campos computados `data_log`, `total_eventos` e `quantidade_linhas` no `ControleArquivoLogSerializer`.
  2. Ajuste do endpoint para `/controle-arquivos-log/visualizar/` em `config.js`.
  3. Enriquecimento do modal do Log Viewer com contagem de eventos, filtro dinÃ¢mico por nÃ­vel (`[AUDIT]`, `ERROR`, `WARNING`, `INFO`), busca textual e coloraÃ§Ã£o semÃ¢ntica industrial.
  4. IntegraÃ§Ã£o universal de emissÃ£o de logs de auditoria `[AUDIT] [SOFT_DELETE]` e `[AUDIT] [RESTAURACAO]` em `SoftDeleteModel` para que todas as exclusÃµes de clientes, equipamentos e registros de negÃ³cio constem nos logs do servidor.
- **Como evitar no futuro:** Garantir alinhamento bidirecional de contratos de dados e rotas entre frontend e serializers do DRF e cobrir serializers com testes automatizados dedicados.

---

## 2026-08-24 - Rota 404 no BotÃ£o de PermissÃµes RBAC e Falta de Controle de AtivaÃ§Ã£o de Colaboradores

- **Sintoma:** Na Central do Administrador -> aba GestÃ£o de Equipe (RBAC), ao clicar no botÃ£o "PERMISSÃ•ES (10 TOGGLES)", o modal nÃ£o abria e exibia a notificaÃ§Ã£o Toast de erro "Erro ao carregar permissÃµes.". AlÃ©m disso, nÃ£o havia botÃµes para ativar/desativar colaboradores nem proteÃ§Ã£o contra auto-desativaÃ§Ã£o.
- **Causa:** O JavaScript tentava requisitar `GET /api/permissoes/?usuario_id=X` e `PATCH /api/permissoes/{id}/`. Essa rota nÃ£o existia como viewset separado no Django REST Framework, pois as permissÃµes 1:1 eram geridas como action no `UsuarioViewSet` em `/api/usuarios/{id}/permissoes/` (que atÃ© entÃ£o aceitava apenas PATCH/PUT sem suporte a GET).
- **SoluÃ§Ã£o aplicada:**
  1. Habilitado suporte completo a `GET`, `PATCH` e `PUT` na action `permissoes` do `UsuarioViewSet`, retornando a matriz completa de 10 toggles.
  2. ImplementaÃ§Ã£o de novas actions semÃ¢nticas no backend: `alternar_status`, `desativar`, `ativar` e `alterar_perfil` (promoÃ§Ã£o/rebaixamento).
  3. AplicaÃ§Ã£o de travas de seguranÃ§a mandatÃ³rias no backend: bloqueio de auto-desativaÃ§Ã£o (`request.user.id == usuario.id`), bloqueio de auto-exclusÃ£o lÃ³gica e proteÃ§Ã£o contra desativaÃ§Ã£o/rebaixamento/exclusÃ£o do Ãºnico Administrador ativo do sistema.
  4. IntegraÃ§Ã£o de emissÃ£o de logs estruturados de auditoria `[AUDIT]` para todas as aÃ§Ãµes de colaboradores (promoÃ§Ã£o, rebaixamento, ativaÃ§Ã£o, desativaÃ§Ã£o, diff de permissÃµes, convite e desbloqueio).
  5. RefatoraÃ§Ã£o da interface da aba GestÃ£o de Equipe no PWA com modal unificado de perfil e 10 toggles dinÃ¢micos, botÃµes diretos de ativaÃ§Ã£o/desativaÃ§Ã£o e auto-identificaÃ§Ã£o da conta logada com tag `[VOCÃŠ]` e botÃ£o desabilitado.
  6. CriaÃ§Ã£o de 7 novos testes automatizados dedicados no `apps.authentication.tests` cobrindo 100% dos novos cenÃ¡rios e travas de seguranÃ§a (157 testes aprovados).
- **Como evitar no futuro:** Sempre validar os contratos de rotas de actions de ViewSets no DRF com testes unitÃ¡rios de integraÃ§Ã£o e alinhar os endpoints mapeados no `config.js` do frontend.

---

## 2026-08-24 - Erro 400 ao Filtrar NÃ­vel AUDIT no Log Viewer e LimitaÃ§Ã£o de Categorias de Log

- **Sintoma:** Ao selecionar o filtro `AUDIT` no modal do Log Viewer, a API retornava `400 Bad Request` com a mensagem `"AUDIT" nÃ£o Ã© uma escolha vÃ¡lida.`, disparando o Toast de erro.
- **Causa:** O serializer `LogViewerFilterSerializer` declarava o campo `nivel` com `ChoiceField` restrito aos nÃ­veis clÃ¡ssicos de severidade do Python (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`), rejeitando categorias estruturadas de auditoria e seguranÃ§a como `AUDIT` ou `SEGURANCA`.
- **SoluÃ§Ã£o aplicada:**
  1. FlexibilizaÃ§Ã£o do campo `nivel` em `LogViewerFilterSerializer` para aceitar qualquer string vÃ¡lida com conversÃ£o automÃ¡tica para maiÃºsculas no `validate_nivel`.
  2. Aprimoramento do mÃ©todo `ler_arquivo_log_seguro` em `backend/apps/administracao/services.py` com suporte inteligente a categorias:
     - `AUDIT`: captura `[AUDIT]`, `[SOFT_DELETE]`, `[RESTAURACAO]`, `[CANCELAMENTO]`, `[ESTORNO]`.
     - `SEGURANCA`: captura `[SEGURANÃ‡A]`, `[SEGURANCA]`, `[SECURITY]`, `401`, `403`, `Unauthorized`, `Forbidden`.
     - `ERROR`: captura `[ERROR]`, `[CRITICAL]`.
     - `WARNING`: captura `[WARNING]`.
     - `INFO`: captura `[INFO]`.
     - `DEBUG`: captura `[DEBUG]`.
  3. AtualizaÃ§Ã£o do modal no frontend (`administracao-view.js`) com a combobox completa de 6 categorias bem descritas e badges estilizados no padrÃ£o *Industrial Integrity*.
  4. Adicionados testes automatizados cobrindo a filtragem de `AUDIT` e `SEGURANCA` com 100% de sucesso.
---

## 2026-08-24 - Falsos Positivos em Badges de Log por ColisÃ£o de Substrings em URLs de RequisiÃ§Ãµes HTTP

- **Sintoma:** Ao consultar o Log Viewer com filtros de severidade (ex: `&nivel=ERROR` ou `&nivel=WARNING`), as linhas normais de requisiÃ§Ã£o HTTP (`[INFO] [django.server] "GET ...&nivel=ERROR" 200`) recebiam badges incorretos de `ERROR` (vermelho) ou `WARN` (Ã¢mbar) no visualizador, e o filtro `INFO` misturava requisiÃ§Ãµes web com aÃ§Ãµes de auditoria.
- **Causa:** O visualizador no frontend determinava os badges por buscas ingÃªnuas de substrings (`.includes('ERROR')`), encontrando o termo dentro da prÃ³pria query string da URL. AlÃ©m disso, o backend nÃ£o segregava a categoria semÃ¢ntica primÃ¡ria da severidade tÃ©cnica do Python (`[INFO]`).
- **SoluÃ§Ã£o aplicada:**
  1. ImplementaÃ§Ã£o de parser semÃ¢ntico estruturado em `backend/apps/administracao/services.py`, classificando cada linha por sua categoria definitiva (`AUDIT`, `SEGURANCA`, `ERROR`, `WARNING`, `HTTP`, `INFO`, `DEBUG`) validando a posiÃ§Ã£o correta dos marcadores.
  2. AdiÃ§Ã£o da categoria `HTTP` no backend e frontend para isolar consultas de API e trÃ¡fego web.
  3. AtualizaÃ§Ã£o de `administracao-view.js` para renderizar badges estritamente a partir da propriedade `item.categoria` enviada pelo backend, eliminando 100% dos falsos positivos.
  4. AmpliaÃ§Ã£o da suÃ­te de testes unitÃ¡rios cobrindo todas as categorias de filtragem (157 testes aprovados com 100% de sucesso).
---

## 2026-08-24 - Truncamento Acidental do Arquivo de Log Real do Dia Durante ExecuÃ§Ã£o de Testes Automatizados

- **Sintoma:** ApÃ³s a execuÃ§Ã£o da suÃ­te completa de testes automatizados (`manage.py test`), o arquivo de log do dia atual (`app-2026-08-24.log`) teve seu histÃ³rico anterior substituÃ­do, passando de 160+ linhas para ~80 linhas.
- **Causa:** O teste unitÃ¡rio `test_log_viewer_leitura_estruturada_e_filtros` abria o arquivo do dia de hoje `open(f"app-{hoje_str}.log", 'w')` no modo de escrita/sobrescrita para injetar 6 linhas de teste mock, apagando o histÃ³rico real anterior.
- **SoluÃ§Ã£o aplicada:**
  1. RefatoraÃ§Ã£o do teste unitÃ¡rio para utilizar uma data fictÃ­cia e segura no futuro (`data_teste = "2099-12-31"`, arquivo `app-2099-12-31.log`).
  2. ImplementaÃ§Ã£o de estrutura `try / finally` garantindo que o arquivo e o registro de teste no manifesto sejam removidos ao final do teste.
  3. Varredura completa na suÃ­te garantindo que nenhum teste manipule arquivos diÃ¡rios reais do dia corrente.
- **Como evitar no futuro:** Testes unitÃ¡rios e de integraÃ§Ã£o que manipulam arquivos fÃ­sicos em disco devem sempre utilizar diretÃ³rios temporÃ¡rios (`tempfile.mkdtemp()`) ou datas fictÃ­cias isoladas com limpeza obrigatÃ³ria no encerramento do teste.

---

## 2026-09-01 - ReconfiguraÃ§Ã£o do Ambiente Operacional Local apÃ³s FormataÃ§Ã£o do Computador

- **Sintoma:** 1. `git status` retornava `fatal: detected dubious ownership in repository at 'D:/gestao_orcamentos_2.0'`. 2. `python.exe` do venv falhava com `did not find executable at 'C:\Users\Gusta\AppData\Local\Programs\Python\Python314\python.exe'`. 3. ConexÃ£o ao MySQL falhava com ausÃªncia da base de dados `emc_soldas` na nova instalaÃ§Ã£o do MariaDB/MySQL local.
- **Causa:** O computador foi formatado pelo usuÃ¡rio, alterando o SID do usuÃ¡rio do Windows, a pasta de instalaÃ§Ã£o nativa do Python 3.14 (agora em `C:\Users\Gusta\AppData\Local\Python\pythoncore-3.14-64`) e resetando os bancos de dados do MySQL local (porta 3306).
- **SoluÃ§Ã£o aplicada:**
  1. Executado `git config --global --add safe.directory D:/gestao_orcamentos_2.0`.
  2. Atualizado `venv/pyvenv.cfg` apontando para o novo executÃ¡vel do Python 3.14.7, preservando 100% dos pacotes jÃ¡ instalados em `site-packages`.
  3. Criado o banco de dados `emc_soldas` via script PyMySQL (`CREATE DATABASE IF NOT EXISTS emc_soldas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`).
  4. Executadas todas as migraÃ§Ãµes do Django (`call_command('migrate')`).
  5. Executado o seeder inicial de dados estruturais (`call_command('seed_initial_data')`), recriando o usuÃ¡rio Administrador Master (`admin@emcsoldas.com.br`) e todos os dicionÃ¡rios.
- **Como evitar no futuro:** Manter documentado o checklist de restauraÃ§Ã£o rÃ¡pida em `AGENTS.md` e `STATUS.md`.

---

## 2026-09-01 - Incompatibilidade de Lookup __date__range em Campos DateTimeField (AssertionError: 0 != 1)

- **Sintoma:** O teste unitÃ¡rio `test_divergencias_conciliacao` falhou com `AssertionError: 0 != 1` na asserÃ§Ã£o `self.assertEqual(dados['total_sobras_erp'], 1)`.
- **Causa:** O filtro de perÃ­odo em `backend/apps/relatorios/services.py` utilizava `data_pagamento__date__range=(data_inicio, data_fim)` sobre o campo `DateTimeField` `data_pagamento`. No SQLite (usado nos testes in-memory), a transformaÃ§Ã£o `__date` gera `django_datetime_cast_date`, comparando strings ISO com inteiros nÃ£o-cotados (`BETWEEN 2026-09-01 AND 2026-09-01` avaliado como `2016`), retornando 0 registros. AlÃ©m disso, no MySQL essa transformaÃ§Ã£o impede o uso de Ã­ndices (nÃ£o-SARGable) e depende da tabela `mysql.time_zone_name`.
- **SoluÃ§Ã£o aplicada:** ImplementaÃ§Ã£o da funÃ§Ã£o utilitÃ¡ria `converter_periodo_para_datetime_range(data_inicio, data_fim)` gerando um range timezone-aware cobrindo de `00:00:00` a `23:59:59.999999` (`America/Sao_Paulo`), e substituiÃ§Ã£o de `data_pagamento__date__range` por `data_pagamento__range=(dt_inicio, dt_fim)` em `DashboardService`, `DREService` e `DivergenciasConciliacaoService`. A suÃ­te de 157 testes automatizados passou com 100% de aprovaÃ§Ã£o.
- **Como evitar no futuro:** Sempre que filtrar intervalos de datas sobre campos `DateTimeField`, converter o perÃ­odo em range datetime timezone-aware em vez de utilizar o lookup de data `__date__range`.

---

## 2026-09-07 - InconsistÃªncia de Formatos Livres e Risco de Entrada de Placas InvÃ¡lidas

- **Sintoma:** O campo `placa` no cadastro de equipamentos/veÃ­culos aceitava strings arbitrÃ¡rias sem restriÃ§Ã£o estrutural de caracteres, permitindo a gravaÃ§Ã£o de placas incompletas ou com formatos fora do padrÃ£o veicular brasileiro.
- **Causa:** AusÃªncia de validaÃ§Ã£o especÃ­fica de regex no serializer de equipamentos e de mÃ¡scara restritiva no frontend para o formato veicular brasileiro (padrÃ£o antigo `AAA-0000` e padrÃ£o Mercosul `AAA0A00`).
- **SoluÃ§Ã£o aplicada:**
  1. CriaÃ§Ã£o da funÃ§Ã£o utilitÃ¡ria `validar_placa(valor)` em `backend/core/utils.py` com sanitizaÃ§Ã£o para maiÃºsculas e validaÃ§Ã£o regex estrita: `^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$`.
  2. ImplementaÃ§Ã£o de validaÃ§Ã£o defensiva em `apps/cadastros/serializers.py` (`validate_placa`) retornando `400 Bad Request` semÃ¢ntico.
  3. AdiÃ§Ã£o de mÃ¡scara de digitaÃ§Ã£o em tempo real no frontend (`frontend/assets/js/utils.js`: `formatarPlacaVeiculo`) com restriÃ§Ã£o posicional estrita: posiÃ§Ãµes 0-2 exclusivamente letras, posiÃ§Ã£o 3 nÃºmero, posiÃ§Ã£o 4 letra ou nÃºmero, e posiÃ§Ãµes 5-6 nÃºmeros.
  4. ValidaÃ§Ã£o e disparo de toast industrial no submit dos modais de cadastro de equipamento e frota em `cadastros-view.js`.
- **Como evitar no futuro:** Campos opcionais com padrÃµes normativos (como placas, documentos, CEP, CNPJ/CPF) devem sempre ter validaÃ§Ã£o simÃ©trica em duas camadas: mÃ¡scara reativa no frontend para guiar o operador e validaÃ§Ã£o estrita no backend REST para garantir a integridade dos dados.

---

## 2026-09-07 - RetenÃ§Ã£o de Scripts Antigos no Navegador por Cache EstÃ¡tico Stale do Service Worker (PWA)

- **Sintoma:** ApÃ³s implementar melhorias na mÃ¡scara de placas no arquivo `utils.js`, o navegador do usuÃ¡rio continuava executando a funÃ§Ã£o legada (permitindo digitar strings exclusivamente com letras sem colocar hÃ­fen e adicionando hÃ­fen em nÃºmeros), ignorando o novo cÃ³digo disponÃ­vel no servidor.
- **Causa:** O Service Worker (`frontend/sw.js`) utiliza estratÃ©gia de cache estÃ¡tico com `caches.match()` prioritÃ¡rio sob a versÃ£o estÃ¡tica `emc-soldas-v2.7`. Como o `CACHE_NAME` nÃ£o havia sido incrementado e o arquivo `index.html` nÃ£o possuÃ­a sufixos de versionamento nas tags `<script>`, o navegador utilizava os arquivos JS desatualizados gravados no Cache Storage local.
- **SoluÃ§Ã£o aplicada:**
  1. Incremento de versÃ£o em `frontend/sw.js` para `CACHE_NAME = 'emc-soldas-v2.8'` com purga imediata de versÃµes anteriores no evento `activate`.
  2. ImplementaÃ§Ã£o de cache-busting em `frontend/index.html`, sufixando todas as tags `<script src="...?v=2.8">` e folhas de estilo `<link rel="stylesheet" href="...?v=2.8">`.
  3. InstituiÃ§Ã£o de regra mandatÃ³ria na SeÃ§Ã£o 6 e 7 do `AGENTS.md` tornando obrigatÃ³rio o incremento de versÃ£o no `sw.js` e `index.html` em toda alteraÃ§Ã£o de frontend, acompanhado de instruÃ§Ã£o de reload forÃ§ado (`Ctrl + Shift + R`).
- **Como evitar no futuro:** Nunca alterar arquivos JS/CSS em PWAs com Service Worker sem simultaneamente incrementar a versÃ£o em `sw.js` e atualizar os sufixos `?v=X.Y` no `index.html`.

---

## 2026-09-11 - Falha na Leitura de Extratos CSV Acentuados e Incompatibilidade de Contrato de Dados na ConciliaÃ§Ã£o BancÃ¡ria

- **Sintoma:** Ao realizar upload de extrato bancÃ¡rio CSV na tela de ConciliaÃ§Ã£o BancÃ¡ria Split-Screen, a aplicaÃ§Ã£o exibia mensagem de sucesso mas nenhuma transaÃ§Ã£o era exibida (`0 TRANSAÃ‡Ã•ES` e `Nenhuma transaÃ§Ã£o encontrada no arquivo`), alÃ©m de os valores numÃ©ricos serem lidos como descriÃ§Ã£o. Adicionalmente, o sistema nÃ£o possuÃ­a tela no frontend para criaÃ§Ã£o e gestÃ£o de contas bancÃ¡rias.
- **Causa:**
  1. O parser de CSV buscava apenas por termos sem acento (`descricao`), falhando no match em cabeÃ§alhos como `Data,Valor,Identificador,DescriÃ§Ã£o` e acionando fallback que selecionava a coluna 1 (`Valor`) como descriÃ§Ã£o.
  2. O backend retornava o extrato na chave `res.extrato`, enquanto o frontend lia `res.transacoes || []` (`undefined`).
  3. AusÃªncia de tela de Contas BancÃ¡rias na Tesouraria para associar aos extratos e aos lanÃ§amentos.
- **SoluÃ§Ã£o aplicada:**
  1. CriaÃ§Ã£o da aba dedicada "CONTAS BANCÃ�RIAS" em `financeiro-view.js` com cards de KPIs, listagem, cadastro e ediÃ§Ã£o de saldos/limites.
  2. ImplementaÃ§Ã£o de motor universal de CSV em 3 camadas em `parsers.py` (normalizaÃ§Ã£o fonÃ©tica sem acento via `NFKD`, sinÃ´nimos multi-banco, heurÃ­stica de inspeÃ§Ã£o por amostragem e filtro de ruÃ­do de saldo anterior).
  3. CompatibilizaÃ§Ã£o de chaves no backend e no frontend (`res.extrato || res.transacoes`), adiÃ§Ã£o de seletor de conta bancÃ¡ria na conciliaÃ§Ã£o e inclusÃ£o de categoria contÃ¡bil no modal de lanÃ§amento rÃ¡pido.
  4. Incremento de versÃ£o do Service Worker PWA para `v4.15` e cache-busting no `index.html`.
- **Como evitar no futuro:** Sempre normalizar e sanitizar termos de arquivos de terceiros (como bancos) e manter contratos de API documentados e sincronizados com os handlers de frontend.

---

## 2026-09-14 - Falha de Upload de Extratos no Celular via Provedor de Nuvem (OneDrive) e InterceptaÃ§Ã£o no Service Worker (Failed to fetch)

- **Sintoma:** Ao tentar importar um extrato bancÃ¡rio pelo smartphone (via 4G/5G atravÃ©s do tÃºnel Cloudflare), o PWA disparava inicialmente `[ERRO] Sem conexÃ£o com o servidor da oficina. OperaÃ§Ã£o offline.` e, apÃ³s ajuste no Service Worker, `[ERRO] Failed to fetch`.
- **Causa:**
  1. **Arquivo Remoto no Android (OneDrive):** O usuÃ¡rio estava selecionando o arquivo diretamente da pasta virtual do OneDrive no seletor de arquivos do Android. O sistema operacional entrega um ponteiro virtual (`content://`) sem os bytes fÃ­sicos em cache local. Quando o navegador Chrome tenta ler os bytes para montar o payload multipart/form-data do `fetch()`, a leitura do stream Ã© abortada pelo sistema operacional mÃ³vel, gerando imediatamente a exceÃ§Ã£o `TypeError: Failed to fetch` antes mesmo de transmitir os pacotes para a rede.
  2. **InterceptaÃ§Ã£o no Service Worker:** Originalmente, o `sw.js` interceptava requisiÃ§Ãµes `POST` de upload e mascarava o erro do navegador gerando um HTTP 503 com aviso de *"Sem conexÃ£o com o servidor da oficina"*.
- **SoluÃ§Ã£o aplicada:**
  1. **Bypass de MutaÃ§Ã£o no Service Worker:** AdiÃ§Ã£o da clÃ¡usula `if (event.request.method !== 'GET') return;` no listener de `fetch` em `frontend/sw.js` (PWA v4.31), garantindo que uploads trafeguem diretamente pela pilha de rede nativa do navegador com buffers e retransmissÃµes do SO.
  2. **Download Local do Arquivo:** O usuÃ¡rio baixou o arquivo do OneDrive para o armazenamento fÃ­sico local do smartphone (pasta `Downloads`), permitindo que o Chrome lesse os bytes instantaneamente e transmitisse o arquivo com 100% de sucesso (resposta HTTP 200 OK com 32.737 bytes de transaÃ§Ãµes processadas).
- **Como evitar no futuro:** Ao realizar uploads em navegadores mÃ³veis (Android/iOS), garantir que os arquivos estejam salvos no armazenamento local do aparelho (e nÃ£o como referÃªncias remotas em nuvens como OneDrive/Google Drive). Manter o Service Worker configurado para nunca interceptar mÃ©todos de mutaÃ§Ã£o (`POST`/`PUT`/`DELETE`).

---

## 2026-10-03 - Erro de SerializaÃ§Ã£o de Comprovantes em LanÃ§amentos Financeiros (O dado submetido nÃ£o era um arquivo)

- **Sintoma:** Ao anexar uma Nota Fiscal ou comprovante a um lanÃ§amento do Caixa Real na Tesouraria (ou ao criar/editar lanÃ§amentos com anexo), o sistema apresentava o toast de erro: `Erro ao anexar comprovante: COMPROVANTE: O dado submetido nÃ£o era um arquivo. Cheque o tipo de codificaÃ§Ã£o no formulÃ¡rio.`
- **Causa:** O endpoint `/api/conciliacao/upload-comprovante/` salvava fisicamente o arquivo no disco do servidor e retornava um JSON com o caminho relativo (ex: `comprovantes/2026/10/arquivo.pdf`). Ao chamar `PATCH /api/lancamentos-financeiros/{id}/` com esse caminho em string, o `LancamentoFinanceiroSerializer` gerava um erro de validaÃ§Ã£o do DRF, pois, sendo um `ModelSerializer` de um modelo com `FileField`, ele exigia obrigatoriamente um objeto binÃ¡rio de upload (`UploadedFile`) e rejeitava strings.
- **SoluÃ§Ã£o aplicada:**
  1. CriaÃ§Ã£o do campo hÃ­brido customizado `ComprovanteFileOrCharField(serializers.FileField)` em `backend/apps/financeiro/serializers.py`, com suporte a strings (caminhos relativos e URLs), uploads diretos e valores nulos.
  2. DeclaraÃ§Ã£o explÃ­cita dos campos `comprovante` e `nome_arquivo_comprovante` no `LancamentoFinanceiroSerializer`.
  3. AdiÃ§Ã£o de testes unitÃ¡rios automatizados em `backend/apps/financeiro/tests.py` cobrindo PATCH com caminho relativo, desvinculaÃ§Ã£o com `null` e criaÃ§Ã£o via POST.
- **Como evitar no futuro:** Em modelos do DRF onde o fluxo de upload de arquivos Ã© desacoplado (o upload do arquivo binÃ¡rio ocorre em um endpoint auxiliar e a persistÃªncia do vÃ­nculo ocorre posteriormente via PATCH/POST em JSON), utilizar serializers fields customizados que aceitem tanto instÃ¢ncias de arquivo quanto caminhos de arquivos jÃ¡ salvos.

---

## 2026-10-03 - Duplicidade de LanÃ§amentos e de Saldo na ImportaÃ§Ã£o de Extratos BancÃ¡rios com LanÃ§amentos Manuais PrÃ©-existentes

- **Sintoma:** Ao realizar um lanÃ§amento manual no Caixa Real (ex: entrada de R$ 6.770,00 em 02/06/2025) e posteriormente importar o extrato bancÃ¡rio (OFX/CSV) daquele perÃ­odo, o sistema criava um segundo lanÃ§amento idÃªntico no Caixa Real para o mesmo dia, duplicando a movimentaÃ§Ã£o financeira e o saldo da conta bancÃ¡ria.
- **Causa:**
  1. O serviÃ§o `enriquecer_transacao_inteligencia` apenas buscava lanÃ§amentos com `is_conciliado=True` ou com mesmo `fitid`. LanÃ§amentos manuais feitos no Caixa Real iniciam com `is_conciliado=False` e sem `fitid`, passando despercebidos pela triagem.
  2. A comparaÃ§Ã£o nÃ£o considerava discrepÃ¢ncias de nomenclatura entre o extrato bancÃ¡rio (ex: "PIX RECEBIDO CAVENGE ENGENHARIA") e o lanÃ§amento manual informado pelo operador (ex: "SERVICO DE SOLDA FLANGE"), exigindo conferÃªncia baseada em valor ($\pm$ R$ 0,05) e janela temporal ($\pm$ 3 dias).
  3. Na importaÃ§Ã£o em lote (`executar_importacao_lote`), o backend sempre criava um novo registro `LancamentoFinanceiro` e recalculava o saldo da conta, creditando/debitando o valor pela segunda vez quando o lanÃ§amento manual jÃ¡ havia sido lanÃ§ado como `PAGO`.
- **SoluÃ§Ã£o aplicada:**
  1. No backend (`backend/apps/conciliacao/services.py`), implementaÃ§Ã£o da detecÃ§Ã£o de correspondÃªncias de lanÃ§amentos manuais nÃ£o conciliados (`is_conciliado=False`) baseada em conta, direÃ§Ã£o (`ENTRADA`/`SAIDA`), valor exato ($\pm$ R$ 0,05) e janela temporal de atÃ© $\pm$ 3 dias, anexando o objeto `lancamento_correspondente`.
  2. AtualizaÃ§Ã£o de `ItemImportacaoLoteSerializer` para aceitar `lancamento_existente_id` e tornar `categoria_id` opcional na vinculaÃ§Ã£o.
  3. No serviÃ§o `executar_importacao_lote`, suporte a `lancamento_existente_id`: se o lanÃ§amento manual jÃ¡ estava `PAGO` na mesma conta (`ja_impactou_saldo`), o sistema apenas concilia o lanÃ§amento existente (`is_conciliado=True`, `fitid`, `data_conciliacao=now`) e **nÃ£o altera o saldo da conta novamente**, prevenindo 100% da duplicidade contÃ¡bil e patrimonial.
  4. No frontend (`frontend/assets/js/views/conciliacao-view.js`), abertura automÃ¡tica do modal industrial de conferÃªncia anti-duplicidade ao importar extratos com correspondÃªncias, permitindo ao usuÃ¡rio escolher entre "VINCULAR E CONCILIAR (Recomendado)", "CRIAR NOVO" ou "DESCARTAR", alÃ©m de controles contextuais nos cards da Mesa de Triagem e atualizaÃ§Ã£o do botÃ£o de importaÃ§Ã£o.
  5. Incremento de versÃ£o do Service Worker PWA para `v4.34` e sufixos de cache-busting `?v=4.34` no `index.html`.
  6. AdiÃ§Ã£o de testes unitÃ¡rios automatizados cobrindo detecÃ§Ã£o de correspondÃªncia e vinculaÃ§Ã£o atÃ´mica em `backend/apps/conciliacao/tests.py`.
- **Como evitar no futuro:** Sempre que um fluxo de importaÃ§Ã£o em lote interagir com o RazÃ£o ContÃ¡bil / Caixa Real, verificar se jÃ¡ existem tÃ­tulos ou lanÃ§amentos equivalentes pendentes de conciliaÃ§Ã£o por valor e data antes de criar novos registros, fornecendo conferÃªncia assistida ao operador com opÃ§Ã£o preferencial de vinculaÃ§Ã£o.

---

## 2026-10-03 - Dashboard Zerado por Incompatibilidade de Contrato de Dados e Falha Silenciosa de CONVERT_TZ no MySQL

- **Sintoma:** O Dashboard Principal (`#/dashboard`) exibia todos os 5 Flip Cards zerados (`0` ou `R$ 0,00`), o grÃ¡fico de Receitas x Despesas vazio com mensagem *"Sem dados suficientes para exibiÃ§Ã£o do grÃ¡fico"* e o feed de atividades recentes como *"Nenhuma atividade recente registrada"*, mesmo havendo lanÃ§amentos financeiros, saldo em contas e tÃ­tulos em atraso no banco de dados.
- **Causa:**
  1. **Mismatch de Contrato nos Flip Cards:** O frontend tentava ler `const cards = res.cards || {}`, mas o backend retornava os cards diretamente na raiz (`res.operacao`, `res.faturamento`, etc.). AlÃ©m disso, os nomes dos atributos internos divergiam (ex: `op.aprovados` vs `op.orcamentos_aprovados`, `rec.faturamento_real` vs `rec.receita_real`, `cxa.saldo_bancario_real` vs `cxa.saldo_real_consolidado`).
  2. **Falha Silenciosa no MySQL (`CONVERT_TZ`):** No grÃ¡fico mensal, o backend usava filtros ORM `data_pagamento__year=ano, data_pagamento__month=mes`. No MySQL com `USE_TZ = True`, isso gerava SQL `EXTRACT(MONTH FROM CONVERT_TZ(data_pagamento, 'UTC', 'America/Sao_Paulo')) = mes`. Sem tabelas de timezone populadas no MySQL (padrÃ£o no Windows/XAMPP), `CONVERT_TZ` retorna `NULL`, fazendo a clÃ¡usula avaliar como falso para 100% das linhas e zerando o grÃ¡fico. No frontend, buscava-se `res.historico` enquanto o backend devolvia `res.meses`.
  3. **Incompatibilidade no Feed:** O backend retornava uma lista direta `[...]` e o frontend esperava `res.atividades`, alÃ©m de buscar `item.data_hora` em vez de `item.timestamp`.
  4. **Filtros de PerÃ­odo Ignorados:** Os botÃµes "HOJE", "MÃŠS ATUAL" e "ANO" passavam `?periodo=X`, ignorado pelo backend.
- **SoluÃ§Ã£o aplicada:**
  1. **Contrato Universal nos Flip Cards:** Backend atualizado para retornar as chaves de topo e tambÃ©m a chave `cards: { ... }` como espelho, com todos os aliases de propriedades esperados pelo frontend (`aprovados`, `em_execucao`, `concluidos`, `cancelados`, `rascunhos`, `faturadas`, `pagas`, `faturamento_real`, `saldo_bancario_real`, `vencidas`, etc.). Frontend atualizado com `res.cards || res || {}` e fallbacks defensivos.
  2. **Consultas Range SARGable no GrÃ¡fico:** SubstituiÃ§Ã£o dos lookups `__year` e `__month` por faixas SARGable `data_pagamento__gte=dt_ini_mes, data_pagamento__lt=dt_fim_mes` via `converter_periodo_para_datetime_range`. Isso elimina dependÃªncia de tabelas de fuso horÃ¡rio do MySQL, utiliza o Ã­ndice B-Tree e funciona 100% em qualquer SGBD. Retornados `meses` e `historico`, `mes_nome` e `mes_sigla`, e determinaÃ§Ã£o inteligente de ano caso o ano corrente nÃ£o possua dados.
  3. **CompatibilizaÃ§Ã£o do Feed:** Backend retorna `timestamp` e `data_hora`, e frontend suporta tanto lista direta quanto objeto com chave `atividades`.
  4. **Filtros de PerÃ­odo:** Suporte implementado em `FiltroPeriodoSerializer` e `DashboardFlipCardsView` (`hoje`, `mes`, `ano`).
  5. **Versionamento PWA:** Cache sincronizado para `v4.36` no `sw.js` e `index.html`.
- **Como evitar no futuro:** Nunca utilizar lookups `__year` ou `__month` em campos `DateTimeField` quando operando com MySQL/MariaDB com `USE_TZ = True`; preferir sempre faixas explÃ­citas de data/hora (`__gte` e `__lt`) com datetimes cientes de fuso horÃ¡rio. Adotar contratos de API defensivos com espelhos de propriedades e fallbacks seguros.

## 2026-10-03 - Tooltips exibidas atrás dos modais

- **Sintoma:** O componente visual de tooltip dos gráficos (.chart-tooltip) não estava se sobrepondo a janelas modais ativas, ficando escondido.
- **Causa:** O z-index configurado na classe .chart-tooltip era 1000, enquanto as sobreposições de modais (.modal-overlay) e modais (.modal-card) possuíam z-index 9999 ou 10000, e outros componentes como dropdowns usavam até 100050.
- **Solução aplicada:** O z-index da classe .chart-tooltip no arquivo industrial-integrity.css foi alterado para 999999 garantindo sobreposição universal. O cache do PWA foi invalidado incrementando a versão em sw.js e index.html.
- **Como evitar no futuro:** Sempre que criar elementos "flutuantes" universais (como tooltips ou toasts), garantir que seu z-index seja hierarquicamente superior ao dos containers modais no Design System.
## 2026-10-03 - Toasts de erro escondidos atrás dos modais

- **Sintoma:** O balão de notificação (toast) indicando erros ("preencha os campos em vermelho") estava sendo ocultado pela máscara do modal de compras.
- **Causa:** O .toast-container possuía z-index 10000 estático, enquanto a mecânica de empilhamento de modais no JS atribuía z-index a partir de 100000 (modalStack.length * 20).
- **Solução aplicada:** O z-index da classe .toast-container foi alterado para 999999 e os dropdowns (combobox e multiselect) para 999998 no industrial-integrity.css. Cache PWA atualizado para v4.47.
- **Como evitar no futuro:** Avaliar o peso do z-index ao utilizar empilhamento dinâmico no JS, documentando a hierarquia máxima permitida para que elementos globais (toasts) sempre fiquem no topo.
## 2026-10-03 - Combobox customizada não destaca borda vermelha na validação

- **Sintoma:** Ao tentar salvar a Nota de Entrada sem selecionar o fornecedor, o Toast de erro exibia a mensagem, mas a combobox não recebia a borda de validação em vermelho.
- **Causa:** O código JavaScript tentava resgatar a instância customizada buscando pelo pai closest('.emc-combobox-wrapper'). Porém, o utils.js constrói o combobox customizado com a classe .emc-combobox como elemento irmão ao <select> nativo, apontando para ele via atributo data-for. A variável ornecedorTrigger ficava como 
ull, falhando silenciosamente a troca de estilo.
- **Solução aplicada:** Substituição da busca pelo seletor apropriado usando .emc-combobox[data-for=""].
- **Como evitar no futuro:** Sempre mapear as instâncias customizadas injetadas no DOM pelos atributos de relação (como data-for) ao invés de usar closest(), já que a estrutura dom de injeção paralela (irmão) rompe com as buscas ancestrais.


## 2026-10-04 - Botão de Adição Inerte na Ficha Técnica BOM por Empilhamento Recursivo de Modais

- **Sintoma:** Ao cadastrar ou gerenciar a Ficha Técnica BOM de um produto (`gerenciarFichaTecnica`), o operador conseguia adicionar o primeiro insumo (ex: chapa), mas as adições subsequentes (como oxigênio, parafusos ou pregos) falhavam silenciosamente: o clique no botão `+ ADICIONAR` ficava completamente inerte, sem requisições HTTP e sem erros no console ou toast.
- **Causa:** Após salvar um item via `POST /api/fichas-tecnicas/`, a função executava recursivamente `this.gerenciarFichaTecnica(produtoId)` para atualizar a tela. Como `openModal` sempre empilha um novo overlay no DOM sem fechar o anterior, criava-se um segundo modal idêntico por cima. O navegador (`document.getElementById`) continuava referenciando os IDs do modal antigo (oculto embaixo), de modo que o botão visível no modal do topo ficava sem nenhum listener de evento atrelado.
- **Solução aplicada:** Refatoração de `gerenciarFichaTecnica` e `removerItemFicha` em `catalogo-view.js` para operar sob ciclo de vida único de modal (Single Modal Lifecycle). A atualização após adição e remoção agora ocorre in-modal via `_atualizarFichaModal`: atualiza a tabela `#ficha-tecnica-tbody`, recalcula a memória de cálculo em tempo real, limpa o campo de quantidade, reseta e atualiza as opções da combobox pesquisável excluindo insumos já inseridos na receita, e sincroniza a listagem de produtos no catálogo em background. Adicionado debounce no botão e suporte à tecla `Enter` no input de quantidade. Cache PWA atualizado para `v4.49`.
- **Como evitar no futuro:** Nunca chamar métodos que abrem modais (`openModal`) como estratégia de "refresh" de dados de um modal que já está em exibição. Em vez disso, isolar a renderização/atualização dos nós internos do DOM em funções reativas dedicadas que apenas mutem os elementos existentes sem instanciar novas camadas modais.
