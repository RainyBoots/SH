from django.db import models
from django.urls import reverse
from django.utils import timezone
from slugify import slugify
from unidecode import unidecode
from .services import ScoreService



class Title(models.Model):
    """
    Модель для названий
    """
    name = models.CharField(max_length=100, verbose_name='Имя')
    slug = models.SlugField(max_length=100, unique=True)


    class Meta:
        verbose_name = "Название произведения"


    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Artist(models.Model):
    """
    Модель для исполнителей
    """
    name = models.CharField(max_length=100, verbose_name='Имя')
    avatar = models.ImageField(upload_to='artists/avatars/', blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)


    class Meta:
        verbose_name_plural = "Исполнители"
        verbose_name = "Исполнитель"


    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Family_of_instruments(models.Model):
    """
    Модель для типов инструментов
    """
    name = models.CharField(max_length=100, verbose_name='Тип инструмента', blank=True, unique=True)
    name_ru = models.CharField(max_length=100, verbose_name='Тип инструмента (русский)', blank=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = "Тип инструмента"
        verbose_name_plural = "Типы инструментов"

    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Instrument(models.Model):
    """
    Модель для музыкальных инструментов
    """
    name = models.CharField(max_length=100, verbose_name='Инструмент', unique=True)
    name_ru = models.CharField(max_length=100, verbose_name='Инструмент (русский)', blank=True)
    avatar = models.ImageField(upload_to='instruments/avatars/', blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True)
    group = models.ForeignKey(Family_of_instruments, on_delete=models.CASCADE, related_name='instruments', null=True, blank=True, verbose_name='Тип инструмента')

    class Meta:
        verbose_name_plural = "Музыкальные инструменты"
        verbose_name = "Музыкальный инструмент"



    def save(self, *args, **kwargs) -> None:
        if not self.slug:
            base_slug = slugify(unidecode(self.name))
            slug = base_slug
            counter = 1
            while Instrument.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
        

    def __str__(self):
        return self.name


class EnsembleCategory(models.Model):
    """
    Модель для категорий ансамблей
    """
    name = models.CharField(max_length=100, verbose_name='Название категории', unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Категория ансамбля'
        verbose_name_plural = 'Категории ансамблей'

    def __str__(self):
        return self.name


class EnsembleType(models.Model):
    """
    Модель для типов ансамблей
    """
    name = models.CharField(max_length=100, verbose_name='Название типа ансамбля')
    category = models.ForeignKey(EnsembleCategory, on_delete=models.CASCADE, related_name='ensemble_types', blank=True, null=True, verbose_name='Категория ансамбля')
    slug = models.SlugField(unique=True)

    class Meta:
        verbose_name = 'Тип ансамбля'
        verbose_name_plural = 'Типы ансамблей'

    def __str__(self):
        return self.name


class Score(models.Model):
    """
    Модель для партитур
    """
    title = models.ForeignKey(Title, on_delete=models.CASCADE, max_length=100, related_name='scores', blank=True, verbose_name='Название')
    envelope_title = models.CharField(max_length=100, blank=True, verbose_name='Название обложки')
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, verbose_name='Исполнитель', related_name='scores', blank=True, null=True) 
    instruments = models.ManyToManyField(Instrument, through='ScoreInstrument', through_fields=('score', 'instrument'), related_name='scores', blank=True) 
    slug = models.SlugField(unique=True, blank=True, verbose_name='Слаг')
    publication_date = models.DateTimeField(auto_now_add=True, verbose_name='Дата публикации')
    ensemble_type = models.ForeignKey(EnsembleType, on_delete=models.CASCADE, blank=True, related_name='scores',verbose_name='Тип ансамбля', null=True)
    score = models.FileField(upload_to='scores/')
    envelope = models.FileField(upload_to='envelope/', blank=True)
    last_modified = models.DateTimeField(blank=True, null=True, verbose_name='Дата изменения')
    is_favorite = models.BooleanField(default=False, verbose_name='Избранное')
    part_count = models.PositiveIntegerField(default=0, verbose_name='Количество партий', blank=True, null=True)
    page_count = models.PositiveIntegerField(default=0, verbose_name='Количество страниц', blank=True)
    key = models.CharField(max_length=100, blank=True, verbose_name='Тональность')
    measures = models.PositiveBigIntegerField(default=0, verbose_name='Количество тактов', blank=True, null=True)
    file_hash = models.CharField(max_length=64, unique=True, blank=True, verbose_name='Хэш файла')


    class Meta:
        verbose_name_plural = "Scores"
        verbose_name = "Score"
        ordering = ['-publication_date']
        indexes = [
            models.Index(fields=['publication_date']),
            models.Index(fields=['slug']),
        ]


    def save(self, *args, **kwargs):
        if not getattr(self, '_is_processing', False):
            self._is_processing = True  

            try:
                is_new = self.pk is None


                if not is_new:  
                    self.last_modified = timezone.now()
                
                if is_new and self.score:
                    score_service = ScoreService(self)
                    score_service.process_new_score()
                else:
                    super().save(*args, **kwargs)
            finally:
                del self._is_processing  
        else:
            super().save(*args, **kwargs)  
    
    
    def __str__(self):
         return f"Партитура: {self.envelope_title}"

    def get_absolute_url(self):
        return reverse('score_detail', args=[self.pk])
    
class ScoreInstrument(models.Model):
    """
    Промежуточная модель для связи Score и Instrument с дополнительными полями
    """
    score = models.ForeignKey(Score, on_delete=models.CASCADE)
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Инструмент в партитуре'
        verbose_name_plural = 'Инструменты в партитурах'
        unique_together = ['score', 'instrument']

    def __str__(self):
        return f"{self.score.envelope_title} - {self.instrument.name}"
