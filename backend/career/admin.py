from django.contrib import admin
from .models import CareerProfile, Skill, UserSkill

admin.site.register(CareerProfile)
admin.site.register(Skill)
admin.site.register(UserSkill)