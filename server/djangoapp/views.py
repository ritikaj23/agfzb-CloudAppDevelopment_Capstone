from django.shortcuts import render
from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
from .models import CarModel, CarDealer
from .restapis import get_dealer_from_cf, get_dealer_reviews_from_cf, get_dealer_by_id_from_cf, post_request
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
# def about(request):
# ...
def about(request):
    if request.method == "GET":
        return render(request, 'djangoapp/about.html')

# Create a `contact` view to return a static contact page
#def contact(request):
def contact(request):
    return render(request, "djangoapp/contact.html")
# Create a `login_request` view to handle sign in request
# def login_request(request):
def login_request(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            #messages.success(request, "Login successfully!")
            return redirect('djangoapp:index')
        else:
            messages.warning(request, "Invalid username or password.")
            return redirect("djangoapp:index")

# Create a `logout_request` view to handle sign out request
# def logout_request(request):
def logout_request(request):
    logout(request)
    return redirect('djangoapp:index')


# Create a `registration_request` view to handle sign up request
# def registration_request(request):
# ...
def registration_request(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/registration.html', context)
    elif request.method == "POST":
        #check if user exists 
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try: 
            User.objects.get(username=username)
            user_exist = True
        except: 
            logger.error("New User")
        if not user_exist:
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password)
            login(request, user)
            return redirect("djangoapp:index")
        else: 
            context['message'] = "User already exists."
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
def get_dealerships(request):
    if request.method == "GET":
        context = {}
        url = "https://us-south.functions.appdomain.cloud/api/v1/web/ddcdeeb5-bec2-481e-b506-af4fdbb68aa7/dealership-package/get-dealership"
        # Get dealers from the URL
        dealerships = get_dealers_from_cf(url)
        # Concat all dealer's short name
        context["dealership_list"] = dealerships
        # Return a list of dealer short name
        return render(request, 'djangoapp/index.html', context)


# Create a `get_dealer_details` view to render the reviews of a dealer
# def get_dealer_details(request, dealer_id):
# ...

def get_dealer_details(request, id):
    if request.method == "GET":
        dealer_url = "https://us-south.functions.appdomain.cloud/api/v1/web/ddcdeeb5-bec2-481e-b506-af4fdbb68aa7/dealership-package/get-dealership"
        dealer = get_dealer_by_id_from_cf(dealer_url, id)
        context = {}
        context["dealer"] = dealer
    
        review_url = "https://us-south.functions.appdomain.cloud/api/v1/web/ddcdeeb5-bec2-481e-b506-af4fdbb68aa7/dealership-package/get-review"
        reviews = get_dealer_reviews_from_cf(review_url, id)
        context["reviews"] = reviews
        
        return render(request, 'djangoapp/dealer_details.html', context)

# Create a `add_review` view to submit a review
# def add_review(request, dealer_id):
# ...
def add_review(request, dealer_id):
    context = {}
    dealer_url = "https://us-south.functions.appdomain.cloud/api/v1/web/ddcdeeb5-bec2-481e-b506-af4fdbb68aa7/dealership-package/get-dealership"
    dealer = get_dealer_by_id_from_cf(dealer_url, dealer_id=dealer_id)
    context["dealer"] = dealer 

    if request.method == "GET":
        cars = CarModel.objects.all()
        context["cars"] = cars
        return render(request, 'djangoapp/add_review.html', context)
    
    if request.method == "POST":
        if request.user.is_authenticated:
            username = request.user.username 
            car_id = request.POST["car"]
            car = CarModel.objects.get(pk=car_id)
        
            review = {}
            review["time"] = datetime.utcnow().isoformat()
            review["dealership"] = dealer_id
            review["review"] = request.POST["content"]
            review["name"] = username
            review["purchase"] = False
            review["car_make"] = ""
            review["car_model"] = ""
            review["car_year"] = 0
            review["purchase_date"] = "mm/dd/yy"
            review["id"] = dealer_id

            if "purchasecheck" in request.POST:
                if request.POST["purchasecheck"] == 'on':
                    review["purchase"] = True
                    review["car_make"] = car.car_make.name
                    review["car_model"] = car.name
                    review["car_year"] = int(car.year.strftime("%Y"))
                    review["purchase_date"] = request.POST["purchase_date"]
                    review["id"] = dealer_id
        
            json_payload = {}
            json_payload["review"] = review
            url = "https://us-south.functions.appdomain.cloud/api/v1/web/ddcdeeb5-bec2-481e-b506-af4fdbb68aa7/dealership-package/post_review"
            post_request(url, json_payload, dealer_id=dealer_id)
    return redirect("djangoapp:dealer_details", dealer_id=dealer_id)