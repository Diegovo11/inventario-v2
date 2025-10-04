from django.core.management.base import BaseCommand
from inventario.models import Monos, RecetaMonos, Material


class Command(BaseCommand):
    help = 'Verifica las recetas de todos los moños'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== VERIFICACIÓN DE RECETAS ===\n'))
        
        monos_all = Monos.objects.all()
        
        if not monos_all.exists():
            self.stdout.write(self.style.WARNING('⚠️  No hay moños en la base de datos'))
            return
        
        self.stdout.write(f'📊 Total de moños: {monos_all.count()}\n')
        
        monos_sin_recetas = []
        monos_con_recetas = []
        
        for mono in monos_all:
            recetas = mono.recetas.all()
            recetas_count = recetas.count()
            
            if recetas_count == 0:
                monos_sin_recetas.append(mono)
                self.stdout.write(
                    self.style.ERROR(f'❌ {mono.codigo} - {mono.nombre}: SIN RECETAS')
                )
            else:
                monos_con_recetas.append(mono)
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {mono.codigo} - {mono.nombre}: {recetas_count} receta(s)')
                )
                
                # Mostrar detalles de las recetas
                for receta in recetas:
                    self.stdout.write(
                        f'   📦 {receta.material.nombre}: '
                        f'{receta.cantidad_necesaria} {receta.material.unidad_base}'
                    )
        
        # Resumen
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'✅ Moños CON recetas: {len(monos_con_recetas)}'))
        self.stdout.write(self.style.ERROR(f'❌ Moños SIN recetas: {len(monos_sin_recetas)}'))
        
        if monos_sin_recetas:
            self.stdout.write('\n⚠️  ATENCIÓN: Los siguientes moños NO tienen recetas:')
            for mono in monos_sin_recetas:
                self.stdout.write(f'   - {mono.codigo}: {mono.nombre}')
            self.stdout.write('\n💡 Estos moños NO descontarán materiales al producirse.')
        
        self.stdout.write('='*60 + '\n')
