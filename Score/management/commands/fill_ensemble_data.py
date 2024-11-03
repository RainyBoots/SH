from django.core.management.base import BaseCommand
from  Score.models import EnsembleCategory, EnsembleType
from django.utils.text import slugify
from unidecode import unidecode

class Command(BaseCommand):
    help = 'Заполняет модели ансамблей данными'

    def handle(self, *args, **kwargs):
        Ensembles = {"String Ensembles": ["String Duet", "String Trio", "String Quartet", "String Quintet", "String Ensemble", "String Sextet"]}

        for category_name, types in Ensembles.items():
            category, created = EnsembleCategory.objects.get_or_create(
                name=category_name,
                slug= slugify(unidecode(category_name))
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Категория "{category_name}" создана.'))
            else:
                self.stdout.write(self.style.WARNING(f'Категория "{category_name}" уже существует.'))

            for type_name in types:
                type_slug = slugify(unidecode(type_name))

                EnsembleType.objects.get_or_create(
                    name=type_name,
                    category=category,
                    slug=type_slug
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Тип ансамбля "{type_name}" создан.'))
                else:
                    self.stdout.write(self.style.WARNING(f'Тип ансамбля "{type_name}" уже существует.'))

        self.stdout.write(self.style.SUCCESS('Данные успешно добавлены.'))