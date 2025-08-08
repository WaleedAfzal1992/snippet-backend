import os
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from email.mime.image import MIMEImage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from rest_framework import viewsets, status, mixins
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from .serializers import RegisterSerializers, LoginSerializers, BlogArticleSerializer, BlogContactUsSerializer, CourseSerializer, CartItemSerializer, PaymentSerializer
from .models import RegisterBlog, BlogArticle, BlogContactUs, Course, CartItem, PaymentVoucher
from rest_framework.decorators import api_view, action
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from django.db import IntegrityError
from datetime import datetime, timedelta
import hmac, hashlib


User = get_user_model()

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
            try:
                serializer.save()
                headers = {'Location': serializer.data.get('slug')}
                return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
            except IntegrityError:
                return Response({"error": "Slug already exists. Try a different title."},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'GET':
        articles = BlogArticle.objects.all()
        serializer = BlogArticleSerializer(articles, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_blog_article_by_id(request, slug):
    try:
        article = BlogArticle.objects.get(slug=slug)
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

    def put(self, request, slug):
        try:
            article = BlogArticle.objects.get(slug=slug)
            article.title = request.data.get('title', article.title)
            article.content = request.data.get('content', article.content)
            article.save()
            return Response({'message': 'Blog updated successfully'}, status=status.HTTP_200_OK)

        except BlogArticle.DoesNotExist:
            return Response({'error': 'Article not found'}, status=status.HTTP_404_NOT_FOUND)


class BlogArticleDetailView(APIView):
    permission_classes = [IsSuperUserOrStaff]  # Restricting to superusers or staff only

    def delete(self, request, slug):
        try:
            article = BlogArticle.objects.get(slug=slug)
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

            # Save the message to database
            serializer.save()

            try:
                # Send email to YOUR email address (admin email)
                send_mail(
                    f"New message from {name} ({email})",  # Subject
                    f"From: {name} <{email}>\n\n{message}",  # Message body
                    settings.DEFAULT_FROM_EMAIL,  # From email (your server email)
                    [settings.ADMIN_EMAIL],  # To email (YOUR email)
                    fail_silently=False,
                )

                # Optional: Send confirmation to the user
                send_mail(
                    "Thank you for contacting us",
                    f"Dear {name},\n\nWe have received your message and will get back to you soon.\n\nYour message:\n{message}",
                    settings.DEFAULT_FROM_EMAIL,
                    [email],  # Send to user's email
                    fail_silently=True,
                )

                return Response({'message': 'Your message has been sent successfully!'},
                                status=status.HTTP_200_OK)
            except Exception as e:
                return Response({'error': str(e)},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

class PasswordResetRequestView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        try:
            user = User.objects.get(Email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        reset_link = f"{request.data.get('frontend_base_url')}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Reset your password",
            message=f"Click here to reset your password: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.Email],
            fail_silently=False,
        )

        return Response({"message": "Password reset link sent!"})


class PasswordResetConfirmView(APIView):
    def post(self, request):
        uidb64 = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not uidb64 or not token or not new_password:
            return Response({"error": "Missing data"}, status=400)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (User.DoesNotExist, ValueError, TypeError):
            return Response({"error": "Invalid user ID"}, status=400)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired token"}, status=400)

        user.set_password(new_password)
        user.save()
        return Response({"message": "Password has been reset successfully!"})


class PaymentViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = PaymentSerializer
    queryset = PaymentVoucher.objects.all()
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        user = request.user  # Assuming the user is authenticated
        user_name = user.name
        print(user_name)


        # Email setup
        subject = "New Voucher Uploaded"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [settings.ADMIN_EMAIL]  # Replace with your admin/accountant email

        text_content = "A student has submitted a new payment voucher."
        html_content = f"""
                <p>A student {user_name} has submitted a new payment voucher.</p>
                <p><strong>Voucher Image:</strong></p>
                <img src="cid:voucher_image" alt="Voucher" style="max-width: 600px; border: 1px solid #ccc;" />
                """
        email = EmailMultiAlternatives(subject, text_content, from_email, to)
        email.attach_alternative(html_content, "text/html")

        # Attach image inline using CID
        if instance.voucher:
            with open(instance.voucher.path, 'rb') as img_file:
                image = MIMEImage(img_file.read())
                image.add_header('Content-ID', '<voucher_image>')
                image.add_header("Content-Disposition", "inline", filename=instance.voucher.name)
                email.attach(image)

        email.send(fail_silently=False)

        return Response(serializer.data, status=status.HTTP_201_CREATED)



class JazzCashPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Example: frontend sends course_id and quantity
        course_id = request.data.get("course_id")
        quantity = int(request.data.get("quantity", 1))

        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': 'Course does not exist'}, status=400)

        price = int(float(course.price)) * quantity  # Assuming course has price field

        # JazzCash configs (use from settings.py or environment)
        JAZZCASH_MERCHANT_ID = os.getenv('JAZZCASH_MERCHANT_ID')
        JAZZCASH_PASSWORD = os.getenv('JAZZCASH_PASSWORD')
        JAZZCASH_RETURN_URL = "http://127.0.0.1:3000/"
        JAZZCASH_INTEGRITY_SALT = os.getenv('JAZZCASH_INTEGRITY_SALT')

        current_datetime = datetime.now()
        pp_TxnDateTime = current_datetime.strftime('%Y%m%d%H%M%S')
        pp_TxnExpiryDateTime = (current_datetime + timedelta(hours=1)).strftime('%Y%m%d%H%M%S')
        pp_TxnRefNo = "T" + pp_TxnDateTime

        post_data = {
            "pp_Version": "1.0",
            "pp_TxnType": "MWALLET",
            "pp_Language": "EN",
            "pp_MerchantID": JAZZCASH_MERCHANT_ID,
            "pp_SubMerchantID": "",
            "pp_Password": JAZZCASH_PASSWORD,
            "pp_BankID": "TBANK",
            "pp_ProductID": "RETL",
            "pp_TxnRefNo": pp_TxnRefNo,
            "pp_Amount": str(price * 100),  # In Paisa
            "pp_TxnCurrency": "PKR",
            "pp_TxnDateTime": pp_TxnDateTime,
            "pp_BillReference": f"Bill{course_id}",
            "pp_Description": f"Payment for {course.title}",
            "pp_TxnExpiryDateTime": pp_TxnExpiryDateTime,
            "pp_ReturnURL": JAZZCASH_RETURN_URL,
            "pp_SecureHash": "",  # Will be filled later
            "ppmpf_1": str(request.user.id),
            "ppmpf_2": "CustomField2",
            "ppmpf_3": "CustomField3",
            "ppmpf_4": "CustomField4",
            "ppmpf_5": "CustomField5"
        }

        # Secure Hash generation
        sorted_string = "&".join(f"{k}={v}" for k, v in sorted(post_data.items()) if v != "")
        secure_hash = hmac.new(JAZZCASH_INTEGRITY_SALT.encode(), sorted_string.encode(), hashlib.sha256).hexdigest()
        post_data["pp_SecureHash"] = secure_hash

        return Response({
            "message": "Redirect to JazzCash",
            "post_data": post_data,
            "redirect_url": "https://sandbox.jazzcash.com.pk/CustomerPortal/transactionmanagement/merchantform/"
        })
