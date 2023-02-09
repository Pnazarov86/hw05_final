from django.test import TestCase

from ..constants import TEXT_LIM
from ..models import Group, Post, User


class PostModelTest(TestCase):
    """Тестирование моделей."""
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

    def test_models_group(self):
        """Проверяем, что у модели Group корректно работает __str__."""
        expected_object_name = self.group.title
        self.assertEqual(expected_object_name, str(self.group))

    def test_models_post(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        expected_object_name = self.post.text[:TEXT_LIM]
        self.assertEqual(expected_object_name, str(self.post))

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа'
        }
        for field, value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name, value
                )

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Выберите группу',
        }
        for field, value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text, value
                )
