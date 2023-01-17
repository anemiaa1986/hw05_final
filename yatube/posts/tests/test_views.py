import shutil
import tempfile
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from posts.models import Comment, Follow, Group, Post
from django.urls import reverse
from django.core.cache import cache
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="test-slug",
        )
        cls.group3 = Group.objects.create(
            title="Тестовая группа 3",
            slug="test-slug3",
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username="HasNoName")
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text="Тестовый текст",
            author=self.user,
            group=self.group,
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse("posts:index"): "posts/index.html",
            reverse(
                "posts:group_list",
                kwargs={"slug": f"{PostPagesTests.group.slug}"}
            ): "posts/group_list.html",
            reverse(
                "posts:profile", kwargs={"username": f"{self.user}"}
            ): "posts/profile.html",
            reverse(
                "posts:post_detail",
                kwargs={"post_id": f"{int(self.post.pk)}"},
            ): "posts/post_detail.html",
            reverse("posts:post_create"): "posts/create_post.html",
            reverse(
                "posts:post_edit", kwargs={"post_id": f"{int(self.post.pk)}"}
            ): "posts/create_post.html",
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с корректным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_group_0 = first_object.group
        post_author_0 = first_object.author
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_author_0, self.user)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с корректным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.group.slug, self.group.slug)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user})
        )
        post = response.context['posts'][0]
        self.assertEqual(post.author, self.user)

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        post_id = self.post.pk
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_id})
        )
        post_context = response.context['post']
        self.assertEqual(post_context.id, post_id)

    def test_create_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={"post_id": self.post.pk})
        )

        form = response.context['form'].initial['text']
        self.assertEqual(form, self.post.text)

    def test_post_with_group_on_pages(self):
        """Проверьте, что если при создании поста указать группу,
        то этот пост появляется на главной странице сайта,
        на странице выбранной группы, в профайле пользователя."""
        templates_pages_names = {
            reverse("posts:index"):
                'posts/index.html',
            reverse("posts:group_list", kwargs={"slug": self.group.slug}):
                'posts/group_list.html',
            reverse("posts:profile", kwargs={"username": self.user}):
                'posts/profile.html',
        }

        for reverse_name, _ in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertIn(
                    self.post, response.context['page_obj']
                )

    def test_post_did_not_fall_into_another_group(self):
        """Проверьте, что этот пост не попал в группу,
        для которой не был предназначен."""
        template_page = reverse(
            'posts:group_list', kwargs={'slug': self.group3.slug}
        )
        response = self.authorized_client.get(template_page)
        self.assertNotIn(
            self.post, response.context['page_obj']
        )


class PaginatorViewsTest(TestCase):
    # Здесь создаются фикстуры: клиент и 13 тестовых записей.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text="Тестовый текст, много текста",
            group=cls.group,
        )
        for x in range(1, 13):
            Post.objects.create(
                author=cls.user,
                text=f"Тестовый пагинатор {1+x}",
                group=cls.group,
            )

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10"""
        templates_pages_names = {
            reverse("posts:index"):
                'posts/index.html',
            reverse("posts:group_list", kwargs={"slug": self.group.slug}):
                'posts/group_list.html',
            reverse("posts:profile", kwargs={"username": self.user}):
                'posts/profile.html',
        }

        for reverse_name, _ in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertEqual(
                    len(response.context['page_obj']), 10
                )

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста"""
        templates_pages_names = {
            reverse("posts:index"):
                'posts/index.html',
            reverse("posts:group_list", kwargs={"slug": self.group.slug}):
                'posts/group_list.html',
            reverse("posts:profile", kwargs={"username": self.user}):
                'posts/profile.html',
        }

        for reverse_name, _ in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                page = 2
                response = self.authorized_client.get(
                    reverse_name,
                    {'page': page}
                )
                self.assertEqual(
                    len(response.context['page_obj']), 3
                )


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            author=cls.author,
            text='Тестовый коммент',
            post=cls.post
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_comment_view(self):
        """Шаблон post_detail показывает новый коммент."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{CommentViewsTest.post.pk}'}
            )
        )
        first_object = response.context.get('comments')[0]
        comment_post_0 = first_object
        self.assertEqual(comment_post_0, CommentViewsTest.comment)


class CacheViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_cach(self):
        """Проверяем кэш на главной."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        content_post = response.content
        Post.objects.filter(id=self.post.id).delete()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(content_post, response.content)
        cache.clear()
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertNotEqual(content_post, response.content)


class FollowViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.user1 = User.objects.create_user(username='HasNoName1')
        self.authorized_client_non_auth1 = Client()
        self.authorized_client_non_auth1.force_login(self.user1)
        self.user2 = User.objects.create_user(username='HasNoName2')
        self.authorized_client_non_auth2 = Client()
        self.authorized_client_non_auth2.force_login(self.user2)

    def test_follower_view(self):
        """Проверка новой записи у подписчика."""
        Follow.objects.create(user=self.user1, author=self.author)
        post_author = Post.objects.create(
            text='Тестовый текст новый',
            author=self.author,
            group=self.group
        )
        response = self.authorized_client_non_auth1.get(
            reverse('posts:follow_index')
        )
        first_object = response.context.get('page_obj').object_list[0]
        self.assertEqual(first_object, post_author)

    def test_not_follower_view(self):
        """Обратная  проверка, что не появится."""
        Follow.objects.create(user=self.user2, author=self.user1)
        Post.objects.create(
            text='Тестовый текст новый',
            author=self.user1,
            group=self.group
        )
        post_author = Post.objects.create(
            text='Тестовый текст самый новый',
            author=self.author,
            group=self.group
        )
        response = self.authorized_client_non_auth2.get(
            reverse('posts:follow_index')
        )
        first_object = response.context.get('page_obj').object_list[0]
        self.assertNotEqual(first_object, post_author)
