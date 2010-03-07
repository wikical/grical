from gridcalendar.gridcal.models import Event, EventUrl, EventTimechunk, EventDeadline, Tag
from django.contrib import admin

class UrlInline(admin.StackedInline):
    model = EventUrl
    extra = 1

class TimechunkInline(admin.StackedInline):
    model = EventTimechunk
    extra = 1

class DeadlineInline(admin.StackedInline):
    model = EventDeadline
    extra = 1

class EventAdmin(admin.ModelAdmin):
    # saves the user logged-in as user (owner) of the event when adding a new Event
    def save_model(self, request, obj, form, change):
        if not change:
            obj.user = request.user
        obj.save()
    list_display = ('title', 'start', 'city', 'country')
    list_filters = ['start', 'country']
    search_fields = ['title', 'tags', 'country', 'city']
    date_hierarchy = 'start'
    inlines = [UrlInline, TimechunkInline, DeadlineInline]

admin.site.register(Event, EventAdmin)
admin.site.register(EventUrl)
admin.site.register(EventTimechunk)
admin.site.register(EventDeadline)
# admin.site.register(Tag)

