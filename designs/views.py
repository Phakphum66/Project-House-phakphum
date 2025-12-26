from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import HouseDesignForm
from .models import HouseDesign


class OwnerRestrictedQuerysetMixin:
	def get_queryset(self):
		queryset = super().get_queryset()
		if self.request.user.is_superuser:
			return queryset.select_related('owner')
		return queryset.filter(owner=self.request.user).select_related('owner')


class HouseDesignListView(LoginRequiredMixin, OwnerRestrictedQuerysetMixin, ListView):
	model = HouseDesign
	template_name = 'designs/design_list.html'
	context_object_name = 'designs'


class HouseDesignDetailView(LoginRequiredMixin, OwnerRestrictedQuerysetMixin, DetailView):
	model = HouseDesign
	template_name = 'designs/design_detail.html'
	context_object_name = 'design'


class HouseDesignCreateView(LoginRequiredMixin, CreateView):
	model = HouseDesign
	form_class = HouseDesignForm
	template_name = 'designs/design_form.html'
	success_url = reverse_lazy('designs:list')

	def form_valid(self, form):
		form.instance.owner = self.request.user
		return super().form_valid(form)


class HouseDesignUpdateView(LoginRequiredMixin, OwnerRestrictedQuerysetMixin, UpdateView):
	model = HouseDesign
	form_class = HouseDesignForm
	template_name = 'designs/design_form.html'
	success_url = reverse_lazy('designs:list')


class HouseDesignDeleteView(LoginRequiredMixin, OwnerRestrictedQuerysetMixin, DeleteView):
	model = HouseDesign
	template_name = 'designs/design_confirm_delete.html'
	success_url = reverse_lazy('designs:list')
