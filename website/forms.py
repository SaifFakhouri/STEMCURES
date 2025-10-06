from django import forms
from .models import ContactSubmission

class ContactForm(forms.ModelForm):
    """Form for contact submissions with validation"""
    
    class Meta:
        model = ContactSubmission
        fields = ['name', 'email', 'interest', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'name',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'email',
                'required': True
            }),
            'interest': forms.Select(attrs={
                'class': 'form-control',
                'id': 'interest'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'message',
                'rows': 4,
                'placeholder': 'Tell us more about your interest in STEM CURES...'
            }),
        }
        labels = {
            'name': 'Full Name',
            'email': 'Email Address',
            'interest': 'How would you like to help?',
            'message': 'Message'
        }
    
    def clean_email(self):
        """Validate email format"""
        email = self.cleaned_data.get('email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_name(self):
        """Clean and validate name"""
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError("Please enter a valid name.")
        return name
