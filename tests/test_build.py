import contextlib
import io
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import build


def word_file(path):
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '''<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>''')
        z.writestr('_rels/.rels', '''<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>''')
        z.writestr('word/document.xml', '''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>A Word interview note</w:t></w:r></w:p></w:body></w:document>''')


class BlogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copytree(build.ROOT / 'assets', self.root / 'assets')
        self.folders = ['GAPS', 'Threat Hunting', 'Place Holder 1', 'Place Holder 2', 'Place Holder 3']
        for folder in self.folders:
            (self.root / folder).mkdir(parents=True)
        self.patch = patch.object(build, 'ROOT', self.root)
        self.patch.start()

    def tearDown(self):
        self.patch.stop()
        self.tmp.cleanup()

    def run_build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return build.build()

    def test_upload_all_formats_and_relative_links(self):
        gaps = self.root / 'GAPS'
        hunt = self.root / 'Threat Hunting'
        (gaps / 'a.md').write_text('# SOC & interviews\n\n[Read](../Threat%20Hunting/a.md#question)\n\n![diagram](diagram.png)\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n<script>alert(1)</script>\n\n[bad](javascript:alert(1))', encoding='utf-8')
        (gaps / 'diagram.png').write_bytes(b'example-image')
        (hunt / 'a.md').write_text('# Question\n\nAnswer', encoding='utf-8')
        word_file(gaps / 'word.docx')
        (gaps / 'reference.PDF').write_bytes(b'%PDF-1.4\n')
        entries = self.run_build()
        self.assertEqual(len(entries), 4)
        self.assertEqual(len({e['url'] for e in entries}), 4)
        md = next(e for e in entries if e['title'] == 'SOC & interviews')
        html = (self.root / 'dist' / md['url']).read_text(encoding='utf-8')
        other = next(e for e in entries if e['folder'] == 'Threat Hunting')
        self.assertIn(other['url'].removeprefix('posts/') + '#question', html)
        self.assertIn('../files/GAPS/diagram.png', html)
        self.assertIn('<table>', html)
        self.assertNotIn('<script>', html)
        self.assertNotIn('javascript:', html)
        word = next(e for e in entries if e['type'] == 'DOCX')
        self.assertIn('A Word interview note', (self.root / 'dist' / word['url']).read_text(encoding='utf-8'))
        pdf = next(e for e in entries if e['type'] == 'PDF')
        self.assertIn('type="application/pdf"', (self.root / 'dist' / pdf['url']).read_text(encoding='utf-8'))
        home = (self.root / 'dist' / 'index.html').read_text(encoding='utf-8')
        for folder in self.folders: self.assertIn(folder, home)
        self.assertTrue((self.root / 'dist' / 'files' / 'GAPS' / 'word.docx').exists())

    def test_deletion_removes_old_pages(self):
        note = self.root / 'GAPS' / 'note.md'
        note.write_text('# Test', encoding='utf-8')
        entry = self.run_build()[0]
        note.unlink()
        self.assertEqual(self.run_build(), [])
        self.assertFalse((self.root / 'dist' / entry['url']).exists())

    def test_corrupt_word_fails_instead_of_silent_missing_note(self):
        (self.root / 'GAPS' / 'broken.docx').write_bytes(b'not a docx')
        with self.assertRaises(zipfile.BadZipFile): self.run_build()

    def test_new_folder_nested_notes_and_renaming_are_automatic(self):
        folder = self.root / 'New Topic' / 'Deep' / 'Further'
        folder.mkdir(parents=True)
        (folder / '2.md').write_text('# Second', encoding='utf-8')
        (folder / '10.md').write_text('# Tenth', encoding='utf-8')
        entries = self.run_build()
        self.assertEqual([e['title'] for e in entries], ['Second', 'Tenth'])
        (self.root / 'New Topic').rename(self.root / 'Renamed Topic')
        entries = self.run_build()
        self.assertEqual({e['folder'] for e in entries}, {'Renamed Topic'})
        home = (self.root / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('Renamed Topic', home)
        self.assertNotIn('New Topic', home)

    def test_images_tools_and_legacy_routes_survive(self):
        (self.root / 'images').mkdir()
        (self.root / 'images' / 'photo.png').write_bytes(b'image')
        (self.root / 'tools').mkdir()
        (self.root / 'tools' / 'breathe-478.html').write_text('<h1>Breathe</h1>')
        (self.root / 'GAPS' / 'note.md').write_text('# Image\n\n![Photo](../images/photo.png)\n\n<details>\n<summary>Answer</summary>\n\n**Bold answer**\n\n</details>', encoding='utf-8')
        entries = self.run_build()
        self.assertTrue((self.root / 'dist' / 'tools' / 'breathe-478.html').exists())
        self.assertTrue((self.root / 'dist' / 'files' / 'images' / 'photo.png').exists())
        self.assertNotIn('images', build.discover_folders())
        html = (self.root / 'dist' / entries[0]['url']).read_text(encoding='utf-8')
        self.assertIn('../files/images/photo.png', html)
        self.assertIn('<details>', html)
        self.assertIn('<strong>Bold answer</strong>', html)
        home = (self.root / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('GAPS/note.md', home)


    def test_rough_stays_in_source_but_is_not_published(self):
        note = self.root / 'GAPS' / 'draft.md'
        note.write_text('# Staging-only draft\n\nUnpublished body', encoding='utf-8')
        published = self.run_build()[0]
        staging = self.root / 'rough' / 'Nested'
        staging.mkdir(parents=True)
        note.rename(staging / 'draft.md')
        (staging / 'attachment.pdf').write_bytes(b'%PDF-1.4')
        (staging / 'broken.docx').write_bytes(b'not converted because it is a draft')
        entries = self.run_build()
        self.assertEqual(entries, [])
        self.assertNotIn('rough', build.discover_folders())
        self.assertTrue((staging / 'draft.md').exists())
        self.assertTrue((staging / 'attachment.pdf').exists())
        self.assertFalse((self.root / 'dist' / published['url']).exists())
        self.assertFalse((self.root / 'dist' / 'files' / 'rough').exists())
        home = (self.root / 'dist' / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('Staging-only draft', home)
        self.assertNotIn('rough/Nested', home)


if __name__ == '__main__': unittest.main()
