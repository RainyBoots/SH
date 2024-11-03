from django.db import transaction
from django.core.files.base import ContentFile
from .score_utils import create_envelope, sanitize_filename, manage_xml_operations, extract_instruments_from_musicxml, count_parts_and_update_score, calculate_page_count, get_instruments_and_part_counts, get_key, get_measures, calculate_file_hash
import os
from slugify import slugify
from unidecode import unidecode
from inflect import engine as inflect_engine
from django.core.files.base import ContentFile
from django.core.files import File
import tempfile
from django.conf import settings
from django.core.exceptions import ValidationError


class ScoreService:

    def __init__(self, score):
        self.score = score
        self.temp_dir = getattr(settings, 'TEMP_FILES_DIR', None)

    def get_temp_file(self):
        """Создает временный файл в указанной директории"""
        if self.temp_dir:
            os.makedirs(self.temp_dir, exist_ok=True)
            return tempfile.NamedTemporaryFile(
                dir=self.temp_dir,
                delete=False,
                suffix='.musicxml'
            )
        return tempfile.NamedTemporaryFile(delete=False, suffix='.musicxml')

    @transaction.atomic
    def process_new_score(self):
        """Полная обработка новой партитуры"""
        from .models import Score

        
        if not self.score.score:
            return

        with tempfile.NamedTemporaryFile(delete=False, suffix='.musicxml') as temp_file:
            for chunk in self.score.score.chunks():
                temp_file.write(chunk)
            temp_file.flush()
            
            try:
                file_hash = calculate_file_hash(temp_file)
                if Score.objects.filter(file_hash=file_hash).exists():
                    raise ValidationError('Эта партитура уже существует в базе данных')
                
                original_filename = os.path.basename(self.score.score.name)
                new_filename = sanitize_filename(original_filename)
                file_base_name = os.path.splitext(new_filename)[0]

                updates = {
                    'score.name': new_filename if new_filename != original_filename else original_filename,
                    'envelope_title': file_base_name,
                    'slug': self._generate_unique_slug(file_base_name),
                    'part_count': count_parts_and_update_score(temp_file.name),
                    'page_count': calculate_page_count(temp_file.name),
                    'key': get_key(temp_file.name),
                    "measures": get_measures(temp_file.name),
                    'file_hash': file_hash,
                }

                artist, title = self._process_artist_and_title(file_base_name)
                updates['artist'] = artist
                updates['title'] = title

                manage_xml_operations(temp_file.name, ["composer", "lyricist"])

                instrument_names = extract_instruments_from_musicxml(temp_file.name)
                instruments = self._get_or_create_instruments(instrument_names)

    
                if updates['part_count']:
                    ensemble_type_name = get_instruments_and_part_counts(temp_file.name, updates['part_count'])
                    if ensemble_type_name:
                        updates['ensemble_type'] = self._get_ensemble_type(ensemble_type_name)

                for key, value in updates.items():
                    setattr(self.score, key, value)

                if new_filename != original_filename:
                    with open(temp_file.name, 'rb') as f:
                        self.score.score.save(new_filename, File(f), save=False)


                self.score.save()
                self.score.instruments.clear()
                self.score.instruments.add(*instruments)

                envelope_svg = create_envelope(self.score)
                envelope_filename = f"envelope_{updates['slug']}.svg"
                envelope_file = ContentFile(envelope_svg.encode('utf-8'))


                self.score.envelope.save(envelope_filename, envelope_file, save=True)

            finally:

                try:
                    os.unlink(temp_file.name)
                except OSError:
                    pass

    def _get_or_create_instruments(self, instrument_names):
        """Получение или создание инструментов"""
        from .models import Instrument
        inflect = inflect_engine()
        instruments = []
        for name in instrument_names:
            if "bass" in name.lower():
                singular_name = name
            else:
                singular_name = inflect.singular_noun(name) or name
            instrument, _ = Instrument.objects.get_or_create(name=singular_name)
            instruments.append(instrument)
        return instruments

    def _generate_unique_slug(self, base_name):
        """Генерация уникального slug"""
        from .models import Score

        base_slug = slugify(unidecode(base_name))
        slug = base_slug
        counter = 1
        while Score.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def _process_artist_and_title(self, file_base_name):
        """Обработка артиста и названия"""
        from .models import Artist, Title
        if " — " in file_base_name:
            parts = file_base_name.split(" — ")
            artist_name = " — ".join(parts[1:]).strip()
            title_name = parts[0].strip()
            artist, _ = Artist.objects.get_or_create(name=artist_name)
            title, _ = Title.objects.get_or_create(name=title_name)
        else:
            title, _ = Title.objects.get_or_create(name=file_base_name)
            artist = None
        return artist, title

    def _get_ensemble_type(self, ensemble_type_name):
        """Получение типа ансамбля"""
        from .models import EnsembleType
        try:
            return EnsembleType.objects.get(name=ensemble_type_name)
        except EnsembleType.DoesNotExist:
            return None