import os 
import re

path = os.path.join('generated_data','images')
files = os.listdir(path)

imgnrs = sorted(list(map(lambda t: int(re.search(r'img(\d+)_', t)[1]), files)))
print(len(imgnrs)/2)
