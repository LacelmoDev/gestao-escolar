from django import forms
from django.utils import timezone
from .models import Inscricao
from usuarios.models import Usuario

class InscricaoForm(forms.ModelForm):
    class Meta:
        model = Inscricao
        exclude = ['status', 'observacoes_adm', 'comprovativo_pagamento']
        widgets = {
            'data_nascimento': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean_data_nascimento(self):
        data = self.cleaned_data.get('data_nascimento')
        if data:
            ano_atual = timezone.now().year
            if data.year > ano_atual:
                raise forms.ValidationError("A data de nascimento não pode ser no futuro.")
            if data.year < 1950:
                raise forms.ValidationError("Ano de nascimento inválido. Deve ser após 1950.")
            if (timezone.now().date() - data).days < 365 * 4:
                raise forms.ValidationError("Idade mínima para inscrição é de 4 anos.")
        return data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-3 border border-gray-200 rounded-2xl focus:outline-none focus:ring-2 focus:ring-tarimba bg-white text-sm transition-all duration-300'
            })
            
class PerfilAlunoForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['email'] 
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full px-3 py-2 border border-gray-200 rounded-md focus:outline-none focus:ring-1 focus:ring-black'}),
        }