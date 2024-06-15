from django.shortcuts import render
from drf_spectacular.utils import (
    extend_schema_view,
    extend_schema,
    OpenApiParameter,
    OpenApiTypes,
)

from rest_framework import (
    viewsets,
    # to add functionality to views
    mixins,
    status,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from efu_auth.models import (
    Rule,
    RuleSet
)
from efu_engine import serializers

@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'rules',
                OpenApiTypes.STR,
                description='Comma separated list of rule IDs to filter',
            )
        ]
    )
)
class RuleSetViewSet(viewsets.ModelViewSet):
    """View for manage recipe APIs."""
    serializer_class = serializers.RuleSetSerializer
    queryset = RuleSet.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def _params_to_ints(self, qs):
        """Convert a list of strings to integers."""
        return [int(str_id) for str_id in qs.split(',')]

    def get_queryset(self):
        """Retrieve recipes for authenticated user."""
        rules = self.request.query_params.get('rules')
        queryset = self.queryset
        if rules:
            rule_ids = self._params_to_ints(rules)
            queryset = queryset.filter(rules__id__in=rule_ids)
        return queryset.filter(
            user=self.request.user
        ).order_by('-id').distinct()

    def get_serializer_class(self):
        """Return the serializer class for request."""
        if self.action == 'list':
            return serializers.RuleSetSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new ruleset."""
        serializer.save(user=self.request.user)


@extend_schema_view(
    list=extend_schema(
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT, enum=[0, 1],
                description='Filter by items assigned to ruleset.',
            ),
        ]
    )
)
class BaseRuleSetAttrViewSet(mixins.DestroyModelMixin,
                            mixins.UpdateModelMixin,
                            mixins.ListModelMixin,
                            viewsets.GenericViewSet):
    """Base viewset for ruleset attributes."""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset to authenticated user."""
        assigned_only = bool(
            int(self.request.query_params.get('assigned_only', 0))
        )
        queryset = self.queryset
        if assigned_only:
            queryset = queryset.filter(ruleset__isnull=False)

        return queryset.filter(
            user=self.request.user
        ).order_by('-name').distinct()

class RuleViewSet(BaseRuleSetAttrViewSet):
    """Manage rules in the database."""
    serializer_class = serializers.RuleSerializer
    queryset = Rule.objects.all()

