"""
Roteador central de URLs da API REST e Frontend do sistema EMC Soldas.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Painel Administrativo do Django
    path('admin/', admin.site.urls),

    # Endpoints da API REST (Kebab-case conforme FSD)
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.authentication.user_urls')),
    path('api/cadastros/', include('apps.cadastros.urls')),
    path('api/catalogo/', include('apps.catalogo.urls')),
    path('api/compras/', include('apps.compras.urls')),
    path('api/orcamentos/', include('apps.orcamentos.urls')),
    path('api/faturamento/', include('apps.faturamento.urls')),
    path('api/financeiro/', include('apps.financeiro.urls')),
    path('api/conciliacao/', include('apps.conciliacao.urls')),
    path('api/administracao/', include('apps.administracao.urls')),
    path('api/relatorios/', include('apps.relatorios.urls')),

    # Frontend PWA (Single Page Application Shell)
    path('', TemplateView.as_view(template_name='index.html'), name='pwa-shell'),
]

# Servir arquivos de mídia protegidos e estáticos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
