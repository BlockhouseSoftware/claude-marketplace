import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('catalog',Path(__file__).resolve().parents[1]/'scripts/check_catalog.py')
catalog=importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

class CatalogPinTests(unittest.TestCase):
    def test_sha_is_required(self):
        entry=json.loads((Path(__file__).resolve().parents[1]/'.claude-plugin/marketplace.json').read_text())['plugins'][0]
        del entry['source']['sha']
        errors=[]
        catalog.check_entry(entry,errors,False,30)
        self.assertTrue(any('sha is required' in e for e in errors))

    def test_fetch_reads_effective_sha_and_rejects_tag_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            def git(*args):
                return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL).decode().strip()
            git('init','-q')
            (root/'.claude-plugin').mkdir()
            (root/'.claude-plugin/plugin.json').write_text('{"name":"x","version":"0.3.1"}')
            git('add','.')
            git('-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','release')
            sha=git('rev-parse','HEAD')
            git('tag','v0.3.1')
            source={'source':'url','url':str(root),'ref':'v0.3.1','sha':sha}
            self.assertEqual(catalog.fetch_manifest(source,30)['version'],'0.3.1')
            source['sha']='a'*40
            with self.assertRaisesRegex(ValueError,'not catalog SHA'):
                catalog.fetch_manifest(source,30)

class PromotionTests(unittest.TestCase):
    def test_missing_tag_leaves_catalog_unchanged(self):
        import sys
        scripts = str(Path(__file__).resolve().parents[1]/'scripts')
        with patch.object(sys,'path',[scripts,*sys.path]):
            import promote_release
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(['git','init','-q',str(root/'repo')],check=True)
            path=root/'marketplace.json'
            path.write_text(json.dumps({'plugins':[{'name':'trojaino','source':{'source':'url','url':str(root/'repo')}}]}))
            original=path.read_bytes()
            with self.assertRaises(subprocess.CalledProcessError):
                promote_release.promote(path,'v0.3.1')
            self.assertEqual(path.read_bytes(),original)
