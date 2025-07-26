from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Theater, Seat, Booking
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count  

# Movie list view
def movie_list(request):
    search_query = request.GET.get('search')
    if search_query:
        movies = Movie.objects.filter(name__icontains=search_query)
    else:
        movies = Movie.objects.all()
    return render(request, 'movies/movie_list.html', {'movies': movies})

# Theater list view
def theater_list(request, movie_id):
    movie = get_object_or_404(Movie, id=movie_id)
    theaters = Theater.objects.filter(movie=movie)
    for theater in theaters:
        total_seats = theater.seats.count()
        booked_seats = theater.seats.filter(is_booked=True).count()
        theater.is_full = (booked_seats == total_seats)

    return render(request, 'movies/theater_list.html', {'movie': movie, 'theaters': theaters})

# Book seats view
@login_required(login_url='/login/')
def book_seats(request, theater_id):
    theaters = get_object_or_404(Theater, id=theater_id)
    seats = Seat.objects.filter(theater=theaters)

    if request.method == 'POST':
        selected_Seats = request.POST.getlist('seats')
        error_seats = []

        if not selected_Seats:
            return render(request, "movies/seat_selection.html", {
                'theater': theaters,
                "seats": seats,
                'error': "No seat selected"
            })

        booked_seat_numbers = []

        for seat_id in selected_Seats:
            seat = get_object_or_404(Seat, id=seat_id, theater=theaters)
            if seat.is_booked:
                error_seats.append(seat.seat_number)
                continue

            try:
                Booking.objects.create(
                    user=request.user,
                    seat=seat,
                    movie=theaters.movie,
                    theater=theaters
                )
                seat.is_booked = True
                seat.save()
                booked_seat_numbers.append(seat.seat_number)
            except IntegrityError:
                error_seats.append(seat.seat_number)

        if error_seats:
            error_messsage = f"The following seats are already booked: {', '.join(error_seats)}"
            return render(request, 'movies/seat_selection.html', {
                'theater': theaters,
                "seats": seats,
                'error': error_messsage
            })

        # Send booking confirmation email
        subject = 'Booking Confirmation - BookMySeat'
        message = (
            f"Hi {request.user.username},\n\n"
            f"Your booking was successful!\n\n"
            f"Movie: {theaters.movie.name}\n"
            f"Theater: {theaters.name}\n"
            f"Seats: {', '.join(booked_seat_numbers)}\n\n"
            f"Thank you for booking with us!\n"
            f"BookMySeat Team"
        )
        recipient_list = [request.user.email]
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list, fail_silently=False)

        return redirect('profile')

    return render(request, 'movies/seat_selection.html', {'theater': theaters, "seats": seats})

# Admin dashboard view
@staff_member_required
def admin_dashboard(request):
    total_revenue = Booking.objects.count() * 200  # Assuming fixed price
    total_bookings = Booking.objects.count()

    most_popular_movies = (
        Movie.objects.annotate(num_bookings=Count('theaters__seats__booking'))
        .order_by('-num_bookings')[:5]
    )

    busiest_theaters = (
        Theater.objects.annotate(num_bookings=Count('seats__booking'))
        .order_by('-num_bookings')[:5]
    )

    return render(request, 'dashboard/admin_dashboard.html', {
        'total_revenue': total_revenue,
        'total_bookings': total_bookings,
        'most_popular_movies': most_popular_movies,
        'busiest_theaters': busiest_theaters,
    })
