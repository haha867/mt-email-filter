from decimal import Decimal
import tempfile
import os

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from unittest import skip
from rest_framework import status

from efu_engine.tests import init_test
init_test()

from rest_framework.test import APIClient

from efu_auth.models import (
    Rule,
    RuleSet
)

from efu_engine.serializers import (
    RuleSerializer,
    RuleSetSerializer,
)


RULESET_URL = reverse('efu_engine:ruleset-list')



# function -> since the required url has to include parameter
def detail_url(ruleset_id):
    """Create and return a ruleset detail URL."""
    #return reverse('ruleset:ruleset-detail', args=[ruleset_id]
    return reverse('efu_engine:ruleset-detail', args=[ruleset_id]
)

def create_ruleset(user, **params):
    """Create and return a sample ruleset."""
    defaults = {
        'name': 'Sample ruleset name',
        'description': 'Sample description'
    }
    defaults.update(params)

    ruleset = RuleSet.objects.create(user=user, **defaults)
    return ruleset

def create_user(**params):
    """Create and return a new user."""
    return get_user_model().objects.create_user(**params)

#@skip('')
class PublicRuleSetAPITests(TestCase):
    """Test unauthenticated API requests."""

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """Test auth is required to call API."""
        res = self.client.get(RULESET_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateRuleSetApiTests(TestCase):
    """Test authenticated API requests."""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='user@example.com', password='test123')
        self.client.force_authenticate(self.user)

    def test_retrieve_rulesets(self):
        """Test retrieving a list of rulesets."""
        create_ruleset(user=self.user)
        create_ruleset(user=self.user)

        res = self.client.get(RULESET_URL)

        rulesets = RuleSet.objects.all().order_by('-id')
        serializer = RuleSetSerializer(rulesets, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ruleset_list_limited_to_user(self):
        """Test list of rulesets is limited to authenticated user."""
        other_user = create_user(email='other@example.com', password='test123')
        create_ruleset(user=other_user)
        create_ruleset(user=self.user)

        res = self.client.get(RULESET_URL)

        rulesets = RuleSet.objects.filter(user=self.user)
        serializer = RuleSetSerializer(rulesets, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_get_ruleset_detail(self):
        """Test get ruleset detail."""
        ruleset = create_ruleset(user=self.user)

        url = detail_url(ruleset.id)
        res = self.client.get(url)

        serializer = RuleSetSerializer(ruleset)
        self.assertEqual(res.data, serializer.data)

    def test_create_ruleset(self):
        """Test creating a ruleset."""
        #pdb.set_trace()
        payload = {
            'name': 'Search Positions',
            'description': 'Find all submitted applications'
        }
        res = self.client.post(RULESET_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ruleset = RuleSet.objects.get(id=res.data['id'])
        for k, v in payload.items():
            self.assertEqual(getattr(ruleset, k), v)
        self.assertEqual(ruleset.user, self.user)

    def test_partial_update(self):
        """Test partial update of a ruleset."""
        ruleset = create_ruleset(
            user=self.user,
            name='Sample ruleset',
        )

        payload = {'name': 'New ruleset name'}
        url = detail_url(ruleset.id)
        res = self.client.patch(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ruleset.refresh_from_db()
        self.assertEqual(ruleset.name, payload['name'])
        self.assertEqual(ruleset.user, self.user)

    def test_full_update(self):
        """Test full update of ruleset."""
        ruleset = create_ruleset(
            user=self.user,
            name='Sample ruleset',
            description='Sample ruleset description.',
        )

        payload = {
            'name': 'New ruleset name',
            'description': 'New ruleset description'
        }
        url = detail_url(ruleset.id)
        res = self.client.put(url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ruleset.refresh_from_db()
        for k, v in payload.items():
            self.assertEqual(getattr(ruleset, k), v)
        self.assertEqual(ruleset.user, self.user)

    def test_update_user_returns_error(self):
        """Test changing the ruleset user results in an error."""
        new_user = create_user(email='user2@example.com', password='test123')
        ruleset = create_ruleset(user=self.user)

        payload = {'user': new_user.id}
        url = detail_url(ruleset.id)
        self.client.patch(url, payload)

        ruleset.refresh_from_db()
        self.assertEqual(ruleset.user, self.user)

    def test_delete_ruleset(self):
        """Test deleting a ruleset successful."""
        ruleset = create_ruleset(user=self.user)

        url = detail_url(ruleset.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RuleSet.objects.filter(id=ruleset.id).exists())

    def test_ruleset_other_users_ruleset_error(self):
        """Test trying to delete another users ruleset gives error."""
        new_user = create_user(email='user2@example.com', password='test123')
        ruleset = create_ruleset(user=new_user)

        url = detail_url(ruleset.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(RuleSet.objects.filter(id=ruleset.id).exists())

    def test_create_ruleset_with_new_rules(self):
        """Test creating a ruleset with new rules."""
        payload = {
            'name': 'positions', 'description': 'check position name in the header',
            'rules': [{'name': 'ingener', 'pattern':'senior'}, {'name': 'vp', 'pattern':'technology'}],
        }
        res = self.client.post(RULESET_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        rulesets = RuleSet.objects.filter(user=self.user)
        self.assertEqual(rulesets.count(), 1)
        ruleset = rulesets[0]
        self.assertEqual(ruleset.rules.count(), 2)
        for tag in payload['rules']:
            exists = ruleset.rules.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_ruleset_with_existing_rules(self):
        """Test creating a ruleset with existing tag."""
        rule_indian = Rule.objects.create(user=self.user, name='Indian', pattern='empty')
        payload = {
            'name': 'Company', 'description' :'agency',
            'rules': [{'name': 'Indian', 'pattern':'empty'}, {'name': 'Breakfast', 'pattern':'tea' }],
        }
        res = self.client.post(RULESET_URL, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        rulesets = RuleSet.objects.filter(user=self.user)
        self.assertEqual(rulesets.count(), 1)
        ruleset = rulesets[0]
        self.assertEqual(ruleset.rules.count(), 2)
        self.assertIn(rule_indian, ruleset.rules.all())
        for rule in payload['rules']:
            exists = ruleset.rules.filter(
                name=rule['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)

    def test_create_rule_on_update(self):
        """Test create rule when updating a ruleset."""
        ruleset = create_ruleset(user=self.user)

        payload = {'rules': [{'name': 'Lunch', 'pattern': 'scrambled eggs'}]}
        url = detail_url(ruleset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        new_tag = Rule.objects.get(user=self.user, name='Lunch')
        self.assertIn(new_tag, ruleset.rules.all())

    def test_update_ruleset_assign_rule(self):
        """Test assigning an existing tag when updating a ruleset."""
        rule_breakfast = Rule.objects.create(user=self.user, name='Breakfast', pattern='coffee')
        ruleset = create_ruleset(user=self.user)
        ruleset.rules.add(rule_breakfast)

        rule_lunch = Rule.objects.create(user=self.user, name='Lunch', pattern='coffee')
        payload = {'rules': [{'name': 'Lunch', 'pattern': 'coffee'}]}
        url = detail_url(ruleset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(rule_lunch, ruleset.rules.all())
        self.assertNotIn(rule_breakfast, ruleset.rules.all())

    def test_clear_ruleset_rules(self):
        """Test clearing a rulesets rules."""
        rule = Rule.objects.create(user=self.user, name='Dessert', pattern='tea')
        ruleset = create_ruleset(user=self.user)
        ruleset.rules.add(rule)

        payload = {'rules': []}
        url = detail_url(ruleset.id)
        res = self.client.patch(url, payload, format='json')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ruleset.rules.count(), 0)


    def test_filter_by_rules(self):
        """Test filtering rulesets by rules."""
        r1 = create_ruleset(user=self.user, name='Thai Vegetable Curry')
        r2 = create_ruleset(user=self.user, name='Aubergine with Tahini')
        tag1 = Rule.objects.create(user=self.user, name='Recipe', pattern='vegan')
        tag2 = Rule.objects.create(user=self.user, name='Breakfast', pattern='coffee')
        r1.rules.add(tag1)
        r2.rules.add(tag2)
        r3 = create_ruleset(user=self.user, name='Fish and chips')

        params = {'rules': f'{tag1.id},{tag2.id}'}
        res = self.client.get(RULESET_URL, params)

        s1 = RuleSetSerializer(r1)
        s2 = RuleSetSerializer(r2)
        s3 = RuleSetSerializer(r3)
        self.assertIn(s1.data, res.data)
        self.assertIn(s2.data, res.data)
        self.assertNotIn(s3.data, res.data)

