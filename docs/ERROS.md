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



