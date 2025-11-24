# Генерируем мутации
from datetime import datetime

from djangoProject1.common_models.graphql_utils import generate_create_mutations
import graphene
from .types import clientsModelsTypes, CompanyType, CompanyPersonType
from ..models import Company, CompanyPerson

#
# mutations = generate_create_mutations(clientsModelsTypes)
#
# class Mutation(graphene.ObjectType):
#     """Основной класс мутаций"""
#     pass
#
# # Добавляем все мутации динамически
# for mutation_name, mutation_class in mutations.items():
#     setattr(Mutation, mutation_name.lower(), mutation_class.Field())


class CreateCompany(graphene.Mutation):
    class Arguments:
        symbolic_code = graphene.String(required=True)
        company_name = graphene.String(required=True)

    company = graphene.Field(CompanyType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, symbolic_code, company_name):
        print("\n=== Начало выполнения мутации CreateCompany ===")
        print(f"Получены параметры: symbolic_code='{symbolic_code}', company_name='{company_name}'")

        try:
            print("Попытка создания компании в базе данных...")
            company = Company.objects.create(
                symbolic_code=symbolic_code,
                company_name=company_name
            )
            print(f"Успешно создана компания: ID={company.id}, symbolic_code='{company.symbolic_code}'")

            # Проверим, сохранилась ли запись в БД
            db_company = Company.objects.filter(id=company.id).first()
            if db_company:
                print("Запись успешно найдена в базе данных после создания")
            else:
                print("ОШИБКА: Запись не найдена в базе данных после создания!")

            return CreateCompany(
                company=company,
                success=True,
                errors=None
            )

        except Exception as e:
            print(f"ОШИБКА при создании компании: {str(e)}")
            return CreateCompany(
                company=None,
                success=False,
                errors=str(e)
            )
        finally:
            print("=== Завершение выполнения мутации ===\n")


class UpdateCompany(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        symbolic_code = graphene.String()
        company_name = graphene.String()

    # Изменяем выходные поля
    success = graphene.Boolean()
    errors = graphene.String()
    company = graphene.Field(CompanyType)

    def mutate(self, info, id, **kwargs):
        try:
            print("\n=== Начало выполнения мутации UpdateCompany ===")
            print(f"{datetime.now()}Получены параметры: id='{id}'")

            # Получаем компанию или возвращаем ошибку
            company = Company.objects.get(pk=id)

            # Обновляем поля
            for field, value in kwargs.items():
                if value is not None:  # Обновляем только переданные значения
                    setattr(company, field, value)
                    print(f'Для поля {field} установлено значение {value}')

            # Валидация перед сохранением
            company.full_clean()
            company.save()

            print("Успешное обновление компании")
            return UpdateCompany(
                success=True,
                errors=None,
                company=company
            )

        except Company.DoesNotExist:
            error_msg = f"Компания с id={id} не найдена"
            print(error_msg)


class CompanyMutation(graphene.Mutation):
    class Arguments:
        # Общие аргументы
        id = graphene.ID(required=False)
        symbolic_code = graphene.String(required=False)
        company_name = graphene.String(required=False)
        operation = graphene.String(required=True)  # 'create' или 'update'

    # Общие выходные поля
    company = graphene.Field(CompanyType)
    success = graphene.Boolean()
    errors = graphene.String()

    def mutate(self, info, operation, **kwargs):
        try:
            if operation == 'create':
                print("\n=== Начало выполнения мутации CreateCompany ===")
                symbolic_code = kwargs.get('symbolic_code')
                company_name = kwargs.get('company_name')

                if not symbolic_code or not company_name:
                    raise ValueError("Для создания компании необходимы symbolic_code и company_name")

                print(f"Получены параметры: symbolic_code='{symbolic_code}', company_name='{company_name}'")

                company = Company.objects.create(
                    symbolic_code=symbolic_code,
                    company_name=company_name
                )

                print(f"Успешно создана компания: ID={company.id}, symbolic_code='{company.symbolic_code}'")

                # Проверка сохранения в БД
                if not Company.objects.filter(id=company.id).exists():
                    raise Exception("Запись не найдена в базе данных после создания!")

                return CompanyMutation(
                    company=company,
                    success=True,
                    errors=None
                )

            elif operation == 'update':
                print("\n=== Начало выполнения мутации UpdateCompany ===")
                company_id = kwargs.get('id')

                if not company_id:
                    raise ValueError("Для обновления компании необходим id")

                print(f"{datetime.now()} Получены параметры: id='{company_id}'")

                company = Company.objects.get(pk=company_id)

                # Обновляем только переданные значения
                update_fields = {}
                for field, value in kwargs.items():
                    if field != 'id' and value is not None:
                        setattr(company, field, value)
                        update_fields[field] = value
                        print(f'Для поля {field} установлено значение {value}')

                if not update_fields:
                    raise ValueError("Не указаны поля для обновления")

                # Валидация перед сохранением
                company.full_clean()
                company.save()

                print("Успешное обновление компании")
                return CompanyMutation(
                    company=company,
                    success=True,
                    errors=None
                )

            else:
                raise ValueError(f"Неизвестная операция: {operation}")

        except Exception as e:
            error_msg = str(e)
            print(f"ОШИБКА: {error_msg}")
            return CompanyMutation(
                company=None,
                success=False,
                errors=error_msg
            )
        finally:
            print("=== Завершение выполнения мутации ===\n")



class CreateCompanyPerson(graphene.Mutation):
    class Arguments:
        symbolic_code = graphene.String(required=True)
        employee_company_id = graphene.ID(required=True)
        phone_number_office = graphene.String()
        phone_number_cell = graphene.String()
        person_email = graphene.String()

    company_person = graphene.Field(CompanyPersonType)

    def mutate(self, info, symbolic_code, employee_company_id, **kwargs):
        company_person = CompanyPerson(
            symbolic_code=symbolic_code,
            employee_company_id=employee_company_id,
            **kwargs
        )
        company_person.save()
        return CreateCompanyPerson(company_person=company_person)


class UpdateCompanyPerson(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        symbolic_code = graphene.String()
        employee_company_id = graphene.ID()
        phone_number_office = graphene.String()
        phone_number_cell = graphene.String()
        person_email = graphene.String()

    company_person = graphene.Field(CompanyPersonType)

    def mutate(self, info, id, **kwargs):
        company_person = CompanyPerson.objects.get(pk=id)
        for field, value in kwargs.items():
            setattr(company_person, field, value)
        company_person.save()
        return UpdateCompanyPerson(company_person=company_person)

# Регистрация мутации в схеме
class Mutation(graphene.ObjectType):
    company_create_company = CreateCompany.Field()
    company_update_company = UpdateCompany.Field()
    company_company_mutation = CompanyMutation.Field()
    company_create_company_person = CreateCompanyPerson.Field()
    company_update_company_person = UpdateCompanyPerson.Field()

# mutation {
#   createCompany(
#     symbolicCode: "ACME",
#     companyName: "ACME Corporation"
#   ) {
#     company {
#       id
#       symbolicCode
#       companyName
#     }
#   }
# }

# mutation {
#   updateCompanyPerson(
#     id: 1,
#     phoneNumberCell: "+79161234567",
#     personEmail: "ivanov@acme.com"
#   ) {
#     companyPerson {
#       id
#       symbolicCode
#       phoneNumberCell
#       personEmail
#     }
#   }
# }