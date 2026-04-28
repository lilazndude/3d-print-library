$r = "\\CASAOS\3D_Printing\repo"

Remove-Item "$r\_app\run.bat"                  -Force -ErrorAction SilentlyContinue
Remove-Item "$r\_app\templates\gallery.html"   -Force -ErrorAction SilentlyContinue
Remove-Item "$r\_app\.gitignore"               -Force -ErrorAction SilentlyContinue
Remove-Item "$r\launch.vbs"                    -Force -ErrorAction SilentlyContinue
Remove-Item "$r\stop.bat"                      -Force -ErrorAction SilentlyContinue
Remove-Item "$r\git-setup.ps1"                 -Force -ErrorAction SilentlyContinue
Remove-Item "$r\3D Print Manager.7z"           -Force -ErrorAction SilentlyContinue

Write-Host "Cleanup done."
