from django.contrib.auth import get_user_model
from django.test import TestCase


from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост, очень много текста',
        )
        cls.comment = Comment.objects.create(
            post=PostModelTest.post,
            author=PostModelTest.user,
            text='коммент',
        )
        cls.follow = Follow.objects.create(
            user=PostModelTest.user_2,
            author=PostModelTest.user,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name_post = post.text[:15]
        self.assertEqual(expected_object_name_post, str(post))
        group = PostModelTest.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))

    def test_comment_verbose_name(self):
        comment = self.comment
        field_verboses = {
            'post': 'Текст поста',
            'author': 'Автор',
            'text': 'Текст комментария',
            'created': 'Дата публикации',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = comment._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)

    def test_comment_help_text(self):
        comment = self.comment
        help_text = comment._meta.get_field('text').help_text
        self.assertEqual(help_text, 'Введите текст комментария')

    def test_follow_verbose_name(self):
        follow = self.follow
        field_verboses = {
            'user': 'Подписчик',
            'author': 'Автор',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                verbose_name = follow._meta.get_field(value).verbose_name
                self.assertEqual(verbose_name, expected)
