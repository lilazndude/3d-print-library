$repo = "\\CASAOS\3D_Printing\repo"
Set-Location $repo

# Allow git to operate on this UNC path
git config --global --add safe.directory '%(prefix)///CASAOS/3D_Printing/repo'

# Clean up old misplaced git repo and junk files
Remove-Item "$repo\_app\.git" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$repo\_app\venv" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item "$repo\_app (2).7z" -Force -ErrorAction SilentlyContinue
Remove-Item "$repo\_app.7z"     -Force -ErrorAction SilentlyContinue
Remove-Item "$repo\_app.zip"    -Force -ErrorAction SilentlyContinue
Remove-Item "$repo\run.zip"     -Force -ErrorAction SilentlyContinue
Remove-Item "$repo\run (2).zip" -Force -ErrorAction SilentlyContinue

# Remove any leftover .git from the failed init attempt
Remove-Item "$repo\.git" -Recurse -Force -ErrorAction SilentlyContinue

# Init fresh
git init
git add .
git commit -m "Initial commit"

# Push to GitHub (force-replaces existing content)
git remote add origin https://github.com/lilazndude/3d-print-library.git
git branch -M main
git push --force origin main

Write-Host ""
Write-Host " Done. Repo is live at https://github.com/lilazndude/3d-print-library"
Write-Host ""
