from django.db import models

# Create your models here.

class Shoot(models.Model):
    photo = models.ImageField(upload_to = 'image')
    text = models.TextField(blank = True, null = True)

    def __str__(self):
        return f'Single snapshot with text {self.text}'

