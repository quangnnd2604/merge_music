import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.controllers.media_controller import MediaController

c=MediaController(r'C:\Users\ADMIN\Desktop\WORKING\music\Acoustic\After_the_Storm')
pairs=c.get_media_pairs()
print('pairs count:', len(pairs))
for p in pairs:
    print(p.audio.base_name, '->', p.audio.name, '+', p.media.name)
