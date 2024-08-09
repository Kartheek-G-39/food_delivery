from django import forms
from django.contrib.auth.forms import UserCreationForm,PasswordChangeForm
from .models import CustomUser, Restaurant, Customer, DeliveryBoy, MenuItem,CartItem,Order,OrderItem

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                self.fields[field_name].label_suffix = ' *'
                self.fields[field_name].widget.attrs.update({'class': 'required'})
                self.fields[field_name].label_attrs = {'class': 'required'}

    class Meta:
        model = CustomUser
        fields = ['username','first_name','last_name', 'email', 'password1', 'password2']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name']

class RestaurantRegistrationForm(forms.ModelForm):
    latitude = forms.FloatField(widget=forms.HiddenInput())
    longitude = forms.FloatField(widget=forms.HiddenInput())
    image = forms.ImageField(label='Please Take Entrance Picture of your Restaurant',required=True)
    def __init__(self, *args, **kwargs):
        super(RestaurantRegistrationForm, self).__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs['class'] = 'required'

    class Meta:
        model = Restaurant
        fields = ['name', 'code', 'address', 'phone_number', 'city', 'cuisine', 'latitude', 'longitude', 'image']
        labels = {
            'name': 'Restaurant Name',
            'address': 'Restaurant Address',
            'phone_number': 'Phone Number',
        }


class CustomerRegistrationForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['address', 'phone_number']

class DeliveryBoyRegistrationForm(forms.ModelForm):
    class Meta:
        model = DeliveryBoy
        fields = ['phone_number', 'vehicle_number']

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['menu', 'item', 'price', 'veg_or_non_veg']
    def __init__(self, *args, **kwargs):
        restaurant = kwargs.pop('restaurant', None)
        super(MenuItemForm, self).__init__(*args, **kwargs)
        if restaurant:
            self.fields['menu'].queryset = restaurant.menus.all()

class CartItemForm(forms.ModelForm):
    class Meta:
        model = CartItem
        fields = ['menu_item', 'quantity']

class OrderForm(forms.ModelForm):
    scheduled_time = forms.DateTimeField(required=False, widget=forms.TextInput(attrs={'type': 'datetime-local'}))

    class Meta:
        model = Order
        fields = ['delivery_address', 'scheduled_time']


class OrderItemFeedbackForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['rating', 'feedback']
        widgets = {
            'rating': forms.RadioSelect(choices=[(i, i) for i in range(6)]),
            'feedback': forms.Textarea(attrs={'rows': 3}),
        }


class OrderSearchForm(forms.Form):
    q = forms.CharField(required=False, label='Search')
    start_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    end_date = forms.DateField(required=False, widget=forms.TextInput(attrs={'type': 'date'}))
    FILTER_CHOICES = [
        ('', '--- Filter by ---'),
        ('last_week', 'Last Week'),
        ('last_month', 'Last Month')
    ]
    filter_by = forms.ChoiceField(choices=FILTER_CHOICES, required=False)