from cloudcalendar.events.models import Event, Tag
from django.contrib import admin

class EventAdmin(admin.ModelAdmin):
	# saves the user logged-in as user (owner) of the event when adding a new Event
	def save_model(self, request, obj, form, change):
		if not change:
			obj.user = request.user
		obj.save()
	list_display = ('title', 'start', 'city', 'country', 'url')
	list_filters = ['start', 'country']
	search_fields = ['title', 'tags', 'country', 'city']
	date_hierarchy = 'start'

admin.site.register(Event, EventAdmin)
# admin.site.register(Tag)

