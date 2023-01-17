from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from ..models import Group, Post
from django.urls import reverse

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
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
                kwargs={'username': self.user}
            ): "posts/profile.html",
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
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
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_group_list_any_user(self):
        """список групп / доступна любому пользователю."""
        response = self.guest_client.get(f"/group/{PostURLTests.group.slug}/")
        self.assertEqual(response.status_code, 200)

    def test_profile_any_user(self):
        """Профиль / доступна любому пользователю."""
        response = self.guest_client.get(f"/profile/{self.user}/")
        self.assertEqual(response.status_code, 200)

    def test_post_detail_any_user(self):
        """Детали поста / доступна любому пользователю."""
        response = self.guest_client.get(f"/posts/{int(self.post.pk)}/")
        self.assertEqual(response.status_code, 200)

    def test_post_create_auth_user(self):
        """Создание постав / доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, 200)

    def test_post_edit_auth_user(self):
        """Редактирование поста / доступна авторизованному пользователю."""
        response = self.authorized_client.get(f"/posts/{int(self.post.pk)}/")
        self.assertEqual(response.status_code, 200)

    def test_post_create_non_auth_user(self):
        """Создание постав / недоступно не ауф пользователю/переадресация."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_non_auth_user(self):
        """Редкатирование поста / недоступно не ауф пользователю."""
        response = self.guest_client.get(f"/posts/{int(self.post.pk)}/")
        self.assertEqual(response.status_code, 200)

    def test_unexisting_page_any_user(self):
        """Index / доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, 404)
