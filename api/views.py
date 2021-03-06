from posts.models import Post
from comments.models import Comment
from deleteList.models import (DeleteTransaction, DeleteArray)
from django.utils import timezone
from django.db.models import Count
from django.shortcuts import get_object_or_404

from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.filters import (
    SearchFilter, 
    OrderingFilter
    )
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.generics import (
    RetrieveUpdateDestroyAPIView,
    UpdateAPIView,
    DestroyAPIView,
    ListAPIView,
    CreateAPIView,
    GenericAPIView,
    )
from api.serializers import (
    PostDetailSerializer,
    PostListSerializer,
    PostCreateSerializer,
    PostDashboardListSerializer,
    CommentListSerializer,
    CommentSerializer,
    DeleteTransactionSerializer,
    )
from .globalFunc import markdown2Abstract

@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        'list': reverse('api_v1:post-list', request=request, format=format),
        'create': reverse('api_v1:post-create', request=request, format=format)
    })

class CommentBlogListViewSet(ListAPIView):
    serializer_class = CommentListSerializer
    def get_queryset(self):
        blog_id = self.kwargs['blog']
        queryset = Comment.objects.filter(blog_id=blog_id, parent=None)
        return queryset.order_by('-publish_date')

class CommentDeleteViewSet(DestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class CommentCreateViewSet(CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

class PostDashboardListViewSet(ListAPIView):
    queryset = Post.objects.all().annotate(comments_num=Count('comment')).order_by(*['-sticky', '-modified_date'])
    serializer_class = PostDashboardListSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['title', 'content']
    ordering_fields = ['title', 'viewed_times', 'publish_date', 'modified_date', 'sticky', 'comments_num']

class PostCreateViewSet(CreateAPIView):
    serializer_class = PostCreateSerializer

class PostListViewSet(ListAPIView):
    queryset = Post.objects.all().order_by(*['-sticky', '-modified_date'])
    serializer_class = PostListSerializer
    filter_backends = [SearchFilter]
    search_fields = ['title', 'content']

class PostDetailViewSet(RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostDetailSerializer

    def put(self, request, *args, **kwargs):
        obj = self.get_object()
        new_obj = request.data
        if (obj.content is not new_obj['content']) or (obj.title is not new_obj['title']):
            obj.modified_date = timezone.now()
            if (obj.content is not new_obj['content']):
                obj.abstract = markdown2Abstract(new_obj['content'])
            obj.save()
        return super(PostDetailViewSet, self).update(request, args, kwargs)


    def get(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.viewed_times += 1
        instance.save()
        return Response(PostDetailSerializer(instance, context={'request':request}).data)

class DeleteTransactionCreateViewSet(CreateAPIView):
    serializer_class = DeleteTransactionSerializer 

class DeleteTransactionExecuteViewSet(GenericAPIView):
    def get_queryset(self):
        transaction_id = self.kwargs['transaction']
        return DeleteArray.objects.filter(transaction_id=transaction_id)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        for item in queryset:
            item.blog.delete()
        
        get_object_or_404(DeleteTransaction, pk=self.kwargs['transaction']).delete()
        return Response(status=status.HTTP_202_ACCEPTED)

class StickyPostViewSet(UpdateAPIView):
    def update(self, request, *args, **kwargs):
        obj = get_object_or_404(Post, pk=kwargs['pk'])
        obj.sticky = request.data['sticky']
        obj.save()
        return Response(status=status.HTTP_200_OK)