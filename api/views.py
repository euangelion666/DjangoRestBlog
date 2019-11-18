from markdown2 import Markdown
from posts.models import Post
from django.utils import timezone
from rest_framework import status

from rest_framework.filters import SearchFilter
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView, 
    ListAPIView, 
    CreateAPIView,
    )
from api.serializers import (
    PostDetailSerializer, 
    PostListSerializer,
    PostCreateSerializer,
    )

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'list': reverse('api_v1:post-list', request=request, format=format),
        'create': reverse('api_v1:post-create', request=request, format=format)
    })

class PostCreateViewSet(CreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostCreateSerializer
    def post(self, request, *args, **kwargs):
        custom_data = request.data
        markdowner = Markdown()
        custom_data['content'] =  markdowner.convert(custom_data['content'])

        serializer = PostCreateSerializer(data=custom_data)
        if serializer.is_valid():
            serializer.save()
            return super(PostCreateViewSet, self).create(request, args, kwargs)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

class PostListViewSet(ListAPIView):
    queryset = Post.objects.all().order_by('-publish_date')
    serializer_class = PostListSerializer
    permission_classes = [AllowAny]
    filter_backends = [SearchFilter]
    search_fields = ['title', 'content']

class PostDetailViewSet(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer
    # permission_classes = [IsAuthenticatedOrReadOnly]
    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        new_obj = request.data
        if (obj.content is not new_obj['content']) or (obj.title is not new_obj['title']):
            obj.modified_date = timezone.now()
            obj.save()
        return super(PostDetailViewSet, self).update(request, args, kwargs)


    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.viewed_times += 1
        instance.save()
        return Response(PostDetailSerializer(instance).data)

