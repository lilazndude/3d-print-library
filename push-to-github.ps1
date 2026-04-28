Set-Location "\\CASAOS\3D_Printing\repo"

# Allow git to work on this network path
git config --global --add safe.directory '%(prefix)///CASAOS/3D_Printing/repo'

# Stage everything (respects .gitignore — models, venvs etc. are excluded)
git add .

# Commit
git commit -m "Initial commit"

# Add remote (skip if already added)
git remote add origin https://github.com/lilazndude/3d-print-library.git 2>$null

# Push — force overwrites whatever is on GitHub with what you have now
git push --force origin main

Write-Host ""
Write-Host " Done. Live at https://github.com/lilazndude/3d-print-library"
Write-Host ""
