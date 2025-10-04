from django.core.management.base import BaseCommand
from inventario.models import Material, Monos, RecetaMonos

class Command(BaseCommand):
    help = 'Verifica las unidades de los materiales y sus recetas'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*80)
        self.stdout.write("VERIFICACIÓN DE UNIDADES DE MATERIALES Y RECETAS")
        self.stdout.write("="*80 + "\n")
        
        # Listar todos los materiales con sus unidades
        materiales = Material.objects.filter(activo=True).order_by('codigo')
        
        self.stdout.write("\n📦 MATERIALES ACTIVOS:\n")
        for material in materiales:
            self.stdout.write(f"  {material.codigo} - {material.nombre}")
            self.stdout.write(f"    Unidad base: {material.unidad_base}")
            self.stdout.write(f"    Tipo: {material.tipo_material}")
            self.stdout.write(f"    Factor conversión: {material.factor_conversion}")
            self.stdout.write(f"    Disponible: {material.cantidad_disponible} {material.unidad_base}")
            
            # Verificar si tiene recetas
            recetas_usando = RecetaMonos.objects.filter(material=material)
            if recetas_usando.exists():
                self.stdout.write(f"    🎀 Usado en {recetas_usando.count()} receta(s):")
                for receta in recetas_usando:
                    self.stdout.write(
                        f"       - {receta.monos.codigo} ({receta.monos.nombre}): "
                        f"{receta.cantidad_necesaria} {material.unidad_base}"
                    )
            else:
                self.stdout.write(f"    ⚠️  No se usa en ninguna receta")
            
            self.stdout.write("")
        
        # Listar todos los moños con sus recetas
        self.stdout.write("\n" + "="*80)
        self.stdout.write("\n🎀 MOÑOS Y SUS RECETAS:\n")
        
        monos_all = Monos.objects.filter(activo=True).order_by('codigo')
        
        for monos in monos_all:
            recetas = monos.recetas.all()
            self.stdout.write(f"\n  {monos.codigo} - {monos.nombre}")
            
            if recetas.exists():
                self.stdout.write(f"    Recetas: {recetas.count()}")
                for receta in recetas:
                    self.stdout.write(
                        f"      📦 {receta.material.nombre}: "
                        f"{receta.cantidad_necesaria} {receta.material.unidad_base}"
                    )
            else:
                self.stdout.write(f"    ⚠️  SIN RECETAS CONFIGURADAS")
        
        self.stdout.write("\n" + "="*80)
        self.stdout.write("✅ Verificación completada\n")
