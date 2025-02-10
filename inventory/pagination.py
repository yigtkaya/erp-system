from rest_framework.pagination import PageNumberPagination

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50  # Default number of items per page.
    page_size_query_param = 'page_size'  # Allow the client to override the page size.
    max_page_size = 100  # Maximum items allowed per page. 