"""
Tests for the Django admin modifications.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import Client
from unittest import skip

#@skip('TODO: implement')
class AdminSiteTests(TestCase):
    """Tests for Django admin."""

    def setUp(self):
        """Create user and client."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            email='admin@example.com',
            password='testpass123',
        )
        self.client.force_login(self.admin_user)
        self.user = get_user_model().objects.create_user(
            email='user@example.com',
            password='testpass123',
            name='Test User'
        )

    def test_users_lists(self):
        """Test that apiusers are listed on page."""
        '''reverse is internal Django function to get url (check Django docs)'''
        url = reverse('admin:efu_auth_apiuser_changelist')
        res = self.client.get(url)

        self.assertContains(res, self.user.name)
        self.assertContains(res, self.user.email)

    def test_edit_user_page(self):
        """Test the edit apiuser page works."""
        url = reverse('admin:efu_auth_apiuser_change', args=[self.user.id])
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)

    def test_create_user_page(self):
        """Test the edit apiuser page works."""
        url = reverse('admin:efu_auth_apiuser_add')
        res = self.client.get(url)

        self.assertEqual(res.status_code, 200)