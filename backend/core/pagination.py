"""
EMC Soldas - Paginação Centralizada do Django REST Framework.
Suporte a navegação por página e limite dinâmico de itens por página.
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Paginação padrão do sistema.
    - page_size padrão: 25 itens.
    - Parâmetro para mudar tamanho: ?page_size=N
    - Limite máximo seguro: 1000 itens (para seletores de catálogo/clientes).
    - Parâmetro de página: ?page=N
    """
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 1000
    page_query_param = 'page'
