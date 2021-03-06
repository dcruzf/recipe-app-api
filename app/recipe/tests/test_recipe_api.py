import tempfile
import os

from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


RECIPE_URL = reverse('recipe:recipe-list')

# Helper functions


def image_upload_url(recipe_id):
    """
    return url for recipe image upload
    """
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


def detail_url(recipe_id):
    """
    Return recipe detail url
    """
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Sample Test Tag'):
    """
    Create and return sample tag
    """
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Sample Test Ingredient'):
    """
    Create and return sample ingredient
    """
    return Ingredient.objects.create(user=user, name=name)


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

    def test_view_recipe_detail(self):
        """
        Test viewing a recipe detail
        """

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))

        url = detail_url(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """
        Test creating recipe
        """
        payload = {
            'title': 'Feijoada',
            'time_minutes': 60,
            'price': 100.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """
        Test Creating recipe with tags
        """
        tag1 = sample_tag(user=self.user, name='Feijoadas')
        tag2 = sample_tag(user=self.user, name='Buchadas')

        payload = {
            'title': 'Feijoada Com Buchada de Bode',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 60,
            'price': 100.12
        }
        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()

        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """
        Test Creating recipe with ingredients
        """
        ingredient1 = sample_ingredient(self.user)
        ingredient2 = sample_ingredient(self.user, name='P?? de porco')

        payload = {
            'title': 'Feijoada Com Buchada de Bode',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 60,
            'price': 100.12
        }

        res = self.client.post(RECIPE_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()

        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)

    def test_partial_update_recipe(self):
        """
        Test updating a recipe with patch
        """
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        new_tag = sample_tag(user=self.user, name='Feij??o')

        payload = {'title': 'Feijoada', 'tags': [new_tag.id]}
        url = detail_url(recipe.id)
        self.client.patch(url, payload)

        recipe.refresh_from_db()

        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 1)
        self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        """
        Test updating a recipe with put
        """

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))

        payload = {
            'title': 'Buchada',
            'time_minutes': 90,
            'price': 30.00
        }

        url = detail_url(recipe.id)
        self.client.put(url, payload)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 0)

    def test_filter_recipes_by_tags(self):
        """
        Test returning recipes with specific tags
        """

        recipe1 = sample_recipe(user=self.user)
        recipe2 = sample_recipe(user=self.user, title='Feijoada com picanha')
        recipe3 = sample_recipe(user=self.user, title='Buchada de bode')

        tag1 = sample_tag(user=self.user)
        tag2 = sample_tag(user=self.user, name='carne')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)

        res = self.client.get(RECIPE_URL,                              {
                              'tags': f'{tag1.id}, {tag2.id}'})

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)

    def test_filter_recipes_by_ingredients(self):
        """
        Test returning recipes with specific tags
        """

        recipe1 = sample_recipe(user=self.user)
        recipe2 = sample_recipe(user=self.user, title='Feijoada com picanha')
        recipe3 = sample_recipe(user=self.user, title='Buchada de bode')

        ingredient1 = sample_ingredient(user=self.user)
        ingredient2 = sample_ingredient(user=self.user, name='carne')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)

        res = self.client.get(
            RECIPE_URL,
            {'ingredients': f'{ingredient1.id}, {ingredient2.id}'}
            )

        serializer1 = RecipeSerializer(recipe1)
        serializer2 = RecipeSerializer(recipe2)
        serializer3 = RecipeSerializer(recipe3)

        self.assertIn(serializer1.data, res.data)
        self.assertIn(serializer2.data, res.data)
        self.assertNotIn(serializer3.data, res.data)


class RecipeImageUploadTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email='test@test.com',
                                                         password='Test123456')
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(user=self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image(self):
        """
        Test uploading an image to recipe
        """

        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)

            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)

        self.recipe.refresh_from_db()
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_invalid_image(self):
        """
        Test uploading an invalid image
        """

        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'notimage'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
