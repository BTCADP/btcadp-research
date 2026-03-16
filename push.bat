cd "C:\Users\mrjun\OneDrive\Documents\BTCC (Bitcoin Currency)\Website\btcadp-research"
git add .
git commit -m "Update website"
git pull --rebase
git push
npx wrangler pages deploy . --project-name btcadp
