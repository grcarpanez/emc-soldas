from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
from pathlib import Path

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / 'frontend'

urlpatterns = [
    # Painel Administrativo do Django
    path('admin/', admin.site.urls),

    # Endpoints da API REST (Kebab-case conforme FSD)
    path('api/auth/', include('apps.authentication.urls')),
    path('api/', include('apps.authentication.user_urls')),
    path('api/', include('apps.catalogo.urls')),
    path('api/', include('apps.financeiro.urls')),
    path('api/', include('apps.cadastros.urls')),
    path('api/', include('apps.compras.urls')),
    path('api/', include('apps.orcamentos.urls')),
    path('api/', include('apps.faturamento.urls')),
    path('api/conciliacao/', include('apps.conciliacao.urls')),
    path('api/', include('apps.administracao.urls')),
    path('api/', include('apps.relatorios.urls')),

    # Frontend PWA (Single Page Application Shell & Static Assets)
    path('', TemplateView.as_view(template_name='index.html'), name='pwa-shell'),
    re_path(r'^(?P<path>(assets/.*|manifest\.json|sw\.js|favicon\.ico))$', serve, {'document_root': FRONTEND_DIR}),
]

# Servir arquivos de mídia protegidos e estáticos durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

