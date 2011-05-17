from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User

from web.instances.models import Instance
from web.comments.models import Comment

class Issue(models.Model):
    message = models.CharField(max_length=260, verbose_name='Issue')
    coins = models.IntegerField(default=0)

    instance = models.ForeignKey(Instance)
    comments = models.ManyToManyField(Comment, blank=True, null=True)

    def __unicode__(self):
        return self.message[:25]

class PlayerIssue(models.Model):
    user = models.ForeignKey(User)
    issue = models.ForeignKey(Issue)
    coins = models.IntegerField(default=0)

class IssueAdmin(admin.ModelAdmin):
    list_display = ('message', 'coins')
    exclude = ('instance',)

    def save_model(self, request, obj, form, change):
        obj.instance = request.session.get('admin_instance')
        obj.save()

    def queryset(self, request):
        qs = super(IssueAdmin, self).queryset(request)

        return qs.filter(instance=request.session.get('admin_instance'))

    obj = None

    def get_form(self, request, obj=None, **kwargs):
        self.obj = obj 

        return super(IssueAdmin, self).get_form(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == 'comments' and getattr(self, 'obj', None):
            kwargs['queryset'] = Issue.objects.get(id=self.obj.id).comments.all()
        elif db_field.name == 'comments':
            kwargs['queryset'] = Issue.objects.filter(id=-2)

        return super(IssueAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)
