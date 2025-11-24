import graphene
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q
from ..models import MediaCategory , MediaTag , MediaLibraryItem
from .types import MediaCategoryType , MediaTagType , MediaLibraryItemType


class MediaLibraryQuery(graphene.ObjectType) :
    # MediaCategory queries
    media_categories = graphene.List(
        MediaCategoryType ,
        id=graphene.ID() ,
        code=graphene.String() ,
        is_predefined=graphene.Boolean() ,
        is_active=graphene.Boolean() ,
        search=graphene.String()
    )

    media_category = graphene.Field(
        MediaCategoryType ,
        id=graphene.ID(required=True)
    )

    # MediaTag queries
    media_tags = graphene.List(
        MediaTagType ,
        id=graphene.ID() ,
        name=graphene.String() ,
        is_active=graphene.Boolean() ,
        search=graphene.String()
    )

    media_tag = graphene.Field(
        MediaTagType ,
        id=graphene.ID(required=True)
    )

    # MediaLibraryItem queries
    media_library_items = graphene.List(
        MediaLibraryItemType ,
        id=graphene.ID() ,
        title=graphene.String() ,
        category_id=graphene.ID() ,
        tag_id=graphene.ID() ,
        is_active=graphene.Boolean() ,
        is_public=graphene.Boolean() ,
        is_image=graphene.Boolean() ,
        search=graphene.String()
    )

    media_library_item = graphene.Field(
        MediaLibraryItemType ,
        id=graphene.ID(required=True)
    )

    # Resolvers for MediaCategory
    def resolve_media_categories(self , info , **kwargs) :
        queryset = MediaCategory.objects.all()

        if kwargs.get('id') :
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('code') :
            queryset = queryset.filter(code__icontains=kwargs['code'])
        if kwargs.get('is_predefined') is not None :
            queryset = queryset.filter(is_predefined=kwargs['is_predefined'])
        if kwargs.get('is_active') is not None :
            queryset = queryset.filter(is_active=kwargs['is_active'])
        if kwargs.get('search') :
            queryset = queryset.filter(
                Q(name__icontains=kwargs['search']) |
                Q(code__icontains=kwargs['search']) |
                Q(description__icontains=kwargs['search'])
            )

        return queryset.order_by('sorting_order' , 'name')

    def resolve_media_category(self , info , id) :
        try :
            return MediaCategory.objects.get(id=id)
        except MediaCategory.DoesNotExist :
            return None

    # Resolvers for MediaTag
    def resolve_media_tags(self , info , **kwargs) :
        queryset = MediaTag.objects.all()

        if kwargs.get('id') :
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('name') :
            queryset = queryset.filter(name__icontains=kwargs['name'])
        if kwargs.get('is_active') is not None :
            queryset = queryset.filter(is_active=kwargs['is_active'])
        if kwargs.get('search') :
            queryset = queryset.filter(name__icontains=kwargs['search'])

        return queryset.order_by('name')

    def resolve_media_tag(self , info , id) :
        try :
            return MediaTag.objects.get(id=id)
        except MediaTag.DoesNotExist :
            return None

    # Resolvers for MediaLibraryItem
    def resolve_media_library_items(self , info , **kwargs) :
        queryset = MediaLibraryItem.objects.select_related(
            'category' , 'created_by'
        ).prefetch_related('tags')

        if kwargs.get('id') :
            queryset = queryset.filter(id=kwargs['id'])
        if kwargs.get('title') :
            queryset = queryset.filter(title__icontains=kwargs['title'])
        if kwargs.get('category_id') :
            queryset = queryset.filter(category_id=kwargs['category_id'])
        if kwargs.get('tag_id') :
            queryset = queryset.filter(tags__id=kwargs['tag_id'])
        if kwargs.get('is_active') is not None :
            queryset = queryset.filter(is_active=kwargs['is_active'])
        if kwargs.get('is_public') is not None :
            queryset = queryset.filter(is_public=kwargs['is_public'])
        if kwargs.get('is_image') is not None :
            if kwargs['is_image'] :
                # Фильтр для изображений
                image_extensions = ['jpg' , 'jpeg' , 'png' , 'gif' , 'bmp' , 'webp' , 'svg']
                queryset = queryset.filter(
                    Q(media_file__endswith='.jpg') |
                    Q(media_file__endswith='.jpeg') |
                    Q(media_file__endswith='.png') |
                    Q(media_file__endswith='.gif') |
                    Q(media_file__endswith='.bmp') |
                    Q(media_file__endswith='.webp') |
                    Q(media_file__endswith='.svg')
                )
        if kwargs.get('search') :
            queryset = queryset.filter(
                Q(title__icontains=kwargs['search']) |
                Q(description__icontains=kwargs['search']) |
                Q(category__name__icontains=kwargs['search']) |
                Q(tags__name__icontains=kwargs['search'])
            ).distinct()

        return queryset.order_by('-created_at')

    def resolve_media_library_item(self , info , id) :
        try :
            return MediaLibraryItem.objects.select_related(
                'category' , 'created_by'
            ).prefetch_related('tags').get(id=id)
        except MediaLibraryItem.DoesNotExist :
            return None