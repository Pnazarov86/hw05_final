import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    """Тестирование формы поста."""
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
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='test-slug_2',
            description='Тестовое описание_2',
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
        )

    def test_create_post(self):
        """Проверяем создание нового поста."""
        old_ids = list(Post.objects.values_list('id', flat=True))
        form_data = {
            'text': 'Тестирование формы',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_posts = Post.objects.exclude(id__in=old_ids)
        self.assertEqual(new_posts.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(new_posts[0].text, form_data['text'])
        self.assertEqual(new_posts[0].group.id, form_data['group'])
        self.assertEqual(new_posts[0].author, self.author)
        self.assertEqual(
            new_posts[0].image,
            'posts/' + form_data['image'].name
        )

    def test_post_edit(self):
        """Проверяем отредактированный пост."""
        form_data = {
            'text': 'Редактированный пост',
            'group': self.group_2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True,
        )
        edit_post = Post.objects.get(id=self.post.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(edit_post.text, form_data['text'])
        self.assertEqual(edit_post.group.id, form_data['group'])
        self.assertEqual(edit_post.author, self.author)


class CommentFormTests(TestCase):
    """Тестирование формы комментариев."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Nemo')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Здесь должно быть написано что-то очень интересное.',
            author=cls.author,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.post = Post.objects.create(
            text='Здесь должно быть написано что-то очень интересное.',
            author=self.author,
            group=self.group,
        )

    def test_create_comment(self):
        """Проверяем создание нового комментария."""
        old_ids = list(Comment.objects.values_list('id', flat=True))
        form_data = {'text': 'Тестовый комментарий'}
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        new_comment = Comment.objects.exclude(id__in=old_ids)
        self.assertEqual(new_comment.count(), 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(new_comment[0].text, form_data['text'])
        self.assertEqual(new_comment[0].author, self.author)
        self.assertEqual(new_comment[0].post, self.post)
