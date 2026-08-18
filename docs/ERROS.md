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
