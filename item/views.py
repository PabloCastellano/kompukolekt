from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, DetailView

from item.forms import UserForm, UserProfileForm, ComputerForm
from item.models import Computer
from item.parsers import create_computer_from_parser

import datetime


def user_profile(request):
    return HttpResponseRedirect(reverse('item-dashboard'))


def edit_item(request, pk):
    context = RequestContext(request)

    if request.method == 'POST':
        old_computer = Computer.objects.get(pk=pk)
        form = ComputerForm(data=request.POST, instance=old_computer)

        if form.is_valid():
            computer = form.save(commit=False)
            computer.updated_at = datetime.datetime.now()
            computer.save()

            return HttpResponseRedirect(reverse('item-detail', args=[pk]))
        else:
            print('ERRORS')
            print(form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        computer = Computer.objects.get(pk=pk)
        form = ComputerForm(instance=computer)

    #print form
    return render_to_response('item/edit.html', {'form': form, 'computer': computer}, context)


def delete_item(request, pk):
    #get_or_404
    computer = Computer.objects.get(pk=pk)
    computer.active = False
    computer.save()
    #computer.delete()
    messages.success(request, 'Your computer %s has been deleted!' % computer.name)
    return HttpResponseRedirect(reverse('item-dashboard'))


def new_item(request):
    context = RequestContext(request)

    if request.method == 'POST':
        form = ComputerForm(data=request.POST)

        if form.is_valid():
            computer = form.save(commit=False)
            computer.user = request.user
            computer.created_at = datetime.datetime.now()
            computer.updated_at = datetime.datetime.now()
            computer.save()

            messages.success(request, 'Your computer %s has been added!' % computer.name)
            return HttpResponseRedirect(reverse('item-dashboard'))
        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print(form.errors)

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        form = ComputerForm()

    print form
    return render_to_response('item/submit.html', {'form': form}, context)


class ItemDashboardView(TemplateView):
    template_name = "dashboard.html"

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ItemDashboardView, self).dispatch(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ItemDashboardView, self).get_context_data(**kwargs)
        context['computers'] = Computer.objects.filter(user=self.request.user, active=True).order_by('-created_at')[:20]
        return context


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['computers'] = Computer.objects.filter(is_public=True).order_by('-created_at')[:10]
        context['last_users'] = User.objects.order_by('-date_joined')[:5]
        return context


class ItemDetail(DetailView):
    model = Computer


MAX_DATA_SIZE = 5120 # 5KB

@csrf_exempt
def submit_item(request):

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is None or not user.is_active:
            return HttpResponse('Login error', status=500)

        #hostname = request.POST.get('hostname')
        hostname = 'dummy'
        format = request.POST.get('type')
        data = request.FILES.get('data')
        print (data, format, hostname)
        if data.size > MAX_DATA_SIZE:
            return HttpResponse('File too large', status=500)
        if None in (data, format, hostname):
            return HttpResponse('Some parameter is missing', status=500)

        content = data.read()

        try:
            computer = create_computer_from_parser(content, user, format)
        except:
            return HttpResponse('Unknown type "%s"' % format, status=500)

        if not computer:
            return HttpResponse('Computer name already exists for this user', status=500)

        return HttpResponse('OK')

    return HttpResponse()




# http://www.tangowithdjango.com/book/chapters/login.html
def register(request):
    context = RequestContext(request)
    registered = False

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()

            user.set_password(user.password)
            user.save()

            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()
            registered = True

        # Invalid form or forms - mistakes or something else?
        # Print problems to the terminal.
        # They'll also be shown to the user.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render our form using two ModelForm instances.
    # These forms will be blank, ready for user input.
    else:
        user_form = UserForm()
        profile_form = UserProfileForm()

    return render_to_response('registration/register.html',
            {'user_form': user_form, 'profile_form': profile_form, 'registered': registered},
            context)
