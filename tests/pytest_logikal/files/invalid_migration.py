from typing import Any

from django.db import migrations


def update(*_args: Any, **_kwargs: Any) -> None:  # missing apps and schema_editor arguments
    """Empty operation."""


class Migration(migrations.Migration):
    operations = [migrations.RunPython(code=update)]  # missing reverse_code
