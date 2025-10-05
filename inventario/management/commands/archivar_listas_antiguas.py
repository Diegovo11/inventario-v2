"""
Management command para archivar automáticamente listas finalizadas con más de 30 días.
Ejecutar: python manage.py archivar_listas_antiguas
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from inventario.models import ListaProduccion


class Command(BaseCommand):
    help = 'Archiva listas finalizadas con más de 30 días de antigüedad'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dias',
            type=int,
            default=30,
            help='Número de días después de los cuales archivar (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se archivaría sin hacer cambios',
        )

    def handle(self, *args, **options):
        dias = options['dias']
        dry_run = options['dry_run']
        
        # Calcular fecha límite
        fecha_limite = timezone.now() - timedelta(days=dias)
        
        # Encontrar listas finalizadas antiguas
        listas_a_archivar = ListaProduccion.objects.filter(
            estado='finalizado',
            fecha_modificacion__lt=fecha_limite
        )
        
        cantidad = listas_a_archivar.count()
        
        if cantidad == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ No hay listas finalizadas con más de {dias} días para archivar'
                )
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'[DRY RUN] Se archivarían {cantidad} lista(s):'
                )
            )
            for lista in listas_a_archivar:
                dias_antiguedad = (timezone.now() - lista.fecha_modificacion).days
                self.stdout.write(
                    f'  - {lista.nombre} (finalizada hace {dias_antiguedad} días)'
                )
        else:
            # Archivar las listas
            listas_a_archivar.update(estado='archivado')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Se archivaron {cantidad} lista(s) finalizadas con más de {dias} días'
                )
            )
            
            for lista in listas_a_archivar:
                self.stdout.write(f'  ✓ {lista.nombre}')
