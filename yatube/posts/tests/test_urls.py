from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostURLTests(TestCase):
    """Тестирование URL."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Nemo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text='Здесь должно быть написано что-то очень интересное.',
            author=self.author,
            group=self.group,
        )

        cache.clear()

    def test_url_exists_at_desired_location(self):
        """Страницы доступны любому пользователю."""
        templates_url_names = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.author}/',
            f'/posts/{self.post.id}/',
        ]
        for pages in templates_url_names:
            response = self.client.get(pages)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_authorized(self):
        """Страницы доступны авторизованному пользователю."""
        templates_url_names = [
            f'/posts/{self.post.id}/edit/',
            '/create/'
        ]
        for pages in templates_url_names:
            response = self.authorized_client.get(pages)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_guest(self):
        """Перенаправляет гостя на страницу входа."""
        pages = [
            reverse('posts:post_create'),
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            )
        ]
        for redirect in pages:
            response = self.client.get(redirect)
            self.assertRedirects(
                response, reverse('users:login') + '?next=' + redirect
            )

    def test_redirect_non_author_when_to_edit_post(self):
        """Перенаправляет не автора при попытке редактировать чужой пост."""
        self.user_2 = User.objects.create(username='Anonym')
        self.authorized_client.force_login(self.user_2)
        response = self.authorized_client.get(f'/posts/{self.post.id}/edit/')
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )

    def test_unexisting_page(self):
        """Страница /unexisting_page/ должна выдать ошибку."""
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.author}/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/unexisting_page/': 'core/404.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
