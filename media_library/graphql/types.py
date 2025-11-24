import graphene
from graphene_django import DjangoObjectType
from django.utils.translation import gettext_lazy as _
from ..models import MediaCategory , MediaTag , MediaLibraryItem


class MediaCategoryType(DjangoObjectType) :
    is_user_defined = graphene.Boolean()
    can_delete = graphene.Boolean()
    media_items_count = graphene.Int()

    class Meta :
        model = MediaCategory
        fields = (
            'id' , 'name' , 'code' , 'description' , 'icon' ,
            'is_predefined' , 'is_active' , 'sorting_order' ,
            'created_at' , 'updated_at'
        )

    def resolve_is_user_defined(self , info) :
        return self.is_user_defined

    def resolve_can_delete(self , info) :
        return self.can_delete

    def resolve_media_items_count(self , info) :
        return self.media_items_count


class MediaTagType(DjangoObjectType) :
    media_items_count = graphene.Int()

    class Meta :
        model = MediaTag
        fields = ('id' , 'name' , 'is_active' , 'created_at' , 'updated_at')

    def resolve_media_items_count(self , info) :
        return self.media_items.count()


class MediaLibraryItemType(DjangoObjectType) :
    filename = graphene.String()
    file_extension = graphene.String()
    file_size_display = graphene.String()
    download_url = graphene.String()
    is_image = graphene.Boolean()
    is_video = graphene.Boolean()
    is_document = graphene.Boolean()

    class Meta :
        model = MediaLibraryItem
        fields = (
            'id' , 'title' , 'description' , 'media_file' , 'preview_file' ,
            'category' , 'tags' , 'mime_type' , 'is_active' , 'is_public' ,
            'created_by' , 'created_at' , 'updated_at'
        )

    def resolve_filename(self , info) :
        return self.filename

    def resolve_file_extension(self , info) :
        return self.file_extension

    def resolve_file_size_display(self , info) :
        return self.file_size_display

    def resolve_download_url(self , info) :
        return self.download_url

    def resolve_is_image(self , info) :
        return self.is_image()

    def resolve_is_video(self , info) :
        return self.is_video()

    def resolve_is_document(self , info) :
        return self.is_document()


# Input types for mutations
class MediaCategoryInput(graphene.InputObjectType) :
    name = graphene.String(required=True)
    code = graphene.String(required=True)
    description = graphene.String()
    icon = graphene.String()
    is_active = graphene.Boolean()
    sorting_order = graphene.Int()


class MediaTagInput(graphene.InputObjectType) :
    name = graphene.String(required=True)
    is_active = graphene.Boolean()


class MediaLibraryItemInput(graphene.InputObjectType) :
    title = graphene.String(required=True)
    description = graphene.String()
    category_id = graphene.ID(required=True)
    tags = graphene.List(graphene.ID)
    is_active = graphene.Boolean()
    is_public = graphene.Boolean()


class MediaFileUploadInput(graphene.InputObjectType) :
    title = graphene.String(required=True)
    description = graphene.String()
    category_id = graphene.ID(required=True)
    tags = graphene.List(graphene.ID)
    is_active = graphene.Boolean(default=True)
    is_public = graphene.Boolean(default=True)