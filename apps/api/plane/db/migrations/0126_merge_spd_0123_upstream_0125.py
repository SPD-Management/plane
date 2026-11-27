# SPD: o fork tem 0123_alter_default_timezone_and_language (pt-BR /
# America/Sao_Paulo), já aplicada em prd, e o upstream v1.5.0+ trouxe a sua
# própria cadeia 0123..0125. Esta migration só junta as duas folhas para o
# Django não acusar "Conflicting migrations". Sem operações.
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("db", "0123_alter_default_timezone_and_language"),
        ("db", "0125_reset_project_deploy_board_identity"),
    ]

    operations = []
