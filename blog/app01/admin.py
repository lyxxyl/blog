from django.contrib import admin
from app01.models import *
from django.utils.safestring import mark_safe
# Register your models here.

admin.site.register(Article)
admin.site.register(Article2Tag)
admin.site.register(ArticleDetail)
admin.site.register(ArticleUpDown)
admin.site.register(Blog)
admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Tag)
admin.site.register(UserInfo)
