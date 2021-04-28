from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer


RECIPE_URL = reverse('recipe:recipe-list')


def sample_recipe(user, **params):
    """
    Create and return a sample recipe
    """

    defaults = {'title': 'Sample recipe',
                'time_minutes': 10,
                'price': 5.11}
    defaults.update(params)

    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """
    Test ingredients Api (public)
    """

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        """
        Test that authentication is required
        """
        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """
    Test authenticated recipe API acess
    """

    def setUp(self):

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email='test@test.com',
                                                         password='test123456')

        self.client.force_authenticate(self.user)

    def test_retrive_recipes(self):
        """
        Test retrive a list of recipes
        """
        # Creating sample recipes in database (same user)
        sample_recipe(user=self.user, title='ONE')
        sample_recipe(user=self.user, title='TWO')

        # HTTP request by authenticated user
        res = self.client.get(RECIPE_URL)

        # All sample recipies from database (there is just one user)
        recipes = Recipe.objects.all().order_by('id')
        serializer = RecipeSerializer(recipes, many=True)

        # Assert it works same way
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_tu_user(self):
        """
        Test retrieving recipes for user
        """

        # Creating a different user
        user_not_same = get_user_model().objects.create_user(
            email='notsame@test.com',
            password='test123456'
        )

        # Creating sample recipes in database with two different users
        sample_recipe(user=user_not_same)
        sample_recipe(user=self.user)

        # HTTP request by authenticated user
        res = self.client.get(RECIPE_URL)

        # Same query in db and serialization
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)
