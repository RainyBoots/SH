from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from Score.views import *






urlpatterns = [
    path('', ScoreCatalogView.as_view(), name='score_catalog'),
    path('instrument/<int:pk>/', InstrumentScoreView.as_view(), name='instrument_scores'),
    path('score/<int:pk>/', ScoreDetailView.as_view(), name='score_detail'),
    path('<int:score_id>/toggle-favorite/', ToggleFavoriteView.as_view(), name='toggle_favorite'),
    path('upload/', ScoreUploadView.as_view(), name='score_upload'),
    path('favorite-scores/', FavoriteScoresListView.as_view(), name='favorite_scores'),
    path('score/<int:pk>/update/', ScoreUpdateView.as_view(), name='score_update'),
    path('score/<int:pk>/delete/', ScoreDeleteView.as_view(), name='score_delete'),
    path('title/<int:pk>/', TitleDetailView.as_view(), name='title_detail'),
    path('artist/<int:pk>/', ArtistListView.as_view(), name='artist_detail'),
    path('solo-piano/', SoloPianoScoresView.as_view(), name='solo_piano_scores'),
    path('ensemble-type/<int:ensemble_type_id>/', EnsembleTypeDetailView.as_view(), name='ensemble_type_detail'),
    path('/solo-guitar/', SoloGuitarScoresView.as_view(), name='solo_guitar_scores'),
    path('recent-scores/', RecentScoresView.as_view(), name='recent_scores'),  
    path('instruments/', InstrumentListView.as_view(), name='instrument_list'),
    path('instruments/add_family/<int:instrument_id>/', AddFamilyToInstrumentView.as_view(), name='add_family_to_instrument'),
    path('ensemble', EnsembleTypeListView.as_view(), name='ensemble_list'),
    path('ensemble/add_category/<int:ensemble_type_id>/', AddCategoryToEnsembleTypeView.as_view(), name='add_category_to_ensemble_type'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)