# Peeyush Rao — Security notes

Add a Markdown, Word, or PDF file to a topic folder. Commit and push to `main`. One GitHub Actions workflow builds the folder list, renders the notes, and publishes the blog.

## One-time installation into your existing clone

Extract `peeyushrao-blog.zip`. Open PowerShell in the extracted folder, then run the installer with the path to your existing clone:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1 -RepositoryPath "C:\path\to\peeyushrao.github.io"
```

The execution-policy override applies only to that command. The installer checks the repository's `origin`, copies the builder and supporting files, preserves the current README as `About/profile.md`, and removes the old `.github/workflows/update-sidebar.yml`. It does not copy the bundled snapshot over your existing topic folders. Existing `index.html` and `_sidebar.md` can remain; the new workflow publishes generated `dist/` instead.

If you don't already have a clone, create one first:

```powershell
cd "$env:USERPROFILE\Documents"
git clone https://github.com/peeyushrao/peeyushrao.github.io.git
```

After installing, in the clone:

```powershell
git status
git diff
git add .
git commit -m "Simplify blog publishing and discover folders automatically"
git push origin main
```

Set **GitHub → Settings → Pages → Source → GitHub Actions** once. Under **Actions → Publish security notes**, run the workflow on `main` if needed after changing that setting. Later pushes publish automatically. Your site is https://peeyushrao.github.io/.

## Everyday use

Keep your existing folders: `Arsenal`, `CrowdStrike`, `CWPP`, `IR`, `Interview-QA`, `Linux`, `Windows`, `Zscaler`, and `tools`.

Create or rename any topic folder in the repository root; the site discovers it automatically. Nested subfolders work too. Add images alongside notes, or use the shared `images/` folder. Empty folders need a `.gitkeep` file for Git to retain them.

```powershell
git pull --ff-only
# Add or edit notes in a topic folder using File Explorer or your editor.
git add .
git commit -m "Update security notes"
git push origin main
```

You do not edit a sidebar, change a folder list in Python, run Python locally, or manually trigger Actions for routine updates. Check the files listed by `git status` before committing.

## Supported content

- Markdown: tables, code blocks, images, relative document links, collapsible answers, and Mermaid diagrams.
- Word `.docx`: readable articles with images/tables; exact Word pagination and advanced layout are not retained.
- PDF: browser viewer plus an original download link. PDF text is not indexed.
- Search: titles, folders, and full Markdown/Word text.
- Downloads: copied alongside the originals. The existing archive remains in `Arsenal/Downloads`.
- Breathing tool: retains its public URL at `/tools/breathe-478.html`.
- Old Docsify `/#/Folder/note.md` bookmarks redirect to the generated article. Existing heading fragments are passed through; old fragments may differ from generated heading IDs.

The root README is setup documentation; the former home/profile content is available under About. Root directories `assets`, `tests`, `images`, `dist`, `work`, `outputs`, `node_modules`, and hidden directories are reserved. Use other names for topics. Symlinks and hidden content are excluded.

The workflow has no permission to commit source changes and creates no bot commits. It uploads the generated site as a Pages artifact. Uploaded material and downloads are public.

## Local preview (optional)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests
.venv\Scripts\python build.py
.venv\Scripts\python -m http.server 8000 --directory dist
```

Open http://localhost:8000. The workflow uses Python 3.13. The `dist/` folder is generated and excluded from Git. Mermaid 10.9.5 is bundled locally under its MIT license; fonts have an offline system-font fallback. Invalid diagrams retain their source as a fallback.
