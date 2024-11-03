from django.core.management.base import BaseCommand
from Score.models import Family_of_instruments

 


class Command(BaseCommand):
    help = 'Выводит все типы инструментов с связанными инструментами в виде списка словарей'

    def handle(self, *args, **kwargs):
        families = Family_of_instruments.objects.prefetch_related('instruments').all()
        result = []

        for family in families:
            family_data = {
                'family_name': family.name,
                'instruments': []
            }

            instruments = family.instruments.all()
            for instrument in instruments:
                family_data['instruments'].append({
                    'instrument_name': instrument.name,
                    'instrument_id': instrument.id,  
                })

            result.append(family_data)

        self.stdout.write(str(result))