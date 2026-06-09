# admin.py

from django.contrib import admin
from .models import (
    AdminProfile, ModeratorProfile, RegularProfile, GuestProfile,
    Post, Comment
)


# ─────────────────────────────
#  PROFILE ADMINS
# ─────────────────────────────

@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username']


@admin.register(ModeratorProfile)
class ModeratorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username']


@admin.register(RegularProfile)
class RegularProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username']


@admin.register(GuestProfile)
class GuestProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['user__username']


# ─────────────────────────────
#  COMMENT INLINE (Post এর ভেতরে দেখানোর জন্য)
# ─────────────────────────────

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0                          # extra blank form দেখাবে না
    fields = ['author', 'content', 'parent']
    readonly_fields = ['created_at']


# ─────────────────────────────
#  POST ADMIN
# ─────────────────────────────

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'status', 'is_pinned', 'view_count', 'created_at']
    list_filter = ['status', 'is_pinned']
    search_fields = ['title', 'author__username']
    prepopulated_fields = {'slug': ('title',)}   # title লিখলে slug auto fill হবে
    readonly_fields = ['view_count', 'published_at', 'created_at', 'updated_at']
    inlines = [CommentInline]

    # Custom action — selected posts publish করা
    actions = ['make_published', 'make_archived']

    @admin.action(description='নির্বাচিত পোস্ট Published করো')
    def make_published(self, request, queryset):
        for post in queryset:
            post.publish()

    @admin.action(description='নির্বাচিত পোস্ট Archived করো')
    def make_archived(self, request, queryset):
        for post in queryset:
            post.archive()


# ─────────────────────────────
#  COMMENT ADMIN
# ─────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'post', 'parent', 'created_at']
    list_filter = ['created_at']
    search_fields = ['author__username', 'post__title', 'content']
    readonly_fields = ['created_at', 'updated_at']