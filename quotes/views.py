from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO
from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.staticfiles import finders
from django.core.exceptions import ImproperlyConfigured
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView, DeleteView
from django.views.decorators.http import require_POST

from designs.models import HouseDesign

from .forms import QuoteRequestForm, QuoteUpdateForm
from .models import EstimateInquiry, Quote

FONT_NORMAL_CANDIDATES = (
	('Sarabun', 'Sarabun', 'fonts/Sarabun/Sarabun-Regular.ttf'),
	('Sarabun', 'Sarabun', 'fonts/Sarabun/SarabunNew-Regular.ttf'),
	('Sarabun', 'Sarabun', r'C:/Windows/Fonts/THSarabunNew.ttf'),
	('Sarabun', 'Sarabun', r'C:/Windows/Fonts/THSARABUN.TTF'),
	('Tahoma', 'Tahoma', r'C:/Windows/Fonts/Tahoma.ttf'),
	('LeelawUI', 'LeelawUI', r'C:/Windows/Fonts/LeelawUI.ttf'),
)

FONT_BOLD_CANDIDATES = (
	('Sarabun', 'Sarabun-Bold', 'fonts/Sarabun/Sarabun-Bold.ttf'),
	('Sarabun', 'Sarabun-Bold', 'fonts/Sarabun/SarabunNew-Bold.ttf'),
	('Sarabun', 'Sarabun-Bold', r'C:/Windows/Fonts/THSarabunNew Bold.ttf'),
	('Sarabun', 'Sarabun-Bold', r'C:/Windows/Fonts/THSARABUNBOLD.TTF'),
	('Tahoma', 'Tahoma-Bold', r'C:/Windows/Fonts/TahomaBD.TTF'),
	('LeelawUI', 'LeelawUI-Bold', r'C:/Windows/Fonts/LeelawUIb.ttf'),
)


def _resolve_font_candidate(candidates, preferred_family: str | None = None):
	def iter_candidates():
		if preferred_family:
			for entry in candidates:
				if entry[0] == preferred_family:
					yield entry
			for entry in candidates:
				if entry[0] != preferred_family:
					yield entry
		else:
			for entry in candidates:
				yield entry

	for family, font_name, path_str in iter_candidates():
		candidate_path = Path(path_str)
		if not candidate_path.is_absolute():
			resolved = finders.find(path_str)
			if not resolved:
				continue
			candidate_path = Path(resolved)
		if candidate_path.exists():
			return family, font_name, candidate_path
	return None, None, None


class QuoteQuerysetMixin:
	def get_queryset(self):
		queryset = super().get_queryset().select_related('design', 'catalog_design', 'requested_by')
		if self.request.user.is_superuser:
			return queryset
		return queryset.filter(requested_by=self.request.user)


class QuoteListView(LoginRequiredMixin, QuoteQuerysetMixin, ListView):
	model = Quote
	template_name = 'quotes/quote_list.html'
	context_object_name = 'quotes'


class QuoteDetailView(LoginRequiredMixin, QuoteQuerysetMixin, DetailView):
	model = Quote
	template_name = 'quotes/quote_detail.html'
	context_object_name = 'quote'


class QuoteCreateView(LoginRequiredMixin, CreateView):
	model = Quote
	form_class = QuoteRequestForm
	template_name = 'quotes/quote_form.html'
	success_url = reverse_lazy('quotes:list')

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		user = self.request.user
		designs = HouseDesign.objects.all()
		if not user.is_superuser:
			owned_designs = designs.filter(owner=user)
			existing = Quote.objects.filter(requested_by=user, design__isnull=False).values_list('design_id', flat=True)
			form.fields['design'].queryset = owned_designs.exclude(id__in=existing)
		else:
			form.fields['design'].queryset = designs
		return form

	def form_valid(self, form):
		form.instance.requested_by = self.request.user
		form.instance.status = Quote.Status.PENDING
		if not self.request.user.is_superuser and form.instance.design.owner_id != self.request.user.id:
			form.add_error('design', 'You can only request quotes for your own designs.')
			return self.form_invalid(form)
		return super().form_valid(form)


class QuoteUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Quote
	form_class = QuoteUpdateForm
	template_name = 'quotes/quote_admin_form.html'
	success_url = reverse_lazy('quotes:list')

	def test_func(self):
		return self.request.user.is_superuser


class QuoteDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Quote
	template_name = 'quotes/quote_confirm_delete.html'
	success_url = reverse_lazy('quotes:list')

	def test_func(self):
		return self.request.user.is_superuser


@login_required
@require_POST
def create_estimate_inquiry(request):
	name = request.POST.get('name', '').strip()
	phone = request.POST.get('phone', '').strip()
	email = request.POST.get('email', '').strip()
	land_size_raw = request.POST.get('land_size')
	house_size_raw = request.POST.get('house_size')
	material_grade = (request.POST.get('material_grade') or '').strip().lower()
	floors_raw = request.POST.get('floors')
	min_raw = request.POST.get('estimate_min')
	max_raw = request.POST.get('estimate_max')

	if not name or not phone or not email:
		return JsonResponse({'status': 'error', 'message': 'กรุณากรอกข้อมูลติดต่อให้ครบถ้วน'}, status=400)

	def parse_positive_int(value: str | None, field_label: str) -> int:
		try:
			parsed = int(value) if value is not None else 0
		except (TypeError, ValueError):
			raise ValueError(f'{field_label} ไม่ถูกต้อง') from None
		if parsed < 0:
			raise ValueError(f'{field_label} ต้องเป็นจำนวนเต็มบวก')
		return parsed

	try:
		land_size = parse_positive_int(land_size_raw, 'ขนาดที่ดิน')
		house_size = parse_positive_int(house_size_raw, 'พื้นที่ใช้สอย')
		floors = parse_positive_int(floors_raw, 'จำนวนชั้น')
	except ValueError as exc:
		return JsonResponse({'status': 'error', 'message': str(exc)}, status=400)

	if material_grade not in EstimateInquiry.MaterialGrade.values:
		material_grade = EstimateInquiry.MaterialGrade.STANDARD

	try:
		estimate_min = Decimal(min_raw or '0')
		estimate_max = Decimal(max_raw or '0')
	except (ValueError, ArithmeticError):
		estimate_min = Decimal('0')
		estimate_max = Decimal('0')

	inquiry = EstimateInquiry.objects.create(
		user=request.user,
		name=name,
		phone=phone,
		email=email,
		land_size=land_size,
		house_size=house_size,
		material_grade=material_grade,
		floors=floors,
		estimate_min=estimate_min,
		estimate_max=estimate_max,
	)

	pending_count = EstimateInquiry.objects.filter(handled=False).count()
	return JsonResponse(
		{
			'status': 'ok',
			'message': 'บันทึกคำขอเรียบร้อยแล้ว ทีมงานจะติดต่อกลับโดยเร็วที่สุด',
			'pending_count': pending_count,
			'inquiry_id': inquiry.id,
		},
	)


@login_required
def download_contract_pdf(request, quote_id):
	quote = get_object_or_404(
		Quote.objects.select_related('design', 'catalog_design', 'requested_by'),
		pk=quote_id,
	)
	if not (request.user.is_superuser or quote.requested_by_id == request.user.id):
		raise Http404

	weasyprint_html_cls = None
	try:
		from weasyprint import HTML as WeasyPrintHTML
	except ImportError:
		weasyprint_html_cls = None
	except OSError:
		weasyprint_html_cls = None
	else:
		weasyprint_html_cls = WeasyPrintHTML

	total_price = quote.price or Decimal('0.00')
	client = quote.requested_by
	client_profile = getattr(client, 'profile', None)
	client_contact = {
		'address': getattr(client_profile, 'address', None) if client_profile else None,
		'phone': getattr(client_profile, 'phone', None) if client_profile else None,
	}
	schedule_plan = [
		{
			'label': 'งวดที่ 1',
			'percentage': Decimal('0.30'),
			'description': 'ชำระ 30% เมื่อเซ็นสัญญาก่อสร้าง',
		},
		{
			'label': 'งวดที่ 2',
			'percentage': Decimal('0.40'),
			'description': 'ชำระ 40% เมื่อก่อสร้างโครงสร้างแล้วเสร็จ',
		},
		{
			'label': 'งวดที่ 3',
			'percentage': Decimal('0.30'),
			'description': 'ชำระ 30% ก่อนส่งมอบงานก่อสร้าง',
		},
	]

	installments = []
	for plan in schedule_plan:
		amount = None
		if quote.price:
			amount = (total_price * plan['percentage']).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		installments.append({
			'label': plan['label'],
			'description': plan['description'],
			'percentage_display': f"{(plan['percentage'] * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)}%",
			'amount': amount,
		})

	design_title = quote.reference_name
	design_description = quote.reference_description
	design_code = quote.reference_code
	if quote.design and quote.design.owner:
		designer_name = quote.design.owner.get_full_name() or quote.design.owner.username
	else:
		designer_name = 'ทีมออกแบบ Project House'

	context = {
		'quote': quote,
		'design_title': design_title,
		'design_description': design_description,
		'design_code': design_code,
		'designer_name': designer_name,
		'is_catalog_design': quote.is_catalog_source,
		'client': client,
		'client_contact': client_contact,
		'issued_date': timezone.now(),
		'installments': installments,
		'total_price': total_price,
		'has_price': bool(quote.price),
		'company': {
			'name': 'บริษัท โฮมแมนเนจเมนท์ จำกัด',
			'address': '123/45 ถนนสุขุมวิท แขวงคลองเตย เขตคลองเตย กรุงเทพมหานคร 10110',
			'phone': '02-123-4567',
			'email': 'contact@homemanagement.co.th',
		},
	}

	font_family, normal_font_name, regular_font_path = _resolve_font_candidate(FONT_NORMAL_CANDIDATES)
	bold_family, bold_font_name, bold_font_path = _resolve_font_candidate(
		FONT_BOLD_CANDIDATES, preferred_family=font_family
	)
	if not font_family and bold_family:
		font_family = bold_family
	if not bold_font_name and normal_font_name:
		bold_font_name = f"{normal_font_name}-Bold"
	if not bold_font_path:
		bold_font_path = regular_font_path
	body_font_family = font_family or 'Helvetica'

	html_string = render_to_string('quotes/contract_pdf.html', context)
	html_string = html_string.replace('__BODY_FONT__', body_font_family)
	pdf_bytes = None
	if weasyprint_html_cls:
		try:
			pdf_bytes = weasyprint_html_cls(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf()
		except OSError:
			pdf_bytes = None  # fall back if system libs missing

	if pdf_bytes is None:
		try:
			from xhtml2pdf import pisa
		except ImportError as exc:
			raise ImproperlyConfigured(
				'ไม่สามารถสร้าง PDF ได้ เนื่องจาก WeasyPrint หรือ xhtml2pdf ไม่พร้อมใช้งาน โปรดติดตั้ง GTK สำหรับ WeasyPrint หรือรัน "pip install xhtml2pdf".'
			) from exc
		from reportlab.pdfbase import pdfmetrics
		from reportlab.pdfbase.ttfonts import TTFont

		def register_font(font_name: str | None, font_path: Path | None):
			if not font_name or not font_path:
				return
			try:
				pdfmetrics.getFont(font_name)
			except KeyError:
				try:
					pdfmetrics.registerFont(TTFont(font_name, str(font_path)))
				except Exception:
					pass

		register_font(normal_font_name or 'Helvetica', regular_font_path)
		register_font(bold_font_name, bold_font_path if bold_font_path else None)
		try:
			if font_family and normal_font_name and bold_font_name and regular_font_path and bold_font_path:
				pdfmetrics.registerFontFamily(font_family, normal=normal_font_name, bold=bold_font_name)
			elif font_family and normal_font_name and regular_font_path:
				pdfmetrics.registerFontFamily(font_family, normal=normal_font_name)
		except Exception:
			pass
		if regular_font_path and normal_font_name:
			try:
				pisa.DEFAULT_FONT = normal_font_name
			except Exception:
				pass

		pdf_stream = BytesIO()
		result = pisa.CreatePDF(html_string, dest=pdf_stream, encoding='utf-8')
		if result.err:
			raise ImproperlyConfigured(
				'ไม่สามารถสร้างไฟล์ PDF ได้ กรุณาตรวจสอบการติดตั้งไลบรารี WeasyPrint หรือ xhtml2pdf.'
			)
		pdf_bytes = pdf_stream.getvalue()

	response = HttpResponse(pdf_bytes, content_type='application/pdf')
	response['Content-Disposition'] = f'attachment; filename="contract_quote_{quote.id}.pdf"'
	return response
