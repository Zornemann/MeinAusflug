git add .
git commit -m "Automatisches Update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git push origin main
Write-Host "🚀 Projekt erfolgreich auf GitHub aktualisiert!" -ForegroundColor Green