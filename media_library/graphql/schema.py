import graphene
from .queries import MediaLibraryQuery
from .mutations import MediaLibraryMutations

mediaLibrarySchema = graphene.Schema(query=MediaLibraryQuery, mutation=MediaLibraryMutations)