import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from django.db.models import Avg
from django.http import HttpResponseNotAllowed
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.generic import FormView, TemplateView

from designs.models import HouseDesign
from quotes.models import EstimateInquiry, Quote
from construction.models import ConstructionProject

from .forms import UserRegistrationForm


class UserRegisterView(FormView):
	template_name = 'accounts/register.html'
	form_class = UserRegistrationForm
	success_url = reverse_lazy('dashboard')

	def form_valid(self, form):
		user = form.save()
		login(self.request, user)
		return super().form_valid(form)


class UserLoginView(LoginView):
	template_name = 'accounts/login.html'
	redirect_authenticated_user = True

	def form_valid(self, form):
		response = super().form_valid(form)
		remember = self.request.POST.get('remember_me')
		if remember:
			self.request.session.set_expiry(60 * 60 * 24 * 30)
		else:
			self.request.session.set_expiry(0)
		return response


class UserLogoutView(LogoutView):
	next_page = reverse_lazy('accounts:login')


class DashboardView(TemplateView):
	def get_template_names(self):
		# Show the public homepage (dashboard.html) to all users, including admins,
		# so admins can also see the hero/search landing page.
		# The admin-specific summary page remains accessible via the Django admin.
		return ['dashboard.html']

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		user = self.request.user
		quotes_qs_base = Quote.objects.select_related('design', 'catalog_design', 'requested_by')
		
		if user.is_authenticated:
			if user.is_superuser:
				designs_qs = HouseDesign.objects.all()
				quotes_qs = quotes_qs_base
				project_qs = ConstructionProject.objects.all()
			else:
				designs_qs = HouseDesign.objects.filter(owner=user)
				quotes_qs = quotes_qs_base.filter(requested_by=user)
				project_qs = ConstructionProject.objects.filter(owner=user)
			
			projects_qs = project_qs.select_related('quote__design', 'quote__catalog_design').prefetch_related('updates')
			progress_agg = projects_qs.aggregate(avg_progress=Avg('total_progress'))
			context['average_progress'] = round(progress_agg['avg_progress'] or 0, 1)
		else:
			designs_qs = HouseDesign.objects.none()
			quotes_qs = Quote.objects.none()
			projects_qs = ConstructionProject.objects.none()
			context['average_progress'] = 0

		context['designs'] = designs_qs
		context['quotes'] = quotes_qs
		context['projects'] = projects_qs
		context['pending_quotes_count'] = quotes_qs.filter(status=Quote.Status.PENDING).count() if user.is_authenticated else 0
		if user.is_superuser:
			pending_inquiries_qs = EstimateInquiry.objects.filter(handled=False).select_related('user')
			context['pending_estimate_inquiry_count'] = pending_inquiries_qs.count()
			context['pending_estimate_inquiries'] = pending_inquiries_qs[:5]
			try:
				context['estimate_inquiry_admin_url'] = reverse('admin:quotes_estimateinquiry_changelist')
			except Exception:
				context['estimate_inquiry_admin_url'] = None
		return context


def _mask_identifier(identifier: str | None) -> str | None:
	if not identifier:
		return None
	value = str(identifier)
	if '-' in value:
		parts = value.split('-')
		masked_parts: list[str] = []
		last_index = len(parts) - 1
		for idx, part in enumerate(parts):
			if idx in (0, 1) or idx >= last_index - 1:
				masked_parts.append(part)
			else:
				masked_parts.append('X' * len(part))
		return '-'.join(masked_parts)
	cleaned = re.sub(r'\W+', '', value)
	if len(cleaned) <= 4:
		return 'X' * len(cleaned)
	keep_start = min(3, len(cleaned) // 2)
	keep_end = min(2, len(cleaned) - keep_start)
	masked_section = 'X' * max(len(cleaned) - keep_start - keep_end, 0)
	return f"{cleaned[:keep_start]}{masked_section}{cleaned[-keep_end:]}"


@login_required
def email_my_data(request):
	if request.method != 'POST':
		return HttpResponseNotAllowed(['POST'])
	user = request.user
	if not user.email:
		messages.error(request, 'ไม่พบอีเมลในบัญชี ผู้ดูแลระบบไม่สามารถส่งข้อมูลส่วนตัวได้')
		return redirect('dashboard')
	try:
		profile = user.profile  # type: ignore[attr-defined]
	except (AttributeError, ObjectDoesNotExist):
		profile = None
	address = None
	phone = None
	national_id = None
	tax_id = None
	if profile:
		address = getattr(profile, 'address', None)
		phone = getattr(profile, 'phone', None) or getattr(profile, 'phone_number', None)
		national_id = getattr(profile, 'national_id', None)
		tax_id = getattr(profile, 'tax_id', None)
	address = address or getattr(user, 'address', '')
	phone = phone or getattr(user, 'phone', '')
	masked_national_id = _mask_identifier(national_id)
	masked_tax_id = _mask_identifier(tax_id)
	design_count = user.house_designs.count() if hasattr(user, 'house_designs') else HouseDesign.objects.filter(owner=user).count()
	quote_count = user.quotes.count() if hasattr(user, 'quotes') else Quote.objects.filter(requested_by=user).count()
	project_count = user.construction_projects.count() if hasattr(user, 'construction_projects') else ConstructionProject.objects.filter(owner=user).count()
	summary_line = (
		f"คุณมีแบบบ้าน {design_count} รายการ, ใบเสนอราคา {quote_count} รายการ และโครงการก่อสร้าง {project_count} โครงการ"
	)
	dashboard_url = request.build_absolute_uri(reverse('dashboard'))
	logo_url = request.build_absolute_uri(static('images/logo.png'))
	generated_at = timezone.localtime(timezone.now())
	context = {
		'full_name': user.get_full_name() or user.get_username(),
		'username': user.get_username(),
		'email': user.email,
		'phone': phone or 'ไม่พบข้อมูล',
		'address': address or 'ไม่พบข้อมูล',
		'national_id': masked_national_id,
		'tax_id': masked_tax_id,
		'design_count': design_count,
		'quote_count': quote_count,
		'project_count': project_count,
		'summary_line': summary_line,
		'generated_at': generated_at,
		'dashboard_url': dashboard_url,
		'logo_url': logo_url,
	}
	html_body = render_to_string('emails/personal_data_summary.html', context)
	text_body = strip_tags(html_body)
	subject = 'Your Personal Data Summary'
	from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@housephakphum.local')
	email = EmailMultiAlternatives(subject, text_body, from_email, [user.email])
	email.attach_alternative(html_body, 'text/html')
	email.send()
	messages.success(request, 'เราได้ส่งข้อมูลส่วนตัวไปยังอีเมลของคุณเรียบร้อยแล้ว')
	redirect_to = request.POST.get('next') or 'dashboard'
	return redirect(redirect_to)
