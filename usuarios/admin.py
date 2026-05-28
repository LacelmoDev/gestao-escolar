from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

try:
    admin.site.unregister(Usuario)
except admin.sites.NotRegistered:
    pass

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informações Académicas', {'fields': ('is_aluno', 'is_professor', 'is_admin_escola', 'bi_numero')}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_aluno', 'is_professor', 'is_staff']

admin.site.register(Usuario, CustomUserAdmin)