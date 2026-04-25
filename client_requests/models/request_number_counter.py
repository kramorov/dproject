# client_requests/models/request_number_counter.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.db.models import F


class RequestNumberCounter(models.Model):
    """
    Нумератор для запросов
    При получении номера для пользователя - увеличивается и счетчик компании
    """
    # Компания
    project_customer = models.ForeignKey(
        'project_customers.ProjectCustomer',
        on_delete=models.CASCADE,
        related_name='request_counter',
        verbose_name=_("Компания")
    )

    # Счетчик компании (сквозной для всех пользователей компании)
    project_customer_request_number = models.IntegerField(
        default=0,
        verbose_name=_("Счетчик запросов компании")
    )

    # Пользователь
    project_customer_user = models.ForeignKey(
        'project_customers.ProjectCustomerUser',
        on_delete=models.CASCADE,
        related_name='request_counter',
        verbose_name=_("Пользователь")
    )

    # Счетчик пользователя
    project_customer_user_request_number = models.IntegerField(
        default=0,
        verbose_name=_("Счетчик запросов пользователя в компании")
    )

    class Meta:
        verbose_name = _("Нумератор запросов")
        verbose_name_plural = _("Нумераторы запросов")
        unique_together = [['project_customer', 'project_customer_user']]

    def __str__(self):
        return f"{self.project_customer.name} / {self.project_customer_user.get_full_name()}: компания={self.project_customer_request_number}, пользователь={self.project_customer_user_request_number}"

    @classmethod
    def get_next_numbers(cls , project_customer , project_customer_user) :
        """
        Получить следующие номера для компании и пользователя
        Возвращает (company_number, user_number)
        """
        print("\n" + "=" * 60)
        print("=== get_next_numbers called ===")
        print(f"  project_customer: {project_customer}")
        print(f"  project_customer_user: {project_customer_user}")

        # Проверяем обязательные параметры
        if not project_customer :
            print("  ❌ ERROR: project_customer is None!")
            return None , None

        if not project_customer_user :
            print("  ❌ ERROR: project_customer_user is None!")
            return None , None

        print(f"  ✅ Оба параметра есть")

        # Получаем или создаем счетчик
        counter , created = cls.objects.get_or_create(
            project_customer=project_customer ,
            project_customer_user=project_customer_user
        )

        if created :
            print(f"  🆕 Создан новый нумератор (id={counter.id})")
        else :
            print(f"  📌 Найден существующий нумератор (id={counter.id})")

        print(
            f"  📊 Текущие значения: company={counter.project_customer_request_number}, user={counter.project_customer_user_request_number}")

        # Увеличиваем оба счетчика
        from django.db.models import F
        counter.project_customer_request_number = F('project_customer_request_number') + 1
        counter.project_customer_user_request_number = F('project_customer_user_request_number') + 1
        counter.save()
        counter.refresh_from_db()

        print(
            f"  📈 Новые значения: company={counter.project_customer_request_number}, user={counter.project_customer_user_request_number}")
        print("=" * 60 + "\n")

        return counter.project_customer_request_number , counter.project_customer_user_request_number