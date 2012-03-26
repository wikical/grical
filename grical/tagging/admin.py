from django.contrib import admin
from grical.tagging.models import Tag, TaggedItem
from grical.tagging.forms import TagAdminForm

class TagAdmin(admin.ModelAdmin):
    form = TagAdminForm

admin.site.register(TaggedItem)
admin.site.register(Tag, TagAdmin)




