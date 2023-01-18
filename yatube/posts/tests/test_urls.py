

from django.test import TestCase, Client
from django.urls import reverse
from http import HTTPStatus
from ..models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Группа поклонников графа',
            slug='tolstoi',
            description='Что-то о группе'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Война и мир изначально назывался «1805 год»',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username="HasNoName")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text="Тестовый текст",
            author=self.user
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): "posts/index.html",
            reverse(
                'posts:group_list',
                kwargs={'slug': PostURLTests.group.slug}
            ): "posts/group_list.html",
            reverse('posts:post_create'): "posts/create_post.html",
            reverse(
                'posts:profile',
                kwargs={'username': PostURLTests.user.username}
            ): "posts/profile.html",
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.pk}
            ): "posts/post_detail.html",

            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): "posts/create_post.html",
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_home_url_exists_at_desired_location(self):
        """Index / доступна любому пользователю."""
        response = self.guest_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_list_any_user(self):
        """список групп / доступна любому пользователю."""
        response = self.guest_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostURLTests.group.slug}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_any_user(self):
        """Профиль / доступна любому пользователю."""
        response = self.guest_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostURLTests.user.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_detail_any_user(self):
        """Детали поста / доступна любому пользователю."""
        response = self.guest_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostURLTests.post.pk}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_auth_user(self):
        """Создание постав / доступна авторизованному пользователю."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_auth_user(self):
        """Редактирование поста / доступна авторизованному пользователю."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_non_auth_user(self):
        """Создание постав / недоступно не ауф пользователю/переадресация."""
        response = self.guest_client.get(
            reverse('posts:post_create'),
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_non_auth_user(self):
        """Редкатирование поста / недоступно не ауф пользователю."""
        response = self.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page_any_user(self):
        """unexisting_page не найдена для любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
