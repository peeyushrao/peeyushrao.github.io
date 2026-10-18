# Peeyush Rao — Security notebook

This repository powers **https://peeyushrao.github.io/**. Add a note, commit, and push to `main`; GitHub builds and publishes the site automatically.

## Start here on this laptop

Your working copy is **`C:\Users\Shashi-Peeyush\Downloads\peeyushrao-blog`**. It is already a Git repository connected to `peeyushrao/peeyushrao.github.io`. There is no nested `repository` directory, and you do not need to extract a ZIP or run an installer again.

```powershell
cd "$env:USERPROFILE\Downloads\peeyushrao-blog"
git pull --ff-only
# Add or edit your notes now.
git status
git add .
git commit -m "Update security notes"
git push origin main
```

Review `git status` before staging, especially when deleting or moving notes. Push only the changes you intend to publish or store on GitHub.

## Where things belong

| Folder / file | Purpose |
| --- | --- |
| `CrowdStrike/`, `CWPP/`, `SecOps/`, `Interview/`, `Linux/`, `Windows/`, `Zscaler/`, `Arsenal/` | Published notes, grouped by topic |
| `CrowdStrike/CQL/` and other child folders | Nested filters beneath their parent topic |
| `About/profile.md` | The About page; also linked from the site header |
| `rough/` | Draft staging: tracked in GitHub, excluded from the generated blog |
| `images/` | Shared images referenced from notes |
| `tools/` | Tool notes and the standalone breathing page |
| `assets/` | Site styles, scripts, and the bundled Mermaid renderer |
| `tests/` | Automated checks run before publishing; keep this folder |
| `build.py` | Generates the static site |
| `.github/workflows/pages.yml` | Builds and deploys on pushes to `main` |
| `dist/` | Generated output; ignored by Git |

## Draft first, publish when ready

Put unfinished notes and their attachments in the root `rough/` folder. Do not add it to `.gitignore`: it should remain in GitHub. The builder excludes all of `rough/` from navigation, search, article pages, legacy routes, and original-file downloads.

To publish a draft, move it and any needed attachments to a topic folder, fix relative links if needed, then commit and push. To unpublish a note, move it into `rough/` and push; the next successful build removes the previously generated page.

**The repository is public.** Drafts in `rough/` remain visible on GitHub and in Git history; staging does not make them private.

## Content and appearance

- Markdown: headings, tables, code blocks, linked images, relative links, collapsible answers, and Mermaid diagrams.
- Word `.docx`: converted into a readable article. Advanced Word formatting and pagination may differ.
- PDF: browser viewer with an original download link. PDF text is not searched.
- Search covers full published Markdown and Word text.
- Topic folders and child folders are discovered automatically; no sidebar edits are needed. Root reserved folders and hidden content are excluded. Empty folders need a `.gitkeep` for Git to retain them.
- The site uses a light ivory, teal, and sage palette with system fonts. Code blocks and diagrams have their own readable panels.
- The breathing tool remains at `/tools/breathe-478.html`; old Docsify article bookmarks redirect where their original source paths still exist.

## Publishing and troubleshooting

Pages should use **Settings → Pages → Source → GitHub Actions**. The workflow is **Publish security notes**. You do not need **Run workflow** for everyday changes; each push to `main` triggers it.

If an update is missing, check the latest commit and Actions run, then use **Ctrl + F5** after a successful deployment. If Git reports *dubious ownership* following the earlier folder cleanup, trust this exact local clone once in your own PowerShell:

```powershell
git config --global --add safe.directory "C:/Users/Shashi-Peeyush/Downloads/peeyushrao-blog"
```

## Optional local preview

Python is not required to publish. For local preview only, use Python 3.13:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m unittest discover -s tests
.venv\Scripts\python build.py
.venv\Scripts\python -m http.server 8000 --directory dist
```

Open http://localhost:8000. Generated files in `dist/` should not be committed. Mermaid 10.9.5 is bundled under its included MIT license. Invalid diagrams retain a source fallback.

## Git guide: managing both blogs

Keep a separate local clone for each blog. The repository folder you run Git from determines which blog receives your changes.

| Blog | Folder on this laptop | Where notes belong |
| --- | --- | --- |
| `rpeeyush.github.io` | `Downloads\rpeeyush-blog\repository` | Inside `content\GAPS`, `content\Threat Hunting`, `content\Guidelines`, or another configured content folder |
| `peeyushrao.github.io` | `Downloads\peeyushrao-blog` | Inside topic folders such as `CrowdStrike\CQL`, `CWPP`, or `Windows` |

The security blog now lives directly in `Downloads\peeyushrao-blog`; there is no nested `repository` folder. The interview blog still uses `Downloads\rpeeyush-blog\repository`. Git publishes changes from the selected clone. Check your destination at any time with:

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
cd "$env:USERPROFILE\Downloads\peeyushrao-blog"
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
