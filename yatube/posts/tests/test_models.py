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

    def test_models(self):
        """Проверяем, что у моделей корректно работает __str__."""
        objects = {
            str(self.group): self.group.title,
            str(self.post): self.post.text[:TEXT_LIM]
        }
        for value, expected in objects.items():
            with self.subTest(value=value):
                self.assertEqual(value, expected)

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
