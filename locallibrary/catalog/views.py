from django.shortcuts import render
from .models import Book, Author, BookInstance, Genre

def index(request):
    """View function of home page."""

    num_books = Book.objects.all().count()
    num_instances = BookInstance.objects.all().count()
    num_instances_availble = BookInstance.objects.filter(status__exact='a').count()
    num_authors = Author.objects.count()

    context = {
        'num_books' : num_books,
        'num_instances' : num_instances,
        'num_instances_available' : num_instances_availble,
        'num_authors' : num_authors,
    }

    return render(request, 'index.html', context=context)