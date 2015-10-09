from django.contrib import admin
from comparedata.models import Job, Org, Object, ObjectField, UnmatchedRecord

class OrgInline(admin.TabularInline):
	fields = ['org_number','org_name', 'username', 'access_token', 'status', 'error']
	ordering = ['org_number',]
	model = Org
	extra = 0

class ObjectInline(admin.TabularInline):
	fields = ['label','api_name']
	ordering = ['label',]
	model = Object
	extra = 0

class UnmatchedRecordInline(admin.TabularInline):
	fields = ['org','data']
	ordering = ['org',]
	model = UnmatchedRecord
	extra = 0

class JobAdmin(admin.ModelAdmin):
    list_display = ('created_date','finished_date','status','error')
    ordering = ['-created_date']
    inlines = [OrgInline, ObjectInline, UnmatchedRecordInline]


admin.site.register(Job, JobAdmin)
