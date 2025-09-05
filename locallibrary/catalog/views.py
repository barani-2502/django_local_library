import datetime
from django.shortcuts import render, get_object_or_404
from .models import Book, Author, BookInstance
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponseRedirect
from django.urls import reverse
from catalog.forms import RenewBookForm
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy

def index(request):
    """View function of home page."""

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_available = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count() #all() is implied by default.

    num_visits = request.session.get('num_visits', 0)
    num_visits += 1
    request.session['num_visits'] = num_visits

    context = {
        'num_books' : num_books,
        'num_instances' : num_instances,
        'num_instances_available' : num_instances_available,
        'num_authors' : num_authors,
        'num_visits' : num_visits,
    }

    return render(request, 'index.html', context=context)

class BookListView(generic.ListView):
    model = Book
    context_object_name = 'book_list'  #name for template
    queryset = Book.objects.all()
    template_name = 'book_list.html'
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book
    context_object_name = 'book_detail'
    template_name = 'book_detail.html'

class AuthorListView(generic.ListView):
    model = Author
    context_object_name = 'author_list'
    template_name = 'author_list.html'
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author
    context_object_name = 'author_detail'
    template_name = 'author_detail.html'

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """Generic class-based view listing books on loan to current user."""
    model = BookInstance
    template_name = 'bookinstance_list_borrowed_user.html'
    paginate_by = 10

    def get_queryset(self):
        return (
            BookInstance.objects.filter(borrower=self.request.user)
            .filter(status__exact='o')
            .order_by('due_back')
        )
    
class AllBorrowedBooksView(PermissionRequiredMixin, generic.ListView):
    model = BookInstance
    template_name = 'bookinstance_list_borrowed.html'
    paginate_by = 10
    permission_required = 'catalog.can_mark_returned'

    def get_queryset(self):
        return (
            BookInstance.objects
            .filter(status__exact='o')
            .order_by('due_back')
        )

@login_required
@permission_required('catalog.can_mark_returned', raise_exception=True)   
def renew_book_librarian(request, pk):
    book_instance = get_object_or_404(BookInstance, pk=pk)

    if request.method == 'POST':
        form = RenewBookForm(request.POST)

        if form.is_valid():
            book_instance.due_back = form.cleaned_data['renewal_date']
            book_instance.save()

            return HttpResponseRedirect(reverse('all-borrowed'))

    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date})

    context = {
        'form': form,
        'book_instance': book_instance,
    }

    return render(request, 'book_renew_librarian.html', context)

class AuthorCreate(PermissionRequiredMixin, CreateView):
    model = Author
    fields = ['first_name', 'last_name', 'date_of_birth', 'date_of_death']
    template_name = "author_form.html"
    permission_required = 'catalog.add_author'

class AuthorUpdate(PermissionRequiredMixin, UpdateView):
    model = Author
    fields = '__all__'  #May have security issues if more fields are added in future (Not recommended)
    permission_required = 'catalog.change_author'

class AuthorDelete(PermissionRequiredMixin, DeleteView):
    model = Author
    template_name = 'author_confirm_delete.html'
    success_url = reverse_lazy('authors')
    permission_required = 'catalog.delete_author'

    def form_valid(self, form):
        try:
            self.object.delete()
            return HttpResponseRedirect(self.success_url)

        except Exception as e:
            return HttpResponseRedirect(reverse("author-delete", kwargs={"pk": self.object.pk}))
        
class BookCreate(PermissionRequiredMixin, CreateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    template_name = 'book_form.html'
    permission_required = 'catalog.add_book'

class BookUpdate(PermissionRequiredMixin, UpdateView):
    model = Book
    fields = ['title', 'author', 'summary', 'isbn', 'genre', 'language']
    template_name = 'book_form.html'
    permission_required = 'catalog.change_book'

class BookDelete(PermissionRequiredMixin, DeleteView):
    model = Book
    template_name = 'book_confirm_delete.html'
    success_url = reverse_lazy('books')
    permission_required = 'catalog.delete_book'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.bookinstance_set.exists():
            # Prevent delete if book instances still exist
            return HttpResponseRedirect(self.object.get_absolute_url())
        return super().delete(request, *args, **kwargs)