import shutil
import tempfile

from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..constants import NUMBER_OF_POSTS, TEST_POSTS
from ..forms import PostForm
from ..models import Comment, Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTests(TestCase):
    """Тестирование Views."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.author = User.objects.create(username='Nemo')
        cls.user = User.objects.create(username='Unknown')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text='Здесь должно быть написано что-то очень интересное.',
            author=self.author,
            group=self.group,
            image=self.uploaded
        )
        self.comment = Comment.objects.create(
            post_id=self.post.id,
            text='Тестовый комментарий',
            author=self.user,
        )
        cache.clear()

    def post_objects(self, post):
        objects = {
            post.id: self.post.id,
            post.text: self.post.text,
            post.author: self.author,
            post.group: self.group,
            post.image: self.post.image
        }
        return objects

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template, in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблонs 'index' сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        objects_post = self.post_objects(post)
        for value, expected in objects_post.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_group_page_show_correct_context(self):
        """Шаблон 'group_list' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context['page_obj'][0]
        group = response.context['group']
        objects_post = self.post_objects(post)
        for value, expected in objects_post.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        objects_group = {
            group.title: self.group.title,
            group.slug: self.group.slug,
        }
        for value, expected in objects_group.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблонs 'profile' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.author})
        )
        post = response.context['page_obj'][0]
        objects_post = self.post_objects(post)
        for value, expected in objects_post.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        Follow.objects.create(user=self.user, author=self.author)
        following = Follow.objects.filter(
            user=self.user,
            author=self.author
        ).exists()
        self.assertNotEqual(response.context['following'], following)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон 'post_detail' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        )
        post = response.context['post']
        comments = response.context['comments'][0]
        objects_post = self.post_objects(post)
        for value, expected in objects_post.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)
        objects_comments = {
            comments.post: self.post,
            comments.text: self.comment.text,
            comments.author: self.user,
        }
        for value, expected in objects_comments.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

    def test_create_edit_page_show_correct_context(self):
        """Шаблон 'post_edit' сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form = response.context['form']
        self.assertIsInstance(form, PostForm)
        self.assertTrue(response.context['is_edit'])

    def test_post_create_page_show_correct_context(self):
        """Шаблон 'post_create' сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form = response.context['form']
        self.assertIsInstance(form, PostForm)

    def test_post_was_in_the_right_group(self):
        """Проверяем, что пост попал в нужную группу."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        ]
        new_post = Post.objects.create(
            text='Новый тестовый пост',
            author=self.author,
            group=self.group,
        )
        for expected in pages:
            with self.subTest(expected=expected):
                response = self.authorized_client.get(expected)
                self.assertEqual(new_post, response.context['page_obj'][0])

    def test_post_not_in_another_group(self):
        """Проверяем, что пост не попал в другую группу."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = Post.objects.exclude(group=self.post.group)
        self.assertNotIn(post, response.context['page_obj'])

    def test_cache_index(self):
        """Проверяем работу кеша главной страницы. """
        response = self.client.get(reverse('posts:index'))
        Post.objects.create(
            author=self.user,
            text='Проверка кеша главной страницы.',
            group=self.group
        )
        response_before_del_post = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_before_del_post.content)
        self.post.delete()
        response_del_post = self.client.get(reverse('posts:index'))
        self.assertEqual(response.content, response_del_post.content)
        cache.clear()
        response_cache_clean = self.client.get(reverse('posts:index'))
        self.assertNotEqual(
            response.content,
            response_cache_clean.content
        )


class PaginatorTest(TestCase):
    """Тестирование пагинатора."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.author = User.objects.create(username='Nemo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = []
        for i in range(TEST_POSTS):
            cls.posts.append(
                Post(
                    text=f'Много тестового текста {i}',
                    author=cls.author,
                    group=cls.group,
                )
            )
        Post.objects.bulk_create(cls.posts)

    def test_first_page_contains_ten_records(self):
        """Проверяем, что количество постов на первой странице равно 10."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author}),
        ]
        for expected in pages:
            with self.subTest(expected=expected):
                response = self.client.get(expected)
                self.assertEqual(
                    len(response.context['page_obj']), NUMBER_OF_POSTS
                )

    def test_second_page_contains_five_records(self):
        """Проверяем, что количество постов на второй странице равно 5."""
        pages = [
            reverse('posts:index') + '?page=2',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2',
            reverse(
                'posts:profile', kwargs={'username': self.author}
            ) + '?page=2',
        ]
        for expected in pages:
            with self.subTest(expected=expected):
                response = self.client.get(expected)
                self.assertEqual(
                    len(response.context['page_obj']),
                    TEST_POSTS - NUMBER_OF_POSTS
                )


class FollowTest(TestCase):
    """Тестирование подписок."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cache.clear()
        cls.author = User.objects.create(username='Nemo')
        cls.user = User.objects.create(username='Unknown')
        cls.post = Post.objects.create(
            text='Тестирование подписок',
            author=cls.author
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_user_follow_other_users(self):
        """Авторизованный user может подписываться на других users."""
        follows_old = list(Follow.objects.values_list('id', flat=True))
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author})
        )
        follow_new = Follow.objects.exclude(id__in=follows_old)
        self.assertEqual(len(follow_new), len(follows_old) + 1)

    def test_authorized_user_unfollow_other_users(self):
        """Авторизованный user может отписываться других users."""
        follow = Follow.objects.create(user=self.user, author=self.author)
        follows_old = list(Follow.objects.values_list('id', flat=True))
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author}
            )
        )
        follow_new = Follow.objects.exclude(id__in=follows_old)
        self.assertNotIn(follow, follow_new)
        self.assertEqual(len(follow_new), len(follows_old) - 1)

    def test_follower_new_post(self):
        """Новая запись пользователя появляется для подписчиков."""
        post = self.post
        Follow.objects.create(user=self.user, author=self.author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        post_count = response.context['page_obj'][0]
        self.assertEqual(post_count.id, post.id)

    def test_unfollower_new_post(self):
        """Новая запись не появляется для не подписчиков."""
        post = self.post
        response = self.authorized_client.get(reverse('posts:follow_index'))
        self.assertNotIn(post.id, response.context['page_obj'])
