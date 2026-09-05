import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'tools' / f'{name}.py')
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def pdf(path):
    # Minimal valid, one-page PDF without third-party test dependencies.
    path.parent.mkdir(parents=True, exist_ok=True)
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 100 100] >>']
    data = b'%PDF-1.4\n'; offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += f'{number} 0 obj\n'.encode() + body + b'\nendobj\n'
    start = len(data)
    data += b'xref\n0 4\n0000000000 65535 f \n'
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    data += f'trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    path.write_bytes(data)


class ArchiveTests(unittest.TestCase):
    def test_upload_versions_catalog_deletion_and_idempotence(self):
        index = module('index_archive').index
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for version in (1, 2, 10):
                pdf(root / f'notes/2026/1141/v{version}/1141.pdf')
            pdf(root / 'misc/Exam & reference.PDF')
            index(root)
            target = root / 'manifests/notes-2026.json'
            data = json.loads(target.read_text())
            self.assertEqual(data['subjects'][0]['version'], 'v10')
            self.assertEqual(data['subjects'][0]['pages'], 1)
            self.assertEqual(len(json.loads((root/'manifests/archive-index.json').read_text())['documents']), 4)
            before = target.read_bytes(); index(root)
            self.assertEqual(before, target.read_bytes())
            for path in (root/'notes').rglob('*.pdf'): path.unlink()
            index(root)
            record = json.loads(target.read_text())['subjects'][0]
            self.assertEqual(record['status'], 'missing')
            self.assertNotIn('pdfUrl', record)

    def test_invalid_upload_does_not_rewrite_manifests(self):
        index = module('index_archive').index
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            pdf(root / 'notes/2021/1001/v1/1001.pdf'); index(root)
            target = root/'manifests/notes-2021.json'; before = target.read_bytes()
            (root/'fake.pdf').write_text('<html>Not a PDF</html>')
            with self.assertRaises(ValueError): index(root)
            self.assertEqual(before, target.read_bytes())

    def test_migration_preserves_original_bytes_and_rejects_modifications(self):
        migrate = module('import_legacy_pdfs').migrate
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source'; archive = root/'archive'
            source.mkdir(); archive.mkdir()
            for path in (source, archive): subprocess.run(['git', 'init', '-q', str(path)], check=True)
            pdf(source/'notes/one.pdf')
            subprocess.run(['git','-C',str(source),'add','.'],check=True)
            subprocess.run(['git','-C',str(source),'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-qm','fixture'],check=True)
            remote = root / 'remote.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            for args in [('checkout','-b','main'),('config','user.name','Test'),('config','user.email','test@example.invalid'),('remote','add','origin',str(remote))]:
                subprocess.run(['git','-C',str(archive),*args],check=True,capture_output=True)
            migrate(source, archive, push=True)
            remote_files = subprocess.check_output(['git','--git-dir',str(remote),'ls-tree','-r','--name-only','main']).decode()
            self.assertIn('notes/one.pdf', remote_files)
            data=json.loads((archive/'manifests/legacy-diploma-notes.json').read_text())
            self.assertEqual(len(data['documents']),1)
            self.assertEqual((source/'notes/one.pdf').read_bytes(),(archive/data['documents'][0]['archivePath']).read_bytes())
            (source/'notes/one.pdf').write_bytes((source/'notes/one.pdf').read_bytes()+b'changed')
            with self.assertRaises(ValueError): migrate(source, archive)


if __name__ == '__main__':
    unittest.main()
