from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from connects.models import *
from connects.serializers import *
from django.shortcuts import get_object_or_404, render, redirect

# ─────────────────────────────
#  HELPER FUNCTIONS
# ─────────────────────────────

def home(request):
    return render(request, 'home.html')

def login_view(request):
    return render(request, 'login.html')

def register_view(request):
    return render(request, 'register.html')

def profile(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'profile.html')

def settings(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return render(request, 'settings.html')

def is_super_admin(user):
    return user.is_authenticated and user.is_superuser

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'admin_profile') 

def is_moderator(user):
    return user.is_authenticated and hasattr(user, 'moderator_profile')


def is_regular_user(user):
    return user.is_authenticated and hasattr(user, 'regular_profile')


def is_guest(user):
    return user.is_authenticated and hasattr(user, 'guest_profile')


# ─────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────

class RegisterView(APIView):
    """
    POST /auth/register/
    Jei keo register korte parbe
    Default role: Regular User (RegularProfile create hobe)
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')

        # Basic validation
        if not username or not password:
            return Response(
                {"error": "Username ar password must lagbe."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Ei username already newa ache."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # User create
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Default role: Regular User
        from connects.models import RegularProfile
        RegularProfile.objects.create(user=user)

        return Response(
            {
                "message": "Registration successful.",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": "Regular User"
                }
            },
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    POST /auth/login/
    Jei keo login korte parbe
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {"error": "Username ar password must lagbe."},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {"error": "Username ba password thik nei."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        login(request, user)

        # Role determine korbe
        if is_super_admin(user):
            role = "Super Admin"
        elif is_admin(user):
            role = "Admin"    
        elif is_moderator(user):
            role = "Moderator"
        elif is_guest(user):
            role = "Guest"
        else:
            role = "Regular User"

        return Response(
            {
                "message": f"Login successful. Welcome {user.username}!",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": role
                }
            },
            status=status.HTTP_200_OK
        )


class LogoutView(APIView):
    """
    POST /auth/logout/
    Shudhu logged in user logout korte parbe
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────
#  USER VIEWS
# ─────────────────────────────

class UserListView(generics.ListAPIView):
    """
    GET /users/
    Shudhu Super Admin dekhte parbe
    Random order e user list ashbe
    """
    serializer_class = SimpleUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if not is_super_admin(self.request.user):
            raise PermissionDenied("Shudhu Super Admin user list dekhte parbe.")
        return User.objects.all().order_by('?')


class UserDetailView(generics.RetrieveAPIView):
    """
    GET /users/<id>/
    Super Admin: jekono user
    Others: shudhu nijer details
    """
    serializer_class = SimpleUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def get_object(self):
        user_obj = super().get_object()
        request_user = self.request.user

        if is_super_admin(request_user):
            return user_obj

        if request_user == user_obj:
            return user_obj

        raise PermissionDenied("Apni shudhu nijer details dekhte parben.")


class UserUpdateView(generics.UpdateAPIView):
    """
    PATCH /users/<id>/update/
    Super Admin: jekono user
    Others: shudhu nijer account
    """
    serializer_class = SimpleUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    http_method_names = ['patch']

    def perform_update(self, serializer):
        user = self.request.user
        target_user = self.get_object()

        if is_super_admin(user):
            serializer.save()
            return

        if user != target_user:
            raise PermissionDenied("Apni shudhu nijer account update korte parben.")

        serializer.save()


class UserDeleteView(generics.DestroyAPIView):
    """
    DELETE /users/<id>/delete/
    Shudhu Super Admin jekono user delete korte parbe
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        if not is_super_admin(self.request.user):
            raise PermissionDenied("Shudhu Super Admin user delete korte parbe.")
        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "User successfully delete hoyeche."},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────
#  POST VIEWS
# ─────────────────────────────

class PostListView(generics.ListAPIView):
    """
    GET /posts/
    Jei keo dekhte parbe (Guest o)
    Shudhu published posts ashbe
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Post.objects.filter(
            status__in=['published', 'draft']
        ).select_related('author')

class PostListHomeView(generics.ListAPIView):
    """
    GET /posts/home/
    Jei keo dekhte parbe (Guest o)
    Shudhu published posts ashbe
    """
    serializer_class = PostListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Post.objects.filter(
            status__in= ['published']
        ).select_related('author')


class PostDetailView(generics.RetrieveAPIView):
    """
    GET /posts/<id>/
    Jei keo dekhte parbe
    View count auto increment hobe
    """
    serializer_class = PostDetailSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Post.objects.all()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.increment_view()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class PostCreateView(generics.CreateAPIView):
    """
    POST /posts/create/
    Shudhu Regular User & Super Admin korte parbe
    Moderator & Guest parbe na
    """
    serializer_class = PostCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if is_guest(user):
            raise PermissionDenied("Guest user post create korte parbe na.")

        if is_moderator(user):
            raise PermissionDenied("Moderator post create korte parbe na.")

        serializer.save(author=user)


class PostUpdateView(generics.UpdateAPIView):
    """
    PATCH /posts/<id>/update/
    Super Admin : jekono post
    Regular User: shudhu nijer post
    Moderator   : parbe na
    Guest       : parbe na
    """
    serializer_class = PostCreateUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Post.objects.all()
    http_method_names = ['patch']

    def perform_update(self, serializer):
        user = self.request.user
        post = self.get_object()

        if is_guest(user):
            raise PermissionDenied("Guest post update korte parbe na.")
        
        if is_admin(user):
            raise PermissionDenied("Admin post update korte parbe na.")

        if is_moderator(user):
            serializer.save()
            return

        if is_super_admin(user):
            serializer.save()
            return

        # Regular user: shudhu nijer post
        if post.author != user:
            raise PermissionDenied("Apni shudhu nijer post update korte parben.")

        serializer.save()


class PostDeleteView(generics.DestroyAPIView):
    """
    DELETE /posts/<id>/delete/
    Super Admin : jekono post
    Moderator   : jekono post
    Regular User: shudhu nijer post
    Guest       : parbe na
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Post.objects.all()

    def perform_destroy(self, instance):
        user = self.request.user

        if is_guest(user):
            raise PermissionDenied("Guest post delete korte parbe na.")

        if is_super_admin(user) or is_moderator(user):
            instance.delete()
            return

        if instance.author != user:
            raise PermissionDenied("Apni shudhu nijer post delete korte parben.")

        instance.delete()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Post successfully delete hoyeche."},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────
#  COMMENT VIEWS
# ─────────────────────────────

class CommentListView(generics.ListAPIView):
    """
    GET /posts/<post_id>/comments/
    Jei keo dekhte parbe
    Shudhu top level comments ashbe (replies nested e thakbe)
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("Post pawa jae ni.")

        return Comment.objects.filter(
            post=post, parent=None
        ).select_related('author', 'post')


class CommentDetailView(generics.RetrieveAPIView):
    """
    GET /comments/<id>/
    Jei keo dekhte parbe
    """
    serializer_class = CommentSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Comment.objects.all()


class CommentCreateView(generics.CreateAPIView):
    """
    POST /posts/<post_id>/comments/create/
    Shudhu Regular User & Super Admin korte parbe
    Moderator & Guest parbe na
    """
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user

        if is_guest(user):
            raise PermissionDenied("Guest comment korte parbe na.")

        if is_moderator(user):
            raise PermissionDenied("Moderator comment create korte parbe na.")

        post_id = self.kwargs.get('post_id')

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            raise NotFound("Post pawa jae ni.")

        serializer.save(author=user, post=post)


class CommentUpdateView(generics.UpdateAPIView):
    """
    PATCH /comments/<id>/update/
    Super Admin : jekono comment
    Regular User: shudhu nijer comment
    Moderator   : parbe na
    Guest       : parbe na
    """
    serializer_class = CommentCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()
    http_method_names = ['patch']

    def perform_update(self, serializer):
        user = self.request.user
        comment = self.get_object()

        if is_guest(user):
            raise PermissionDenied("Guest comment update korte parbe na.")

        if is_moderator(user):
            raise PermissionDenied("Moderator comment update korte parbe na.")

        if is_super_admin(user):
            serializer.save()
            return

        # Regular user: shudhu nijer comment
        if comment.author != user:
            raise PermissionDenied("Apni shudhu nijer comment update korte parben.")

        serializer.save()


class CommentDeleteView(generics.DestroyAPIView):
    """
    DELETE /comments/<id>/delete/

    Super Admin  : jekono comment
    Moderator    : jekono comment
    Post Owner   : nijer post er jekono comment
    Comment Owner: shudhu nijer comment
    Guest        : parbe na
    """
    permission_classes = [permissions.IsAuthenticated]
    queryset = Comment.objects.all()

    def perform_destroy(self, instance):
        user = self.request.user

        if is_guest(user):
            raise PermissionDenied("Guest comment delete korte parbe na.")

        # Super Admin ba Moderator
        if is_super_admin(user) or is_moderator(user):
            instance.delete()
            return

        # Post owner tar post er jekono comment delete korte parbe
        if instance.post and instance.post.author == user:
            instance.delete()
            return

        # Comment owner nijer comment delete korte parbe
        if instance.author == user:
            instance.delete()
            return

        raise PermissionDenied("Apnar ei comment delete korar permission nei.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(
            {"message": "Comment successfully delete hoyeche."},
            status=status.HTTP_200_OK
        )