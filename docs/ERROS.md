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




