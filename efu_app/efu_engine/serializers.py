from rest_framework import serializers

from efu_auth.models import (
    Rule,
    RuleSet
)


class RuleSerializer(serializers.ModelSerializer):
    """Serializer for rules."""

    class Meta:
        model = Rule
        fields = ['id', 'name', 'pattern', 'description']
        read_only_fields = ['id']


class RuleSetSerializer(serializers.ModelSerializer):
    """Serializer for recipes."""
    rules = RuleSerializer(many=True, required=False)

    class Meta:
        model = RuleSet
        fields = ['id', 'name', 'description', 'rules']
        read_only_fields = ['id']

    def _get_or_create_rules(self, rules, ruleset):
        """Handle getting or creating rules as needed."""
        auth_user = self.context['request'].user
        for rule in rules:
            rule_obj, created = Rule.objects.get_or_create(
                user=auth_user,
                **rule,
            )
            ruleset.rules.add(rule_obj)

    def create(self, validated_data):
        """Create a ruleset."""
        rules = validated_data.pop('rules', [])
        ruleset = RuleSet.objects.create(**validated_data)
        self._get_or_create_rules(rules, ruleset)
        return ruleset

    def update(self, instance, validated_data):
        """Update ruleset."""
        rules = validated_data.pop('rules', [])
        if rules is not None:
            instance.rules.clear()
            self._get_or_create_rules(rules, instance)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

