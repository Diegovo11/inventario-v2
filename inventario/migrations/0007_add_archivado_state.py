# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0006_alter_listaproduccion_estado'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listaproduccion',
            name='estado',
            field=models.CharField(
                choices=[
                    ('borrador', 'Borrador'),
                    ('pendiente_compra', 'Pendiente de Compra'),
                    ('comprado', 'Materiales Comprados'),
                    ('reabastecido', 'Inventario Reabastecido'),
                    ('en_produccion', 'En Producción'),
                    ('en_salida', 'Lista en Salida'),
                    ('finalizado', 'Finalizado'),
                    ('archivado', 'Archivado')
                ],
                default='borrador',
                max_length=20
            ),
        ),
    ]
