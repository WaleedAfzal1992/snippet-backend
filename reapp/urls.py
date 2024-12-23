from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import BlogArticleDetailView, UpdateBlogArticleView, RegistrationViewSet, LoginViewSet, ContactUsViewSet

router = DefaultRouter()
router.register(r'register', RegistrationViewSet, basename='api-register')
router.register(r'login', LoginViewSet, basename='api-login')
router.register(r'contact', ContactUsViewSet, basename='api-contact')

urlpatterns = [
    path('', include(router.urls)),
    path('articles/', views.create_blog_article, name='create_blog_article'),
    path('articles/<int:id>/update/', UpdateBlogArticleView.as_view(), name='UpdateBlogArticleView'),
    path('articles/<int:id>/', views.get_blog_article_by_id, name='get_blog_article_by_id'),  # This is for GET
    path('articles/<int:id>/delete/', BlogArticleDetailView.as_view(), name='delete_blog_article'),  # This is for DELETE
    path('api-auth/', include('rest_framework.urls')),
]
