from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import ListView
from django.urls import reverse_lazy
from django.db.models import Avg, Count, Max
from django.db import transaction
from django.views import generic
from . forms import UserForm, QuestionForm, ProfileForm
from . models import Question, Answer, User, Profile
from django.contrib.sites.shortcuts import get_current_site
from .tokens import account_activation_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_text
from django.http import HttpResponse,HttpResponseRedirect, JsonResponse
from .checker.report import Report
import json
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from datetime import datetime
from django.db.models import Avg
from django.core.mail import EmailMessage
from django.contrib.auth import login, authenticate
import random
import string
import threading
import pytz
from django.utils import timezone

datetimeformat = "%Y %d %m %H:%M"
tz = pytz.timezone('Asia/Kolkata') #TODO: set to users timezone somehow

@login_required(login_url="login")
#@transaction.atomic
def update_profile(request):
    # if request.method == 'POST':
    #     user_form = UserForm(request.POST, instance=request.user)
    #     profile_form = ProfileForm(request.POST, instance=request.user.profile)
    #     if user_form.is_valid() and profile_form.is_valid():
    #         user_form.save()
    #         profile_form.save()
    #         messages.success(request, _('Your profile was successfully updated!'))
    #         return redirect('settings:profile')
    #     else:
    #         messages.error(request, _('Please correct the error below.'))
    # else:
    #     user_form = UserForm(instance=request.user)
    #     profile_form = ProfileForm(instance=request.user.profile)
    # return render(request, 'registration/profile.html', {
    #     'user_form': user_form,
    #     'profile_form': profile_form
    # })
    return render(request, 'registration/profile.html', {
        'user': request.user,
        'profile': request.user.profile
    })

class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient):
        self.subject = subject
        self.recipient = recipient
        self.html_content = html_content
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMessage(self.subject, self.html_content, to=[self.recipient])
        msg.content_subtype = "html"
        try:
            msg.send()
        except e:
            print(e)

def send_html_mail(subject, html_content, recipient):
    EmailThread(subject, html_content, recipient).start()

def signup(request):
    c = Profile.objects.order_by().values_list('college').distinct()
    colleges = [col[0] for col in c if col[0]]
    print(colleges)
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            profile = profile_form.save(commit = False)
            user = user_form.save(commit = False)
            user.is_active = False
            user.save()
            user.profile.name = profile.name
            user.profile.college = profile.college
            user.profile.college_id = profile.college_id
            user.profile.branch_of_study = profile.branch_of_study
            user.save()
            
            
            current_site = get_current_site(request)
            mail_subject = 'Activate your grammar expert account.'
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            tok = account_activation_token.make_token(user)          
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':uid.decode('utf-8'),
                'token':tok,
            })
            to_email = user_form.cleaned_data.get('email')

            send_html_mail(mail_subject, message, to_email)
            # email = EmailMessage(
            #             mail_subject, message, to=[to_email]
            # )
            # email.send()
            return render(request, 'registration/message.html', {'message':'Please confirm your email address to complete the registration'})
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    return render(request, 'registration/signup.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'college_list': colleges
    })

def activate(request, uidb64, token, backend='django.contrib.auth.backends.ModelBackend'):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)

    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return redirect('homepage')
    else:
        return render(request, 'registration/message.html', {"message":'Activation link is invalid!'})

def not_found(request):
    return render(request, 'errors/not_found.html')

def server_error(request):
    return render(request, 'errors/server_error.html')

def permission_denied(request):
    return render(request, 'errors/permission_denied.html')

def bad_request(request):
    return render(request, 'errors/bad_request.html')

@login_required(login_url="login")
@permission_required('exam.create_test')
def questionmanager(request):
    user = request.user
    context = dict()
    if request.method == "POST":
        form = QuestionForm(request.POST)
        code = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=8))
        c = Question.objects.filter(code=code)
        while len(list(c))>0:
            code = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=8))
            c = Question.objects.filter(code=code)
        if form.is_valid():
            question = form.save(commit = False)
            question.user = request.user
            question.code = code
            question.save()
    else:
        form = QuestionForm()
    context['form'] = form
    context['object_list'] = Question.objects.filter(user_id=request.user.id)
    return render(request, template_name = 'examcreator/questionmanager.html', context=context)

@login_required(login_url="login")
def practice(request):
    context = dict()
    results = []
    questions = Question.objects.filter(user_id = 1)
    for q in questions:
        a = list(Answer.objects.filter(user_id=request.user.id,question_id=q.id))
        s = 0
        n = 0
        avg = 0
        for x in a:
            s += x.score
            n += 1
        if n>0:
            avg = s/n
        if len(a) < q.attempts_allowed:
            results.append((q, True, avg, n, q.attempts_allowed))
        else:
            
            results.append((q, False, avg, n, q.attempts_allowed))
    return render(request, template_name = 'examuser/practice.html', context={"questions":results})

def main_view(request):
    return render(request,template_name="homepage.html", context={"user": request.user})


@login_required(login_url="login")
def attempt(request,code):
    s = datetime.strftime(datetime.now(), datetimeformat)
    
    q = Question.objects.get(code=code)
    a = list(Answer.objects.filter(user_id=request.user.id,question_id=q.id))
    if len(a) < q.attempts_allowed:
        return render(request, template_name="examuser/attempt.html",context = {'question': q, 'starttime':s})
    else:
        return redirect('homepage')

def can_attempt_question(userid, qid):
    q = Question.objects.get(pk=qid)
    a = list(Answer.objects.filter(user_id=userid,question_id=qid))
    return len(a) < q.attempts_allowed

@login_required(login_url="login")
def canattempt(request, code):
    q = Question.objects.get(code=code)
    a = list(Answer.objects.filter(user_id=request.user.id,question_id=q.id))
    if len(a) < q.attempts_allowed:
        return JsonResponse({"status":"OK", "url":request.build_absolute_uri("/attempt/"+code)})
    else:
        return JsonResponse({"status":"You have already reached maximum attempt limit. Please try with diferent code or practice!"})

@login_required(login_url="login")
def get_results(request):
    if request.method == "POST":
        id = request.POST['id']
        qs =  Answer.objects.get(pk=id)
        if request.user == qs.user or request.user.has_perm('exam.create_test'):
            return HttpResponse(qs.Json)
        else:
            return JsonResponse([])
    else:
        return JsonResponse([])

@login_required(login_url="login")
def fetch_results(request):
    if request.method == "POST":
        essay = request.POST['essay']
        qid = request.POST['qid']
        q = Question.objects.get(pk=qid)

        if not can_attempt_question(request.user.id, qid):
           return JsonResponse({'status':'Already Submitted. Further submissions not allowed'})

        starttime = datetime.strptime(request.POST['starttime'], datetimeformat)
        endtime = datetime.now()
        d = Report(essay, q.word_limit).reprJSON()
        score = d['score']
        grammarCount = d['grammarErrorCount']
        spellingCount = d['spellingErrorCount']
        json_object = json.dumps(d)
        foo_instance = Answer(user_id=request.user.id,question_id = qid,Json = json_object,score = score,grammarErrors = grammarCount ,spellingErrors = spellingCount, starttime=starttime, endtime=endtime)
        foo_instance.save()
       
        return HttpResponse(json_object)

@login_required(login_url="login")
@permission_required('exam.create_test')
def updatequestion(request, qid):
    form = QuestionForm(request.POST)
    q = Question.objects.get(pk = qid)
    return render(request,"examcreator/editquestion.html",{'form':form})
        
@login_required(login_url="login")
@permission_required('exam.create_test')
def getquestiondata(request, qid):
    obj = Question.objects.get(pk = qid)
    return JsonResponse({"wordlimit":obj.word_limit, "timelimit":obj.time_limit, "attempts":obj.attempts})

class EditQuestion(PermissionRequiredMixin,LoginRequiredMixin,generic.UpdateView):
    login_url = '/login/'
    model = Question
    form_class = QuestionForm
    template_name = 'examcreator/editquestion.html'
    success_url = reverse_lazy("questionmanager")

    def has_permission(self):
        question  = Question.objects.get(id=self.kwargs['pk'])
        return question.user == self.request.user

    def has_no_permission(self):
        if self.raise_exception:
            raise PermissionDenied(self.get_permission_denied_message())
        return redirect(self.request.META.get("HTTP_REFERER"))


@login_required(login_url="login")
@permission_required('exam.create_test')
def delete_question(request, qid):
    question = Question.objects.get(pk=qid)
    # add case where user can del question which is created by him only
    if question.user_id != request.user.id:
        return HttpResponse("Not allowed")
    else:
        question.delete()
        return redirect('questionmanager')

def getFormattedDuration(timeinsec):
    timeinsec = int(timeinsec)
    m = timeinsec//60
    s = timeinsec - m*60
    return "{0}m {1}s".format(m, s)

@login_required(login_url="login")
@permission_required('exam.create_test')
def update_comment(request):
    if request.POST:
        comment = request.POST["comment"]
        aid = request.POST["id"]
        a = Answer.objects.get(pk=aid)
        if a:
            # only the person who created the question can give comments for its answers
            q = Question.objects.get(pk=a.question_id)
            if q.user == request.user:
                a.comments = comment
                a.save()
                return JsonResponse({"status":"OK"})
            else:
                return JsonResponse({"status":"Permission Denied"})
        
    return JsonResponse({"status":"invalid data"})
    

@login_required(login_url="login")
@permission_required('exam.create_test')
def leaderboard(request, qid):
    qs = Answer.objects.filter(question_id=qid).order_by('-score').only("id", "user", "score", "starttime", "endtime", "comments")
    q = Question.objects.get(pk=qid)
    results = []
    if qs:
        rank = 1
        for attempt in qs:
            t = getFormattedDuration((attempt.endtime - attempt.starttime).total_seconds())
            results.append((attempt.user, rank, round(attempt.score,2), datetime.strftime(attempt.endtime.astimezone(tz), "%d-%m-%Y %H:%M ("+t+")"), attempt.id, attempt.comments))
            rank += 1
    return render(request, template_name="examcreator/leaderboard.html", context={"results": results, "question":q.question, "questionsetter":q.user==request.user})

@login_required(login_url="login")
def getuserattemptdata(request):
    a =  Answer.objects.filter(user_id=request.user.id).order_by('starttime').only("score", "starttime")
    data = []
    labels = []
    for x in a:
        data.append(round(x.score,2))
        labels.append(x.starttime)
    return JsonResponse({"data":data, "labels":labels})

@login_required(login_url="login")
def getuserperformance(request):
    #TODO: calculate rank of user overall and also branchwise.
    # should we consider all essays or only with users who attempted same essays
    # should we be comparing progress trends as well. What to maintain in the cube?
    score = Answer.objects.filter(user_id = request.user.id).aggregate(Avg('score'))
    avg_score = score['score__avg']
    no_of_attempts = Answer.objects.filter(user_id = request.user.id).count()
    qs = Answer.objects.filter(user_id=request.user.id).order_by('-score').only("id", "question_id", "score", "starttime", "endtime", "grammarErrors", "spellingErrors", "comments")
    results = []
    avgscore = 0
    totalattempts = 0
    attempttimes = []
    lastattempted = "nil"
    
    print(timezone.now())
    if qs:
        for attempt in qs:
            avgscore += attempt.score
            totalattempts += 1
            attempttimes.append(attempt.starttime)
            q = Question.objects.get(pk=attempt.question_id).question
            t = getFormattedDuration((attempt.endtime - attempt.starttime).total_seconds())
            
            results.append((q, round(attempt.score,2), datetime.strftime(attempt.endtime.astimezone(tz), "%d-%m-%Y %H:%M ("+t+")"), attempt.grammarErrors, attempt.spellingErrors, attempt.comments, attempt.id))
    if(totalattempts>0):
        avgscore /= totalattempts
        lastattempted = sorted(attempttimes)[-1]
    
    return render(request, template_name="examuser/userperformance.html", context={"results": results, "user":request.user, "avgscore":round(avgscore,2), "totalattempts":totalattempts, "lastattempted":lastattempted})

@login_required(login_url="login")
@permission_required('exam.create_test')
def getuserperfdata(request, uid):
    a = Answer.objects.filter(question__user_id=request.user.id, user_id=uid).order_by('starttime').only('score', 'starttime')
    data = []
    labels = []
    for x in a:
        data.append(round(x.score,2))
        labels.append(x.starttime)
    return JsonResponse({"data":data, "labels":labels})

    

@login_required(login_url="login")
@permission_required('exam.create_test')
def getallusersummary(request):
    minscore = 0
    maxscore = 10
    if request.method=="POST":
        minscore = request.POST["minscore"]
        maxscore = request.POST["maxscore"]

    #TODO: improve query performance
    qs = Answer.objects.filter(question__user_id=request.user.id, score__gte = minscore, score__lte = maxscore).select_related().values("user_id").annotate(Avg('score'), Count('question'), Max('starttime'))
    results = []
    for result in qs:
        u = User.objects.get(pk=result['user_id'])
        results.append({"userid":result['user_id'], "username":u.username, "profile":u.profile, "avgscore":round(result['score__avg'],2), "count":result['question__count'], "lastattempted":result['starttime__max']})
    
    results.sort(key=lambda x: -x["avgscore"])

    attrs = {"minscore":minscore, "maxscore":maxscore}
    return render(request, template_name="examcreator/getallusersummary.html", context={"results":results, "attrs":attrs})
