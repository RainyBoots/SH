from django.contrib import admin
from .models import Score, Artist, Instrument, Family_of_instruments, Title, ScoreInstrument, EnsembleType, EnsembleCategory

class ScoreInstrumentInline(admin.TabularInline):
    model = ScoreInstrument
    extra = 1
    fields = ['instrument',]

    can_delete = True  
    show_change_link = True  
    verbose_name = "Инструмент"
    verbose_name_plural = "Инструменты"


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ('title',)
    search_fields = ('name',)
    inlines = [ScoreInstrumentInline]

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Family_of_instruments)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name_ru',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(ScoreInstrument)
class ScoreInstrumentAdmin(admin.ModelAdmin):
    list_display = ['score', 'instrument']
    list_filter = ['instrument']
    search_fields = ['score__title', 'instrument__name']



@admin.register(EnsembleCategory)
class EnsembleCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(EnsembleType)
class EnsembleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug')
    list_filter = ('category',)
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)