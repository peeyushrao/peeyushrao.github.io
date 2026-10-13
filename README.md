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

Open http://localhost:8000. The workflow uses Python 3.13. The `dist/` folder is generated and excluded from Git. Mermaid 10.9.5 is bundled locally under its MIT license; the theme uses system fonts. Invalid diagrams retain their source as a fallback.

## Git guide: managing both blogs

Keep a separate local clone for each blog. The repository folder you run Git from determines which blog receives your changes.

| Blog | Folder on this laptop | Where notes belong |
| --- | --- | --- |
| `rpeeyush.github.io` | `Downloads\rpeeyush-blog\repository` | Inside `content\GAPS`, `content\Threat Hunting`, `content\Guidelines`, or another configured content folder |
| `peeyushrao.github.io` | `Downloads\peeyushrao-blog\repository` | Inside topic folders such as `CrowdStrike\CQL`, `CWPP`, or `Windows` |

Edit files inside the clone named `repository`, rather than the extracted ZIP's surrounding folder. Git publishes tracked changes in the clone. Check your destination at any time with:

```powershell
git remote -v
```

### Set the correct account for each blog (once per clone)

For the interview blog:

```powershell
cd "$env:USERPROFILE\Downloads\rpeeyush-blog\repository"
git remote set-url origin https://rpeeyush@github.com/rpeeyush/rpeeyush.github.io.git
git config user.name "Peeyush"
git config user.email "EMAIL_FOR_RPEEYUSH"
```

For the security blog:

```powershell
cd "$env:USERPROFILE\Downloads\peeyushrao-blog\repository"
git remote set-url origin https://peeyushrao@github.com/peeyushrao/peeyushrao.github.io.git
git config user.name "Peeyush Rao"
git config user.email "EMAIL_FOR_PEEYUSHRAO"
```

Replace each email placeholder with that account's verified GitHub email or its GitHub-provided private commit email. These settings are local to the clone. `user.name` and `user.email` control commit attribution; the account in the remote URL guides Git Credential Manager's login selection. Never put passwords or tokens in the URL.

### Everyday routine

Open PowerShell in the appropriate clone, then download the latest changes **before editing**:

```powershell
git pull --ff-only
```

Add or edit your Markdown, Word (`.docx`), or PDF files using File Explorer or your editor. Then review, commit, and push:

```powershell
git status
git add .
git commit -m "Update notes"
git push origin main
```

`git status` shows the pending changes. `git add .` stages additions, edits, and deletions beneath the current directory, so run it from the clone's root and check the listed files. `git commit` records them locally. `git push` sends your commits to GitHub.

If you only want to publish content changes in the interview blog, use `git add content` instead. For changes to site files such as `build.py`, JavaScript, CSS, or this README, use `git add .` or explicitly stage those files.

Choose the matching GitHub account when a login window appears. A saved login may be reused without a prompt.

### Upload directly through GitHub's website

1. Sign in to the correct account and open the correct repository.
2. Navigate to the destination folder.
3. Choose **Add file → Upload files**.
4. Select your files and commit the changes to `main`.

Both website uploads and Git pushes trigger the publishing workflow. If GitHub creates a separate branch, merge its pull request into `main` to publish those changes.

After a website upload, run `git pull --ff-only` in that blog's local clone before making further local edits. This keeps the website and local copy synchronized.

### Automatic publishing and folder behavior

- GitHub Pages uses **Settings → Pages → Source → GitHub Actions**. This is a one-time setting for each repository.
- Every push or website commit to `main` automatically builds and publishes the site.
- Routine updates do not need **Run workflow**. Use it for a manual retry or an initial deployment after changing Pages settings.
- The interview blog's workflow is **Publish interview blog**. The security blog's is **Publish security notes**.
- Wait for both build and deploy to succeed, then refresh the site. On Windows, **Ctrl + F5** forces a refresh.
- In the interview blog, the top-level folder names under `content/` must match `FOLDERS` in `build.py`; update that list when renaming a top-level folder.
- In the security blog, new and renamed topic folders are discovered automatically. With the child-folder update installed, selecting CrowdStrike includes all its notes, while selecting its CQL child includes only that subtree.
- Git does not track empty directories. Put a `.gitkeep` file in an empty folder if you want it retained.

### Move to another laptop

Push any unpushed work from the old laptop first. Install [Git for Windows](https://git-scm.com/install/windows) on the new laptop, reopen PowerShell, and clone both repositories:

```powershell
cd "$env:USERPROFILE\Documents"
git clone https://rpeeyush@github.com/rpeeyush/rpeeyush.github.io.git
git clone https://peeyushrao@github.com/peeyushrao/peeyushrao.github.io.git
```

Your new working folders are now:

```text
Documents/
  rpeeyush.github.io/
  peeyushrao.github.io/
```

Set your commit identity in each new clone, replacing the email placeholders:

```powershell
cd "$env:USERPROFILE\Documents\rpeeyush.github.io"
git config user.name "Peeyush"
git config user.email "EMAIL_FOR_RPEEYUSH"

cd "$env:USERPROFILE\Documents\peeyushrao.github.io"
git config user.name "Peeyush Rao"
git config user.email "EMAIL_FOR_PEEYUSHRAO"
```

Use the same pull → edit → status → add → commit → push routine in the chosen new folder. Authenticate with the corresponding GitHub account when asked. You do not need the original ZIP, the installer, Python, or another Pages setup to publish updates: the repositories contain the blog source and GitHub runs the builds. Python is only needed for an optional local preview.

When switching between laptops, push before leaving one and pull before editing on the other. You can also manage uploads through GitHub's website on any laptop.

### Troubleshooting

Run these from the affected clone:

```powershell
git status
git remote -v
git log -1 --oneline
```

| Message or symptom | What to do |
| --- | --- |
| `ahead of origin/main` | Your commit is local; run `git push origin main`. |
| `Everything up-to-date` | There are no unpushed commits. Check `git status` for unstaged files and confirm you edited the actual clone. |
| `nothing to commit, working tree clean` | No file changes are waiting to be committed; this alone does not prove the new version is deployed. Check the latest commit and Actions run. |
| `403` or `Permission denied to rpeeyush` for the security repository | Set its remote to `https://peeyushrao@github.com/peeyushrao/peeyushrao.github.io.git` and retry the push using the `peeyushrao` account. Do not create another commit for the same changes. |
| Git asks who you are | Set `git config user.name` and `git config user.email` in that clone, then retry the commit. |
| Push rejected because the remote contains new work | If your working tree is clean, run `git pull --rebase`, resolve any reported conflicts, then push. Preserve existing edits before attempting this; stop and ask for help if unsure. |
| `git pull --ff-only` fails | Stop and inspect `git status`. Local edits or diverging commits need attention; do not discard them or force-push. |
| Site still shows the old version | Check the correct repository's Actions tab. If no new run exists, verify your push. If the run failed, read the failed step. If it succeeded, use Ctrl + F5. |

Official references: [cloning repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository), [multiple GitHub accounts with Git Credential Manager](https://github.com/git-ecosystem/git-credential-manager/blob/main/docs/multiple-users.md), and [GitHub Pages publishing settings](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site).
