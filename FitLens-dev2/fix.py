import codecs
path = 'frontend-vite/src/components/UploadMode.jsx'
with codecs.open(path, 'r', 'utf-8') as f:
    text = f.read()

import re
text = re.sub(r'timeout: 180000\s*console.log\(', 'timeout: 180000\n      });\n\n      console.log(', text)

with codecs.open(path, 'w', 'utf-8') as f:
    f.write(text)
