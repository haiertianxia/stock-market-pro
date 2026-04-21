
#!/usr/bin/env python3
import akshare as ak
print(dir(ak))
print([x for x in dir(ak) if 'us' in x.lower()])
print([x for x in dir(ak) if 'stock' in x.lower()])
