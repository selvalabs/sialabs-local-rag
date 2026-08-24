from __future__ import annotations

import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from sialabs_local_rag.main import create_app
from sialabs_local_rag.settings import Settings


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('openapi.json')
    with TemporaryDirectory(prefix='sialabs-openapi-') as temp_dir:
        database_url = f'sqlite:///{Path(temp_dir) / "schema.db"}'
        app = create_app(Settings(app_env='schema-export', database_url=database_url))
        schema = app.openapi()
    output.write_text(json.dumps(schema, indent=2) + '\n', encoding='utf-8')
    print(f'OpenAPI schema: {output}')


if __name__ == '__main__':
    main()
