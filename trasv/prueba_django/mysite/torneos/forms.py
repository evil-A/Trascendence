# coding=utf-8

from django import forms 
from django.utils.translation import gettext_lazy as _
from .models import Torneo

class TorneoForm(forms.Form):  
    nombre = forms.CharField(max_length=150, label=_('Tournament name'))
    comienzo_inscripcion = forms.DateTimeField(
        label=_('Start of registration'), 
        #widget=forms.widgets.DateInput(attrs={'type': 'datetime', 'placeholder': 'yyyy-mm-dd hh:mm', 'class': 'form-control'})
        widget=forms.TextInput(attrs={'type':'datetime-local'})
    )
    fin_inscripcion = forms.DateTimeField(
        label=_('End of registration'),
        # widget=forms.widgets.DateInput(attrs={'type': 'datetime', 'placeholder': 'yyyy-mm-dd hh:mm', 'class': 'form-control'})
        widget=forms.TextInput(attrs={'type':'datetime-local'})
    )
    comienzo_partidos = forms.DateTimeField(
        label=_('Start of matches'),
        # widget=forms.widgets.DateInput(attrs={'type': 'datetime', 'placeholder': 'yyyy-mm-dd hh:mm', 'class': 'form-control'})
        widget=forms.TextInput(attrs={'type':'datetime-local'})
    )
    minutos_duracion_maxima_partidos = forms.IntegerField(label=_('Maximum match duration in minutes'))
    minutos_entre_partidos = forms.IntegerField(label=_('Minutes between matches'))
    class Meta:  
        model = Torneo
