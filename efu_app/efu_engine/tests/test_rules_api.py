"""
Tests for the rules API.
"""
from decimal import Decimal
from efu_engine.tests import init_test
init_test()

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from unittest import skip
from rest_framework import status
from rest_framework.test import APIClient

from efu_auth.models import (
    Rule,
    RuleSet,
)
from efu_engine.serializers import RuleSerializer


RULES_URL = reverse('efu_engine:rule-list')


def detail_url(rule_id):
    """Create and return a rule detail url."""
    return reverse('efu_engine:rule-detail', args=[rule_id])


def create_user(email='user@example.com', password='testpass123'):
    """Create and return a user."""
    return get_user_model().objects.create_user(email=email, password=password)


class PublicRulesApiTests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required for retrieving rules."""
        res = self.client.get(RULES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

#@skip('')
class PrivateRulesApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_rules(self):
        """Test retrieving a list of rules."""
        Rule.objects.create(user=self.user, name='LinkedInf', pattern='email_linkedin')
        Rule.objects.create(user=self.user, name='FromJason', pattern='from_jason')

        res = self.client.get(RULES_URL)

        rules = Rule.objects.all().order_by('-name')
        serializer = RuleSerializer(rules, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_rules_limited_to_user(self):
        """Test list of rules is limited to authenticated user."""
        user2 = create_user(email='user2@example.com')
        Rule.objects.create(user=user2, name='FindJason', pattern='jason')
        rule = Rule.objects.create(user=self.user, name='CheckPosition',pattern='subject:developer' )

        res = self.client.get(RULES_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], rule.name)
        self.assertEqual(res.data[0]['id'], rule.id)


    def test_update_rule(self):
        """Test updating a rule."""
        rule = Rule.objects.create(user=self.user, name='After Dinner', pattern='Dinner')

        payload = {'name': 'FindCompany', 'pattern': 'Bloomberg'}
        url = detail_url(rule.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        rule.refresh_from_db()
        self.assertEqual(rule.name, payload['name'])

    def test_delete_rule(self):
        """Test deleting a rule."""
        rule = Rule.objects.create(user=self.user, name='Recipe', pattern='Breakfast')

        url = detail_url(rule.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        rules = Rule.objects.filter(user=self.user)
        self.assertFalse(rules.exists())


    def test_filter_rules_assigned_to_rulesets(self):
        """Test listing rules to those assigned to rulesets."""
        rule1 = Rule.objects.create(user=self.user, name='Recipe', pattern='Breakfast')
        rule2 = Rule.objects.create(user=self.user, name='Lunch', pattern='Location')
        ruleset = RuleSet.objects.create(
            name='Recipies from Internet',
            user=self.user,
        )
        ruleset.rules.add(rule1)

        res = self.client.get(RULES_URL, {'assigned_only': 1})

        s1 = RuleSerializer(rule1)
        s2 = RuleSerializer(rule2)
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_rules_unique(self):
        """Test filtered rules returns a unique list."""
        rule = Rule.objects.create(user=self.user, name='Breakfast', pattern='^diner$')
        Rule.objects.create(user=self.user, name='Diner', pattern='diner$')
        ruleset1 = RuleSet.objects.create(
            name='Pancakes',
            user=self.user,
        )
        ruleset2 = RuleSet.objects.create(
            name='Porridge',
            user=self.user,
        )
        ruleset1.rules.add(rule)
        ruleset2.rules.add(rule)

        res = self.client.get(RULES_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)