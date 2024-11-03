from django import forms
from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView, DetailView, CreateView
from django.views.generic.edit import UpdateView, DeleteView
from django.db.models import Count, Q, Prefetch
from .models import Score, Instrument, EnsembleType, EnsembleCategory, Family_of_instruments, Title, Artist
from .forms import ScoreUploadForm, ScoreUpdateForm
from .services import ScoreService
from .score_utils import count_parts_and_update_score, calculate_page_count, get_key, get_measures
from django.urls import reverse_lazy, reverse
from django.contrib import messages
import tempfile
import os






class HomeView(View):
    def get(self, request, *args, **kwargs):
        total_instruments = Instrument.objects.filter(group__isnull=True).count()  
        recent_scores = Score.objects.order_by('-last_modified') 
        recent_scores_count = recent_scores.count()
        new_scores=Score.objects.order_by('-publication_date')[:8]
        total_ensemble_types_without_category = EnsembleType.objects.filter(category=None).exclude(name='Solo').count()
        total_Scores = Score.objects.all().count()

        context = {
            'total_instruments': total_instruments,
            'recent_scores': recent_scores,
            'recent_scores_count': recent_scores_count,
            'new_scores' : new_scores, 
            'total_ensemble_types_without_category': total_ensemble_types_without_category,
            'total_Scores': total_Scores
        }
        
        return render(request, 'home.html', context)






class ScoreCatalogView(ListView):
    template_name = 'Score/score_catalog.html'
    context_object_name = 'scores'
    paginate_by = 20

    def get_queryset(self):
        queryset = Score.objects.all()

        ensemble_types = self.request.GET.getlist('ensemble_type')
        instruments = self.request.GET.getlist('instrument')
        search_query = self.request.GET.get('search')

        if ensemble_types:
            ensemble_types = [id for id in ensemble_types if id]
            if ensemble_types:
                queryset = queryset.filter(ensemble_type__in=ensemble_types)

        if instruments:
            instruments = [id for id in instruments if id]
            if instruments:
                for instrument_id in instruments:
                    if instrument_id:  
                        queryset = queryset.filter(instruments=instrument_id)

        if search_query:
            queryset = queryset.filter(
                Q(title__name__icontains=search_query) |
                Q(envelope_title__icontains=search_query) |
                Q(artist__name__icontains=search_query)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_h1'] = self.get_title_h1()
        context['title_page'] = self.get_title_page()

        selected_ensemble_types = self.request.GET.getlist('ensemble_type')
        selected_instruments = self.request.GET.getlist('instrument')
        search_query = self.request.GET.get('search')

        current_scores = self.get_queryset()

        available_ensemble_types = EnsembleType.objects.filter(
            scores__in=current_scores
        ).annotate(
            score_count=Count('scores', distinct=True)
        ).distinct()

        available_instruments = Instrument.objects.filter(
            scores__in=current_scores
        ).annotate(
            score_count=Count('scores', distinct=True)
        ).distinct()

        uncategorized_ensemble_types = available_ensemble_types.filter(category__isnull=True)

        categories = EnsembleCategory.objects.filter(
            ensemble_types__in=available_ensemble_types
        ).prefetch_related(
            Prefetch('ensemble_types', queryset=available_ensemble_types)
        ).annotate(
            ensemble_type_count=Count('ensemble_types', distinct=True)
        ).distinct()

        families = Family_of_instruments.objects.filter(
            instruments__in=available_instruments
        ).prefetch_related(
            Prefetch('instruments', queryset=available_instruments)
        ).annotate(
            instrument_count=Count('instruments', distinct=True)
        ).distinct()

        context.update({
            'categories': categories,
            'families': families,
            'selected_ensemble_types': selected_ensemble_types,
            'selected_instruments': selected_instruments,
            'search_query': search_query,
            'available_ensemble_types': available_ensemble_types,
            'available_instruments': available_instruments,
            'uncategorized_ensemble_types': uncategorized_ensemble_types,
        })

        return context

    def get_title_h1(self):
        ensemble_type_id = self.request.GET.get('ensemble_type')
        instrument_id = self.request.GET.get('instrument')
        search_query = self.request.GET.get('search')

        if ensemble_type_id:
            ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
            
            if ensemble_type.name == "Solo" and instrument_id:
                instrument = get_object_or_404(Instrument, id=instrument_id)
                return f"Партитура для Solo {instrument.name}"
            return f"Партитура для {ensemble_type.name}"
        elif search_query:
            return f"Результаты поиска: '{search_query}'"
        else:
            return "Каталог партитур"

    def get_title_page(self):
        ensemble_type_id = self.request.GET.get('ensemble_type')
        instrument_id = self.request.GET.get('instrument')
        search_query = self.request.GET.get('search')

        if ensemble_type_id:
            ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
            
            if ensemble_type.name == "Solo" and instrument_id:
                instrument = get_object_or_404(Instrument, id=instrument_id)
                return f"Партитура для Solo {instrument.name}"
            return f"Партитура для {ensemble_type.name}"
        elif search_query:
            return f"Результаты поиска: '{search_query}'"
        else:
            return "Каталог партитур"

    def get(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        context = self.get_context_data()

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, self.template_name, context)

        return super().get(request, *args, **kwargs)

class RecentScoresView(ScoreCatalogView):
    model = Score
    template_name = 'Score/score_catalog.html' 
    context_object_name = 'scores'

    def get_queryset(self):
        return Score.objects.order_by('-last_modified')   # только последние 10 оценок

    def get_title_page(self):
        return "Последние изминения"
    def get_title_h1(self):
        return "Последние изминения"	

class InstrumentScoreView(ScoreCatalogView):
    def get(self, request, *args, **kwargs):
        instrument_id = self.kwargs.get('pk')
        if instrument_id:
            self.instrument = get_object_or_404(Instrument, id=instrument_id)
            self.object_list = self.get_queryset()  
        else:
            self.object_list = self.get_queryset()

        context = self.get_context_data()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return render(request, self.template_name, context)
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(instruments=self.instrument)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title_h1'] = self.get_title_h1()
        context['title_page'] = self.get_title_page()
        return context

    def get_title_h1(self):
        return f"Партитуры для {self.instrument.name}"

    def get_title_page(self):
        return f"Партитуры - {self.instrument.name}"
       

class EnsembleTypeDetailView(ScoreCatalogView):
    def get(self, request, *args, **kwargs):
        ensemble_type_id = self.kwargs.get('ensemble_type_id')
        instrument_id = self.request.GET.get('instrument')
        
        ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
        
        base_url = reverse('score_catalog')
        
        if ensemble_type.name == "Solo" and instrument_id:
            redirect_url = f"{base_url}?ensemble_type={ensemble_type_id}&instrument={instrument_id}"
        else:
            redirect_url = f"{base_url}?ensemble_type={ensemble_type_id}"
        
        return redirect(redirect_url)

    def get_title_h1(self):
        ensemble_type_id = self.request.GET.get('ensemble_type')
        instrument_id = self.request.GET.get('instrument')

        if not ensemble_type_id:
            return super().get_title_h1()

        ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
        
        if ensemble_type.name == "Solo" and instrument_id:
            instrument = get_object_or_404(Instrument, id=instrument_id)
            return f"Партитура для Solo {instrument.name}"
        return f"Партитура для {ensemble_type.name}"

    def get_title_page(self):
        ensemble_type_id = self.request.GET.get('ensemble_type')
        instrument_id = self.request.GET.get('instrument')

        if not ensemble_type_id:
            return super().get_title_page()

        ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
        
        if ensemble_type.name == "Solo" and instrument_id:
            instrument = get_object_or_404(Instrument, id=instrument_id)
            return f"Партитура для Solo {instrument.name}"
        return f"Партитура для {ensemble_type.name}"



class ScoreDetailView(DetailView):
    model = Score
    template_name = 'Score/score_detail.html'
    context_object_name = 'score'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        score = self.object
        context['score_file_url'] = score.score.url if score.score else ''
        return context




@method_decorator(csrf_exempt, name='dispatch')
class ToggleFavoriteView(View):
    def post(self, request, score_id):
        score = get_object_or_404(Score, id=score_id)
        score.is_favorite = not score.is_favorite
        score.save()
        return JsonResponse({
            'is_favorite': score.is_favorite,
            'message': 'Добавлено в избранное' if score.is_favorite else 'Удалено из избранного'
        })


class ScoreUploadView(CreateView):
    model = Score
    form_class = ScoreUploadForm
    template_name = 'Score/upload_score.html'
    success_url = reverse_lazy('score_catalog')

    def post(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            uploaded_file = request.FILES.get('score')
            if not uploaded_file:
                return JsonResponse({'error': 'No file uploaded'}, status=400)

            existing_score = Score.objects.filter(score=uploaded_file.name).first()
            if existing_score:
                return JsonResponse({
                    'error': 'Партитура с таким именем уже существует в базе данных.'
                }, status=400)  

            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.musicxml') as temp_file:
                    for chunk in uploaded_file.chunks():
                        temp_file.write(chunk)
                    temp_file.flush()

                    temp_score = Score(score=uploaded_file)
                    score_service = ScoreService(temp_score)
                    
                    preview_data = {
                        'envelope_title': os.path.splitext(uploaded_file.name)[0],
                        'part_count': count_parts_and_update_score(temp_file.name),
                        'page_count': calculate_page_count(temp_file.name),
                        'key': get_key(temp_file.name),
                        'measures': get_measures(temp_file.name),
                    }

                    return JsonResponse(preview_data)

            except Exception as e:
                return JsonResponse({
                    'error': f'Ошибка при обработке файла: {str(e)}'
                }, status=500)  

        return super().post(request, *args, **kwargs)


class FavoriteScoresListView(ScoreCatalogView):
    def get_queryset(self):
        queryset = Score.objects.filter(is_favorite=True)

        ensemble_types = self.request.GET.getlist('ensemble_type')
        instruments = self.request.GET.getlist('instrument')
        search_query = self.request.GET.get('search')

        if ensemble_types:
            queryset = queryset.filter(ensemble_type__in=ensemble_types)
        if instruments:
            for instrument_id in instruments:
                queryset = queryset.filter(instruments=instrument_id)
        if search_query:
            queryset = queryset.filter(
                Q(title__name__icontains=search_query) |
                Q(envelope_title__icontains=search_query) |
                Q(artist__name__icontains=search_query)
            )

        return queryset

    def get_title_h1(self):
        return 'Избранные партитуры'

    def get_title_page(self):
        return 'Избранные партитуры'


class ScoreUpdateView(UpdateView):
    model = Score
    form_class = ScoreUpdateForm
    template_name = 'Score/update_score.html'
    context_object_name = 'score'

    def get_success_url(self):
        return reverse('score_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        try:
            old_score = self.object.score
            old_envelope = self.object.envelope


            self.object = form.save(commit=False)

            score_service = ScoreService(self.object)
            score_service.process_new_score()

            messages.success(self.request, 'Партитура успешно обновлена')

            return JsonResponse({
                'status': 'success',
                'redirect_url': self.get_success_url()
            })

        except Exception as e:
            self.object.score = old_score
            self.object.envelope = old_envelope
            self.object.save()


            return JsonResponse({
                'status': 'error',
                'message': f'Ошибка при обновлении партитуры: {str(e)}'
            })


class ScoreDeleteView(DeleteView):
    model = Score
    success_url = reverse_lazy('score_catalog')

    def delete(self, request, *args, **kwargs):
        success_url = self.success_url
        self.object = self.get_object()
        if self.object.score:
            self.object.score.delete()
        if self.object.envelope:
            self.object.envelope.delete()
        self.object.delete()
        return HttpResponseRedirect(success_url)


class TitleDetailView(ScoreCatalogView):
    def get_queryset(self):
        self.title = get_object_or_404(Title, pk=self.kwargs['pk'])
        queryset = Score.objects.filter(title=self.title)

        ensemble_types = self.request.GET.getlist('ensemble_type')
        instruments = self.request.GET.getlist('instrument')
        search_query = self.request.GET.get('search')

        if ensemble_types:
            queryset = queryset.filter(ensemble_type__in=ensemble_types)
        if instruments:
            for instrument_id in instruments:
                queryset = queryset.filter(instruments=instrument_id)
        if search_query:
            queryset = queryset.filter(
                Q(envelope_title__icontains=search_query) |
                Q(artist__name__icontains=search_query)
            )

        return queryset

    def get_title_h1(self):
        return f"Партитура: {self.title.name}"

    def get_title_page(self):
        return f"Партитуры : {self.title.name}"


class ArtistListView(ScoreCatalogView):
    def get_queryset(self):
        self.artist = get_object_or_404(Artist, pk=self.kwargs['pk'])
        queryset = Score.objects.filter(artist=self.artist)

        ensemble_types = self.request.GET.getlist('ensemble_type')
        instruments = self.request.GET.getlist('instrument')
        search_query = self.request.GET.get('search')

        if ensemble_types:
            queryset = queryset.filter(ensemble_type__in=ensemble_types)
        if instruments:
            for instrument_id in instruments:
                queryset = queryset.filter(instruments=instrument_id)
        if search_query:
            queryset = queryset.filter(
                Q(title__name__icontains=search_query) |
                Q(envelope_title__icontains=search_query)
            )

        return queryset

    def get_title_h1(self):
        return f"Партитуры артиста: {self.artist.name}"

    def get_title_page(self):
        return f"Партитуры артиста: {self.artist.name}"



class SoloPianoScoresView(ScoreCatalogView):
    def get(self, request, *args, **kwargs):
        solo_id = EnsembleType.objects.get(name='Solo').id
        piano_id = Instrument.objects.get(name='Piano').id

        base_url = reverse('score_catalog')
        redirect_url = f"{base_url}?ensemble_type={solo_id}&instrument={piano_id}"
        
        return redirect(redirect_url)


class SoloGuitarScoresView(ScoreCatalogView):
    def get(self, request, *args, **kwargs):
        # Получаем ID для Solo и Guitar
        solo_id = EnsembleType.objects.get(name='Solo').id
        guitar_id = Instrument.objects.get(name='Guitar').id
        
        # Формируем URL с параметрами
        base_url = reverse('score_catalog')
        redirect_url = f"{base_url}?ensemble_type={solo_id}&instrument={guitar_id}"
        
        return redirect(redirect_url)
    

class InstrumentListView(ListView):
    model = Instrument
    template_name = 'Score/instrument_list.html'
    
    def get_queryset(self):
        return Instrument.objects.filter(group__isnull=True)

class EnsembleTypeListView(ListView):
    model = EnsembleType
    template_name = 'Score/ensemble_type_list.html'
    
    def get_queryset(self):
        return EnsembleType.objects.filter(category__isnull=True).exclude(name='Solo')
    
class EnsembleCategorySelectionForm(forms.Form):
    category_id = forms.ModelChoiceField(queryset=EnsembleCategory.objects.all(), empty_label="Выберите категорию")

class FamilySelectionForm(forms.Form):
    family_id = forms.ModelChoiceField(queryset=Family_of_instruments.objects.all(), empty_label="Выберите семью")

class AddFamilyToInstrumentView(View):
    template_name = 'Score/add_family.html'
    
    def get(self, request, instrument_id):
        instrument = get_object_or_404(Instrument, id=instrument_id)
        form = FamilySelectionForm()  
        families = Family_of_instruments.objects.all()
        return render(request, self.template_name, {
            'instrument': instrument,
            'form': form,
            'families': families
        })
    
    def post(self, request, instrument_id):
        instrument = get_object_or_404(Instrument, id=instrument_id)
        form = FamilySelectionForm(request.POST)
        if form.is_valid():
            family = form.cleaned_data['family_id']
            instrument.group = family
            instrument.save()
            return redirect('instrument_list')
        families = Family_of_instruments.objects.all()
        return render(request, self.template_name, {
            'instrument': instrument,
            'form': form,
            'families': families
        })
    
class AddCategoryToEnsembleTypeView(View):
    template_name = 'Score/add_category.html'
    
    def get(self, request, ensemble_type_id):
        ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
        form = EnsembleCategorySelectionForm()  # Создаем новую форму
        categories = EnsembleCategory.objects.all()
        return render(request, self.template_name, {
            'ensemble_type': ensemble_type,
            'form': form,
            'categories': categories
        })
    
    def post(self, request, ensemble_type_id):
        ensemble_type = get_object_or_404(EnsembleType, id=ensemble_type_id)
        form = EnsembleCategorySelectionForm(request.POST)
        if form.is_valid():
            category = form.cleaned_data['category_id']
            ensemble_type.category = category
            ensemble_type.save()
            return redirect('ensemble_type_list')
        categories = EnsembleCategory.objects.all() 
        return render(request, self.template_name, {
            'ensemble_type': ensemble_type,
            'form': form,
            'categories': categories    
        })
