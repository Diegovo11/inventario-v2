# Generated manually
from django.db import migrations


def migrate_en_produccion_to_en_salida(apps, schema_editor):
    """
    Migra todas las listas que están en estado 'en_produccion' a 'en_salida'
    ya que el paso 5 fue eliminado del flujo de trabajo.
    """
    ListaProduccion = apps.get_model('inventario', 'ListaProduccion')
    
    # Actualizar todas las listas en 'en_produccion' a 'en_salida'
    updated_count = ListaProduccion.objects.filter(estado='en_produccion').update(estado='en_salida')
    
    if updated_count > 0:
        print(f"✓ {updated_count} lista(s) migrada(s) de 'en_produccion' a 'en_salida'")


def reverse_migration(apps, schema_editor):
    """
    No hay reversión ya que el estado 'en_produccion' ya no existe
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0006_alter_listaproduccion_estado'),
    ]

    operations = [
        migrations.RunPython(migrate_en_produccion_to_en_salida, reverse_migration),
        migrations.AlterField(
            model_name='listaproduccion',
            name='estado',
            field=migrations.CharField(
                choices=[
                    ('borrador', 'Borrador'),
                    ('pendiente_compra', 'Pendiente de Compra'),
                    ('comprado', 'Materiales Comprados'),
                    ('reabastecido', 'Inventario Reabastecido'),
                    ('en_salida', 'Lista en Salida'),
                    ('finalizado', 'Finalizado')
                ],
                default='borrador',
                max_length=20
            ),
        ),
    ]
