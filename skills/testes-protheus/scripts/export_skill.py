"""Exporta pasta validada sem intermediários. author: daniel.montagna."""
import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile, ZIP_DEFLATED
from validate_package import validate


def export(root, output):
    root = Path(root).resolve()
    output = Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError("ZIP deve ficar fora da pasta da skill")
    errors = validate(root)
    if errors:
        raise ValueError("Pacote reprovado pelo scanner: " + "; ".join(errors))
    files = sorted(path for path in root.rglob("*") if path.is_file())
    manifest = {"author": "daniel.montagna", "skill": "testes-protheus", "files": []}
    # modo x impede substituição silenciosa de entrega previamente publicada.
    with ZipFile(output, "x", compression=ZIP_DEFLATED) as archive:
        for path in files:
            content = path.read_bytes()
            name = "testes-protheus/" + path.relative_to(root).as_posix()
            manifest["files"].append({"path": name, "bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()})
            archive.writestr(name, content)
        archive.writestr("MANIFESTO.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Uso: python -B export_skill.py PASTA_SKILL ZIP_NOVO")
    result = export(sys.argv[1], sys.argv[2])
    print(json.dumps({"author": "daniel.montagna", "files": len(result["files"]), "zip": str(Path(sys.argv[2]).resolve())}, ensure_ascii=False))
