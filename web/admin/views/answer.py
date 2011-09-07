from django.http import Http404, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse

from admin.views import verify
from player_activities.models import PlayerActivity
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from answers.models import Answer
from comments.forms import CommentForm


@login_required
def manage(request, activity_id, template="admin/manage_answers.html"):
    ok = verify(request)
    if ok != None:
        return ok

    try:
        activity = PlayerActivity.objects.untranslated().get(pk=int(activity_id))
    except PlayerActivity.DoesNotExist:
        raise Http404 ("PlayerActivity with id %s does not exist" % activity_id)

    if (request.POST.has_key("submit_btn") and request.POST["submit_btn"] == "Cancel"):
        return HttpResponseRedirect(reverse("admin:manage-answers", args=[activity_id]))

    data = {}
    for answer in Answer.objects.filter(activity=activity):        
        data[answer] = {'comments': answer.comments,}       
        
    comment_form = CommentForm(data=request.POST or None)      
    

    context = {
        'data' : data,        
        'activity': activity,
        'comment_form': comment_form
    }
    return render_to_response(template, RequestContext(request, context))


@login_required
def answer(request, activity_id, answer_id=None, template="admin/trans_answer_edit_new.html"):   
    pass
