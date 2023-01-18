import shutil
import tempfile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.models import Comment, Follow, Group, Post, User
from http import HTTPStatus
from django.conf import settings

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст, много текста',
            group=cls.group,
            author=cls.user,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_new_post_created(self):
        """при отправке валидной формы со страницы создания поста
        reverse('posts:create_post') создаётся новая запись в базе данных"""
        posts_count = Post.objects.count()
        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        uploaded = SimpleUploadedFile(
            name="small.gif", content=small_gif, content_type="image/gif"
        )
        form_data = {
            'text': 'Тестовый текст, много текста',
            'group': self.group.pk,
            'author': self.user,
            'image': uploaded,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.user,
                group=self.group.pk,
                image='posts/small.gif'
            ).exists()
        )

    def test_doing_post_edit(self):
        """при отправке валидной формы со страницы редактирования поста
        reverse('posts:post_edit', args=('post_id',))  происходит
        изменение поста с post_id в базе данных.."""
        form_data = {
            'text': self.post.text + 'Тестовый текст',
            'group': self.post.group.pk,
            'author': self.post.author,
        }

        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data, follow=True,
        )

        first_post = Post.objects.get(id=self.post.pk)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(form_data['text'], first_post.text)
        self.assertEqual(self.post.author, first_post.author)
        self.assertEqual(self.post.group, first_post.group)

    def test_non_auth_user_new_post(self):
        # неавторизоанный не может создавать посты
        form_data = {
            'text': 'Тестовый текст, много текста',
            'group': self.group.pk,
            'author': self.user,
        }
        self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='Тестовый текст').exists())


class CommentCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовое название',
            slug='test-slug',
            description='Тестовое описнаие группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.author,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_comment(self):
        """Создание коммента авторизованным пользователем."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentCreateFormTests.post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': CommentCreateFormTests.post.pk
                }
            )
        )
        lastcomment = Comment.objects.order_by('-id')[0]
        self.assertTrue(
            Comment.objects.filter(
                id=lastcomment.id,
                text=form_data['text'],
            ).exists()
        )

    def test_create_non_auth(self):
        """не авторизованный юзер не сможем оставить коммент."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый коммент',
        }
        response = self.client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': CommentCreateFormTests.post.id}
            ),
            data=form_data
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response,
            f'/auth/login/?next=/posts'
            f'/{CommentCreateFormTests.post.id}/comment/'
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)


class FollowCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='userposts')
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
        self.user_1 = User.objects.create_user(username='HasNoName1')
        self.authorized_client_not_author_1 = Client()
        self.authorized_client_not_author_1.force_login(self.user_1)
        self.user_2 = User.objects.create_user(username='HasNoName2')
        self.authorized_client_not_author_2 = Client()
        self.authorized_client_not_author_2.force_login(self.user_2)

    def test_follow(self):
        """проверка подписки."""
        follow_count = Follow.objects.count()
        form_data = {
            'username': self.author.username
        }
        response = self.authorized_client_not_author_1.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.author.username}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.author.username
                }
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                author=self.author,
                user=self.user_1
            ).exists()
        )

    def test_unfollow(self):
        """Проверка, отписки."""
        follow = Follow.objects.create(user=self.user_1, author=self.author)
        follow_count = Follow.objects.count()
        follow.delete()
        form_data = {
            'username': self.author.username
        }
        response = self.authorized_client_not_author_1.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.author.username}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={
                    'username': self.author.username
                }
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                author=self.author,
                user=self.user_1
            ).exists()
        )
