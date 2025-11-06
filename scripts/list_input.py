from pathlib import Path
p=Path(r'C:\Users\ADMIN\Desktop\WORKING\music\Acoustic\After_the_Storm')
print('Folder exists:', p.exists())
for f in sorted(p.iterdir()):
    if f.is_file():
        print(f.name, '->', f.suffix.lower(), 'base:', f.stem)
