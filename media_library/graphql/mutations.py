import graphene
from graphql import GraphQLError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from graphene_file_upload.scalars import Upload

from ..models import MediaCategory ,  MediaLibraryItem
from .types import MediaCategoryType ,  MediaLibraryItemType
from .types import MediaCategoryInput , MediaTagInput , MediaLibraryItemInput , MediaFileUploadInput

User = get_user_model()


class CreateMediaCategory(graphene.Mutation) :
    class Arguments :
        input = MediaCategoryInput(required=True)

    media_category = graphene.Field(MediaCategoryType)

    @classmethod
    def mutate(cls , root , info , input) :
        if not info.context.user.has_perm('media_library.add_mediacategory') :
            raise GraphQLError(_("У вас нет прав для создания категорий"))

        try :
            media_category = MediaCategory(
                name=input.name ,
                code=input.code ,
                description=input.description or '' ,
                icon=input.icon or '📁' ,
                is_active=input.is_active if input.is_active is not None else True ,
                sorting_order=input.sorting_order or 0
            )
            media_category.full_clean()
            media_category.save()
            return CreateMediaCategory(media_category=media_category)
        except ValidationError as e :
            raise GraphQLError(str(e))


class UpdateMediaCategory(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True)
        input = MediaCategoryInput(required=True)

    media_category = graphene.Field(MediaCategoryType)

    @classmethod
    def mutate(cls , root , info , id , input) :
        if not info.context.user.has_perm('media_library.change_mediacategory') :
            raise GraphQLError(_("У вас нет прав для изменения категорий"))

        try :
            media_category = MediaCategory.objects.get(id=id)

            # Запрещаем изменение кода предопределенных категорий
            if media_category.is_predefined and input.code != media_category.code :
                raise GraphQLError(_("Нельзя изменять код предопределенной категории"))

            media_category.name = input.name
            if not media_category.is_predefined :
                media_category.code = input.code
            media_category.description = input.description or media_category.description
            media_category.icon = input.icon or media_category.icon
            media_category.is_active = input.is_active if input.is_active is not None else media_category.is_active
            media_category.sorting_order = input.sorting_order or media_category.sorting_order

            media_category.full_clean()
            media_category.save()
            return UpdateMediaCategory(media_category=media_category)
        except MediaCategory.DoesNotExist :
            raise GraphQLError(_("Категория не найдена"))
        except ValidationError as e :
            raise GraphQLError(str(e))


class DeleteMediaCategory(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls , root , info , id) :
        if not info.context.user.has_perm('media_library.delete_mediacategory') :
            raise GraphQLError(_("У вас нет прав для удаления категорий"))

        try :
            media_category = MediaCategory.objects.get(id=id)

            if not media_category.can_delete :
                raise GraphQLError(_("Нельзя удалить эту категорию"))

            media_category.delete()
            return DeleteMediaCategory(success=True)
        except MediaCategory.DoesNotExist :
            raise GraphQLError(_("Категория не найдена"))

class UploadMediaFile(graphene.Mutation) :
    class Arguments :
        file = Upload(required=True)  # ← Используйте Upload вместо graphene.Upload
        input = MediaFileUploadInput(required=True)

    media_item = graphene.Field(MediaLibraryItemType)

    @classmethod
    def mutate(cls , root , info , file , input) :
        if not info.context.user.has_perm('media_library.add_medialibraryitem') :
            raise GraphQLError(_("У вас нет прав для загрузки файлов"))

        try :
            # Создаем объект медиа
            media_item = MediaLibraryItem(
                title=input.title ,
                description=input.description or '' ,
                category_id=input.category_id ,
                is_active=input.is_active ,
                is_public=input.is_public ,
                created_by=info.context.user
            )

            # Сохраняем файл
            media_item.media_file = file

            # Сохраняем объект (автоматически определится MIME-тип и создастся превью)
            media_item.save()

            # Добавляем теги если указаны
            if input.tags :
                media_item.tags.set(input.tags)

            return UploadMediaFile(media_item=media_item)
        except Exception as e :
            raise GraphQLError(f"Ошибка при загрузке файла: {str(e)}")


class UpdateMediaLibraryItem(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True)
        input = MediaLibraryItemInput(required=True)

    media_item = graphene.Field(MediaLibraryItemType)

    @classmethod
    def mutate(cls , root , info , id , input) :
        if not info.context.user.has_perm('media_library.change_medialibraryitem') :
            raise GraphQLError(_("У вас нет прав для изменения медиафайлов"))

        try :
            media_item = MediaLibraryItem.objects.get(id=id)

            # Проверяем права на объект (только создатель или админ может редактировать)
            if (media_item.created_by != info.context.user and
                    not info.context.user.has_perm('media_library.change_any_medialibraryitem')) :
                raise GraphQLError(_("Вы можете редактировать только свои файлы"))

            media_item.title = input.title
            media_item.description = input.description or media_item.description
            media_item.category_id = input.category_id
            media_item.is_active = input.is_active if input.is_active is not None else media_item.is_active
            media_item.is_public = input.is_public if input.is_public is not None else media_item.is_public

            media_item.save()

            # Обновляем теги если указаны
            if input.tags is not None :
                media_item.tags.set(input.tags)

            return UpdateMediaLibraryItem(media_item=media_item)
        except MediaLibraryItem.DoesNotExist :
            raise GraphQLError(_("Медиафайл не найден"))


class ReplaceMediaFile(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True)
        file = Upload(required=True)
        create_preview = graphene.Boolean(default_value=True)

    media_item = graphene.Field(MediaLibraryItemType)

    @classmethod
    def mutate(cls , root , info , id , file , create_preview) :
        if not info.context.user.has_perm('media_library.change_medialibraryitem') :
            raise GraphQLError(_("У вас нет прав для замены файлов"))

        try :
            media_item = MediaLibraryItem.objects.get(id=id)

            # Проверяем права на объект
            if (media_item.created_by != info.context.user and
                    not info.context.user.has_perm('media_library.change_any_medialibraryitem')) :
                raise GraphQLError(_("Вы можете заменять только свои файлы"))

            # Заменяем файл
            success = media_item.replace_file(file , create_preview=create_preview)
            if not success :
                raise GraphQLError(_("Ошибка при замене файла"))

            return ReplaceMediaFile(media_item=media_item)
        except MediaLibraryItem.DoesNotExist :
            raise GraphQLError(_("Медиафайл не найден"))


class RecreatePreview(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True)

    media_item = graphene.Field(MediaLibraryItemType)
    success = graphene.Boolean()
    message = graphene.String()

    @classmethod
    def mutate(cls , root , info , id) :
        if not info.context.user.has_perm('media_library.change_medialibraryitem') :
            raise GraphQLError(_("У вас нет прав для управления превью"))

        try :
            media_item = MediaLibraryItem.objects.get(id=id)

            if not media_item.is_image() :
                raise GraphQLError(_("Превью можно создавать только для изображений"))

            success , message = media_item.recreate_preview()
            return RecreatePreview(
                media_item=media_item ,
                success=success ,
                message=message
            )
        except MediaLibraryItem.DoesNotExist :
            raise GraphQLError(_("Медиафайл не найден"))


class DeleteMediaLibraryItem(graphene.Mutation) :
    class Arguments :
        id = graphene.ID(required=True)

    success = graphene.Boolean()

    @classmethod
    def mutate(cls , root , info , id) :
        if not info.context.user.has_perm('media_library.delete_medialibraryitem') :
            raise GraphQLError(_("У вас нет прав для удаления медиафайлов"))

        try :
            media_item = MediaLibraryItem.objects.get(id=id)

            # Проверяем права на объект
            if (media_item.created_by != info.context.user and
                    not info.context.user.has_perm('media_library.delete_any_medialibraryitem')) :
                raise GraphQLError(_("Вы можете удалять только свои файлы"))

            media_item.delete()
            return DeleteMediaLibraryItem(success=True)
        except MediaLibraryItem.DoesNotExist :
            raise GraphQLError(_("Медиафайл не найден"))


class MediaLibraryMutations(graphene.ObjectType) :
    create_media_category = CreateMediaCategory.Field()
    update_media_category = UpdateMediaCategory.Field()
    delete_media_category = DeleteMediaCategory.Field()

    upload_media_file = UploadMediaFile.Field()
    update_media_library_item = UpdateMediaLibraryItem.Field()
    replace_media_file = ReplaceMediaFile.Field()
    recreate_preview = RecreatePreview.Field()
    delete_media_library_item = DeleteMediaLibraryItem.Field()