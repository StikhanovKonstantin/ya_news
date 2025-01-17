from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from news.models import News, Comment
from news.forms import CommentForm


User = get_user_model()



class TestHomePage(TestCase):
    """Тестирование контента на главной странице."""

    HOME_URL = reverse('news:home')

    @classmethod
    def setUpTestData(cls):
        """Устанавливает все нужные объекты перед запуском тестов."""
        today = datetime.today()
        News.objects.bulk_create(
            News(
                title=f"Новость {index}",
                text="Просто текст.",
                date=today - timedelta(days=index),
            )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        )

    def test_news_count(self):
        """Проверяет, что на главной странице отображается 10 новостей."""
        response = self.client.get(self.HOME_URL)
        news_list = response.context['news_list']
        news_count = news_list.count()
        self.assertEqual(news_count, settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_ordering(self):
        """Сортировка на главной странице, от новых к старым записям."""
        response = self.client.get(self.HOME_URL)
        object_list = response.context['object_list']
        all_dates = [news.date for news in object_list]
        sorted_dates = sorted(all_dates, reverse=True)
        self.assertEqual(all_dates, sorted_dates)


class TestDetailPage(TestCase):
    """Проверяет контент на странице новости."""

    @classmethod
    def setUpTestData(cls):
        """Устанавливает все нужные объекты перед началом тестирования."""
        cls.news = News.objects.create(title='Тестовая новость', text='Текст.')
        cls.detail_url = reverse('news:detail', args=(cls.news.id,))
        cls.author = User.objects.create(username='Комментатор')
        now = timezone.now()
        for index in range(10):
            comment = Comment.objects.create(
                news=cls.news,
                author=cls.author,
                text=f'Текст {index}',
            )
            comment.created = now + timedelta(days=index)
            comment.save()

    def test_comment_ordering(self):
        """
        Сортировка комментариев на странице отдельной новости,
        от старых к новым.
        """
        response = self.client.get(self.detail_url)
        self.assertIn('news', response.context)
        news = response.context['news']
        all_comments = news.comment_set.all()
        all_timestamps = [comment.created for comment in all_comments]
        sorted_timestamps = sorted(all_timestamps)
        self.assertEqual(all_timestamps, sorted_timestamps)

    def test_anonymous_client_has_no_form(self):
        """
        Проверяет, что на странице новости у неавторизованного
        пользователя нет формы для создания комментария.
        """
        response = self.client.get(self.detail_url)
        self.assertNotIn('form', response.context)

    def authorized_client_has_form(self):
        """
        Проверяет, что на странице новости у авторизованного
        пользователя есть форма для создания комментария.
        """
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], CommentForm)
