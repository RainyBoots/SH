from django.core.management.base import BaseCommand
from Score.models import Family_of_instruments, Instrument
from django.utils.text import slugify
from unidecode import unidecode

class Command(BaseCommand):
    help = 'Добавление инструментов в базу данных'

    def handle(self, *args, **options):
        family = {"Bowed string": ["Octobass", "Fiddle", "Strings", "Viol", "Erhu", "Baryton", "Nyckelharpa", "Cello", "Viola", "Violin", "Contrabass"]}
        for family_name, instruments in family.items():
            family, created = Family_of_instruments.objects.get_or_create(
                name=family_name, 
                defaults={'name_ru': f"{family_name} (русский)"})  
            

            for instrument_name in instruments:
                instrument_slug = slugify(unidecode(instrument_name))
                Instrument.objects.get_or_create(
                    name=instrument_name,
                    defaults={
                        'name_ru': f"{instrument_name} (русский)",  
                        'slug': instrument_slug,
                        'group': family
                    }
                )
        
        self.stdout.write(self.style.SUCCESS('Инструменты успешно добавлены в базу данных.'))