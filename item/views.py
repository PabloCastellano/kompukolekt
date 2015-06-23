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
from item.models import Computer, HardDisk, CPU, GPU, Motherboard, Memory, NetworkAdapter
from item.parsers import parse_inxi

import datetime


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

        hostname = request.POST.get('hostname')
        format = request.POST.get('type')
        data = request.FILES.get('data')
        print (data, format, hostname)
        if data.size > MAX_DATA_SIZE:
            return HttpResponse('File too large', status=500)
        if None in (data, format, hostname):
            return HttpResponse('Some parameter is missing', status=500)

        content = data.read()

        if format == 'inxi':
             computer_dict = parse_inxi(content)
        elif format == 'sysinfo':
            raise NotImplementedError
        else:
            return HttpResponse('Unknown type "%s"' % format, status=500)

        try:
            Computer.objects.get(name=computer_dict['hostname'], user=User.objects.get(username=username))
            return HttpResponse('Computer name already exists for this user', status=500)
        except Computer.DoesNotExist:
            pass

        try:
            gpu = GPU.objects.get(name=computer_dict['gpu_name'])
        except GPU.DoesNotExist:
            if 'NVIDIA' in computer_dict['gpu_chipset']:
                gpu_vendor = 'NVIDIA'
            elif 'ATI' in computer_dict['gpu_chipset']:
                gpu_vendor = 'ATI'
            else:
                gpu_vendor = 'Unknown'
            gpu = GPU.objects.create(name=computer_dict['gpu_name'], vendor=gpu_vendor)

        try:
            cpu = CPU.objects.get(name=computer_dict['cpu'])
        except CPU.DoesNotExist:
            if 'Intel' in computer_dict['cpu']:
                cpu_vendor = 'Intel'
            elif 'AMD' in computer_dict['cpu']:
                cpu_vendor = 'AMD'
            else:
                cpu_vendor = 'Unknown'
            cpu = CPU.objects.create(name=computer_dict['cpu'], model=computer_dict['cpu'], vendor=cpu_vendor)

        try:
            hd = HardDisk.objects.get(model=computer_dict['hd_model'])
        except HardDisk.DoesNotExist:
            assert(computer_dict['hd_unit'] == 'GB')
            hd = HardDisk.objects.create(name=computer_dict['hd_model'], model=computer_dict['hd_model'], capacity_gb=computer_dict['hd_capacity'])

        mobo, _ = Motherboard.objects.get_or_create(vendor=computer_dict['mobo_vendor'], name=computer_dict['mobo_model'])
        generic_memory = Memory.objects.get(name='Generic', capacity_mb=1024)
        generic_network = NetworkAdapter.objects.get(name='Generic', speed='1 Gbps')
        # Computer(computer).save()
        print(cpu)
        print(gpu)
        print(hd)
        computer = Computer(name=computer_dict['hostname'], user=User.objects.get(username='pablo'))
        computer.is_laptop = False
        computer.is_public = True
        computer.cpu = cpu
        computer.mobo = mobo
        computer.gpu = gpu
        computer.hd = hd
        computer.memory = generic_memory
        computer.network = generic_network
        computer.created_at = datetime.datetime.now()
        computer.updated_at = datetime.datetime.now()
        computer.year = datetime.datetime.now().year
        computer.save()

        # TODO: Save to "uploads" folder
        fname = "info_%d-%s-%s.txt" % (computer.id, computer.user, datetime.datetime.now())
        with open(fname, 'wb+') as fp:
            fp.write(content)
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
