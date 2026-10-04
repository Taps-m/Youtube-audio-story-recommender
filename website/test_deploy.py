import tempfile,shutil,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('pack',ROOT/'package_deploy.py');pack=importlib.util.module_from_spec(spec);spec.loader.exec_module(pack)
pack.validate(ROOT/'dist')
with tempfile.TemporaryDirectory() as tmp:
 dest=Path(tmp)/'dist';shutil.copytree(ROOT/'dist',dest)
 (dest/'local-test-catalog.json').write_text('[]')
 try:pack.validate(dest)
 except ValueError:pass
 else:raise AssertionError('Private files were accepted')
print('Public directory passes; deployment rejects a private test catalog.')
