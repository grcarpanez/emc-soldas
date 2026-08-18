"""
Classes base abstratas para persistência, Soft Delete e Auditoria.
Garante integridade referencial, rastreabilidade e proibição de Hard Delete.
"""
from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet customizado que impede a listagem padrão de registros inativados."""

    def active(self):
        """Retorna apenas registros ativos (não deletados)."""
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        """Retorna exclusivamente registros que sofreram soft delete (Lixeira)."""
        return self.filter(deleted_at__isnull=False)

    def delete(self, user_id=None):
        """Sobrescreve o delete em lote para aplicar soft delete."""
        return self.update(deleted_at=timezone.now(), deleted_by_id=user_id)

    def hard_delete(self):
        """Bloqueado por padrão para cumprir a regra de Proibição de Hard Delete na V1."""
        raise PermissionError(
            "Hard Delete é estritamente proibido pela governança do sistema EMC Soldas na V1."
        )


class SoftDeleteManager(models.Manager):
    """Manager padrão que filtra registros ativos."""

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=True)

    def with_deleted(self):
        """Permite consultas incluindo registros deletados (para relatórios históricos e lixeira)."""
        return SoftDeleteQuerySet(self.model, using=self._db)

    def only_deleted(self):
        """Retorna exclusivamente registros na Lixeira."""
        return SoftDeleteQuerySet(self.model, using=self._db).filter(deleted_at__isnull=False)


class AuditableModel(models.Model):
    """
    Campos de auditoria temporal e de autoria.
    Rastreia criação e última alteração.
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data de Criação"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Data de Atualização"
    )
    created_by_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Criado por (ID do Usuário)"
    )
    updated_by_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Atualizado por (ID do Usuário)"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Injeta automaticamente o usuário autenticado da thread se não informado
        from core.middleware import get_current_user
        current_user = get_current_user()
        user_id = getattr(current_user, 'id', None) if current_user else None

        if user_id:
            if not self.pk and not self.created_by_id:
                self.created_by_id = user_id
            self.updated_by_id = user_id

        super().save(*args, **kwargs)


class SoftDeleteModel(models.Model):
    """
    Campos e métodos para controle de Soft Delete (Exclusão Lógica).
    """
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        verbose_name="Data de Exclusão Lógica"
    )
    deleted_by_id = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name="Excluído por (ID do Usuário)"
    )

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    @property
    def is_deleted(self) -> bool:
        """Verifica se o registro está excluído logicamente."""
        return self.deleted_at is not None

    def delete(self, user_id=None, using=None, keep_parents=False):
        """Aplica Soft Delete registrando data e autor."""
        self.deleted_at = timezone.now()
        if user_id:
            self.deleted_by_id = user_id
        else:
            from core.middleware import get_current_user
            current_user = get_current_user()
            if current_user and getattr(current_user, 'id', None):
                self.deleted_by_id = current_user.id
        self.save(update_fields=['deleted_at', 'deleted_by_id'])

    def soft_delete(self, user=None):
        """Alias amigável para aplicação de soft delete."""
        user_id = getattr(user, 'id', user) if user else None
        self.delete(user_id=user_id)

    def restore(self):
        """Restaura o registro da Lixeira para o estado ativo."""
        self.deleted_at = None
        self.deleted_by_id = None
        self.save(update_fields=['deleted_at', 'deleted_by_id'])


class BaseModel(AuditableModel, SoftDeleteModel):
    """
    Classe base universal para as entidades de negócio do EMC Soldas.
    Reúne Auditoria Plena e Soft Delete.
    """

    class Meta:
        abstract = True
