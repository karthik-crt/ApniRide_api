from django.contrib import admin
from .models import DistanceReward, TourismOffer

@admin.register(DistanceReward)
class DistanceRewardAdmin(admin.ModelAdmin):
    list_display = ("min_distance", "max_distance", "cashback", "water_bottles", "tea", "discount")
    list_editable = ("cashback", "water_bottles", "tea", "discount")

@admin.register(TourismOffer)
class TourismOfferAdmin(admin.ModelAdmin):
    list_display = ("name", "discount", "tea", "water_bottles", "long_term_days")
    list_editable = ("discount", "tea", "water_bottles", "long_term_days")
  