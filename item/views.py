from django.views.generic import TemplateView, DetailView
from django.shortcuts import render_to_response
from django.template import RequestContext

from item.models import Computer
from item.forms import UserForm, UserProfileForm
from django.contrib.auth.models import User


class HomeView(TemplateView):
    template_name = "index.html"

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['computers'] = Computer.objects.filter(is_public=True).order_by('-created_at')[:10]
        context['last_users'] = User.objects.order_by('-date_joined')[:5]
        return context


class ItemDetail(DetailView):
    model = Computer


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
