from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from quotes.models import Quote

from .forms import ConstructionProjectForm, ProgressUpdateForm
from .models import ConstructionProject, ProgressUpdate


class ProjectQuerysetMixin:
	def get_queryset(self):
		queryset = super().get_queryset().select_related('owner', 'quote__design')
		if self.request.user.is_superuser:
			return queryset
		return queryset.filter(owner=self.request.user)


class ConstructionProjectListView(LoginRequiredMixin, ProjectQuerysetMixin, ListView):
	model = ConstructionProject
	template_name = 'construction/project_list.html'
	context_object_name = 'projects'


class ConstructionProjectDetailView(LoginRequiredMixin, ProjectQuerysetMixin, DetailView):
	model = ConstructionProject
	template_name = 'construction/project_detail.html'
	context_object_name = 'project'

	def get_queryset(self):
		return super().get_queryset().prefetch_related('updates')


class ConstructionProjectCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
	model = ConstructionProject
	form_class = ConstructionProjectForm
	template_name = 'construction/project_form.html'
	success_url = reverse_lazy('construction:list')

	def test_func(self):
		return self.request.user.is_superuser

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.fields['quote'].queryset = Quote.objects.filter(status=Quote.Status.APPROVED)
		return form

	def form_valid(self, form):
		quote = form.cleaned_data.get('quote')
		owner = form.cleaned_data.get('owner')
		if quote and quote.status != Quote.Status.APPROVED:
			form.add_error('quote', 'Only approved quotes can be linked to a project.')
			return self.form_invalid(form)
		if quote and owner != quote.requested_by:
			form.add_error('owner', 'Owner must match the approved quote requester.')
			return self.form_invalid(form)
		return super().form_valid(form)


class ConstructionProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = ConstructionProject
	form_class = ConstructionProjectForm
	template_name = 'construction/project_form.html'
	success_url = reverse_lazy('construction:list')

	def test_func(self):
		return self.request.user.is_superuser

	def get_form(self, form_class=None):
		form = super().get_form(form_class)
		form.fields['quote'].queryset = Quote.objects.filter(status=Quote.Status.APPROVED)
		return form

	def form_valid(self, form):
		quote = form.cleaned_data.get('quote')
		owner = form.cleaned_data.get('owner')
		if quote and quote.status != Quote.Status.APPROVED:
			form.add_error('quote', 'Only approved quotes can be linked to a project.')
			return self.form_invalid(form)
		if quote and owner != quote.requested_by:
			form.add_error('owner', 'Owner must match the approved quote requester.')
			return self.form_invalid(form)
		return super().form_valid(form)


class ProgressUpdateCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
	model = ProgressUpdate
	form_class = ProgressUpdateForm
	template_name = 'construction/progress_form.html'

	def test_func(self):
		return self.request.user.is_superuser

	def get_success_url(self):
		project = self.get_project()
		return reverse_lazy('construction:detail', kwargs={'pk': project.pk})

	def get_project(self) -> ConstructionProject:
		return get_object_or_404(ConstructionProject, pk=self.kwargs['project_pk'])

	def form_valid(self, form):
		form.instance.project = self.get_project()
		return super().form_valid(form)

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['project'] = self.get_project()
		return context


class ConstructionProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = ConstructionProject
	template_name = 'construction/project_confirm_delete.html'
	success_url = reverse_lazy('construction:list')

	def test_func(self):
		return self.request.user.is_superuser
