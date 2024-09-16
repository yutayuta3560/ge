from django.db import models
from django.contrib.auth.models import User


class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Balance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    investment = models.DecimalField(max_digits=10, decimal_places=2)
    payout = models.DecimalField(max_digits=10, decimal_places=2)
    profit = models.DecimalField(max_digits=10, decimal_places=2, editable=False, null=True)
    comment = models.TextField(null=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.created_at}"

    def save(self, *args, **kwargs):
        self.profit = float(self.payout) - float(self.investment)
        super().save(*args, **kwargs)
