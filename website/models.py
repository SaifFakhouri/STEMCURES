from django.db import models
from django.utils import timezone

class ContactSubmission(models.Model):
    """Model to store contact form submissions"""
    
    INTEREST_CHOICES = [
        ('volunteer', 'Volunteer'),
        ('donate', 'Donate'),
        ('partner', 'Partnership'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    interest = models.CharField(max_length=20, choices=INTEREST_CHOICES, blank=True)
    message = models.TextField()
    submitted_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Contact Submission'
        verbose_name_plural = 'Contact Submissions'
    
    def __str__(self):
        return f"{self.name} - {self.email} ({self.submitted_at.strftime('%Y-%m-%d')})"