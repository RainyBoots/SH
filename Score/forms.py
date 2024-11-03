from django import forms
from .models import Score
import os


class ScoreUploadForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['score', 'envelope_title', 'key', 'part_count', 'page_count', 'measures']
        widgets = {
            'score': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.musicxml,.xml',
                'id': 'scoreUpload'
            }),
            'envelope_title': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'key': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'part_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'page_count': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            }),
            'measures': forms.NumberInput(attrs={
                'class': 'form-control',
                'readonly': True
            })
        }

class ScoreUpdateForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = ['score']
    def clean_score(self):
        score = self.cleaned_data.get('score')
        if score:
            valid_extensions = ['.musicxml', '.xml']
            ext = os.path.splitext(score.name)[1].lower()
            if ext not in valid_extensions:
                raise forms.ValidationError('Неподдерживаемый формат файла. Используйте .musicxml или .xml')
        return score
    
