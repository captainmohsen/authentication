from rest_framework import pagination
from rest_framework.response import Response


class HeaderPagination(pagination.PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):

        headers = {
            "X-Result-Count": self.page.paginator.count,
        }

        return Response(data, headers=headers)
