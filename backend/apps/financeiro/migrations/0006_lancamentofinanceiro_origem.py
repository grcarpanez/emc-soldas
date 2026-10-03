from django.db import migrations, models
from django.utils import timezone


def popular_origem_e_sanear_63(apps, schema_editor):
    LancamentoFinanceiro = apps.get_model('financeiro', 'LancamentoFinanceiro')

    # 1. Transações de Conciliação Bancária
    LancamentoFinanceiro.objects.filter(models.Q(fitid__isnull=False) | models.Q(is_conciliado=True)).update(origem='CONCILIACAO')

    # 2. Transações de Faturamento
    LancamentoFinanceiro.objects.filter(fatura__isnull=False).update(origem='FATURA')

    # 3. Transações de Cartão
    LancamentoFinanceiro.objects.filter(fatura_cartao__isnull=False).update(origem='CARTAO')

    # 4. Lançamentos Avulsos manuais (ex: #91 e #63)
    LancamentoFinanceiro.objects.filter(id__in=[63, 91]).update(origem='AVULSO')

    # 5. Saneamento do lançamento #63 (estornado que virou conta a pagar indevidamente)
    lanc_63 = LancamentoFinanceiro.objects.filter(id=63).first()
    if lanc_63:
        lanc_63.origem = 'AVULSO'
        lanc_63.status_pagamento = 'CANCELADO'
        lanc_63.motivo_cancelamento = 'ESTORNO DE LANCAMENTO AVULSO DUPLICADO'
        lanc_63.deleted_at = timezone.now()
        lanc_63.deleted_by_id = lanc_63.updated_by_id or lanc_63.created_by_id or 1
        lanc_63.save(update_fields=['origem', 'status_pagamento', 'motivo_cancelamento', 'deleted_at', 'deleted_by_id'])


def reverter_popular_origem(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('financeiro', '0005_lancamentofinanceiro_comprovante_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='lancamentofinanceiro',
            name='origem',
            field=models.CharField(choices=[('AGENDA', 'Conta Agendada (Contas a Pagar/Receber)'), ('AVULSO', 'Compra / Lançamento Avulso no Extrato'), ('CONCILIACAO', 'Extrato / Conciliação Bancária'), ('FATURA', 'Faturamento de Orçamentos'), ('CARTAO', 'Fatura de Cartão de Crédito')], db_index=True, default='AGENDA', max_length=20, verbose_name='Origem do Lançamento'),
        ),
        migrations.RunPython(popular_origem_e_sanear_63, reverter_popular_origem),
    ]
