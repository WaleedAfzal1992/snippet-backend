from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .serializers import RegisterSerializers, LoginSerializers, BlogArticleSerializer, BlogContactUsSerializer, CourseSerializer, CartItemSerializer
from .models import RegisterBlog, BlogArticle, BlogContactUs, Course, CartItem
from rest_framework.decorators import api_view, action
from rest_framework.permissions import BasePermission, IsAuthenticatedOrReadOnly
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


class RegistrationViewSet(viewsets.ModelViewSet):
    queryset = RegisterBlog.objects.all()
    serializer_class = RegisterSerializers

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Registration successful'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginViewSet(viewsets.ViewSet):
    serializer_class = LoginSerializers

    def create(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                # Retrieve user based on username
                user = RegisterBlog.objects.get(name=username)

                # Check if password is correct
                if check_password(password, user.password):
                    # Generate JWT token for the user
                    refresh = RefreshToken.for_user(user)
                    access_token = refresh.access_token

                    # Prepare user information to return in the response
                    user_info = {
                        'is_superuser': user.is_superuser,
                        'is_staff': user.is_staff,
                        'is_active': user.is_active
                    }

                    # Return success message with JWT token and user info
                    return Response({
                        'message': 'Login successful',
                        'access_token': str(access_token),
                        'user_info': user_info
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Invalid password'}, status=status.HTTP_400_BAD_REQUEST)
            except RegisterBlog.DoesNotExist:
                return Response({'error': 'Username does not exist'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST'])
def create_blog_article(request):
    if request.method == 'POST':
        serializer = BlogArticleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        articles = BlogArticle.objects.all()
        serializer = BlogArticleSerializer(articles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_blog_article_by_id(request, id):
    try:
        article = BlogArticle.objects.get(id=id)
        serializer = BlogArticleSerializer(article)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except BlogArticle.DoesNotExist:
        return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)


class IsSuperUserOrStaff(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_superuser or request.user.is_staff)


# In your view
class UpdateBlogArticleView(APIView):
    permission_classes = [IsSuperUserOrStaff]
    authentication_classes = [JWTAuthentication]

    def put(self, request, id):
        try:
            article = BlogArticle.objects.get(id=id)
            article.title = request.data.get('title', article.title)
            article.content = request.data.get('content', article.content)
            article.save()
            return Response({'message': 'Blog updated successfully'}, status=status.HTTP_200_OK)

        except BlogArticle.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)


class BlogArticleDetailView(APIView):
    permission_classes = [IsSuperUserOrStaff]  # Restricting to superusers or staff only

    def delete(self, request, id):
        try:
            article = BlogArticle.objects.get(id=id)
            article.delete()
            return Response({"message": "Blog deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except BlogArticle.DoesNotExist:
            return Response({"error": "Blog not found"}, status=status.HTTP_404_NOT_FOUND)


class ContactUsViewSet(viewsets.ModelViewSet):
    queryset = BlogContactUs.objects.all()
    serializer_class = BlogContactUsSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data['name']
            email = serializer.validated_data['email']
            message = serializer.validated_data['message']

            try:
                send_mail(
                    f"Message from {name}",
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                return Response({'message': 'Your message has been sent successfully!'}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    lookup_field = 'slug'


class CartItemViewSet(viewsets.ModelViewSet):
    serializer_class = CartItemSerializer
    queryset = CartItem.objects.all()

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return CartItem.objects.filter(user=self.request.user).select_related('course')
        if not self.request.session.session_key:
            self.request.session.create()
        return CartItem.objects.filter(session_key=self.request.session.session_key).select_related('course')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        course_id = request.data.get('course_id')
        quantity = int(request.data.get('quantity', 1))

        try:
            course = Course.objects.get(pk=course_id)

            if request.user.is_authenticated:
                cart_item, created = CartItem.objects.get_or_create(
                    user=request.user,
                    course=course,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
            else:
                if not request.session.session_key:
                    request.session.create()
                cart_item, created = CartItem.objects.get_or_create(
                    session_key=request.session.session_key,
                    course=course,
                    defaults={'quantity': quantity}
                )
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()

            # Return the created/updated cart item
            serializer = self.get_serializer(cart_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Course.DoesNotExist:
            return Response(
                {"error": "Course does not exist"},
                status=status.HTTP_400_BAD_REQUEST
            )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)

        courses = Course.objects.all()
        course_serializer = CourseSerializer(courses, many=True)

        return Response({
            'cart_items': serializer.data,
            'available_courses': course_serializer.data
        })
