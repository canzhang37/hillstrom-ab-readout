# get the original challenge CSV into data/
import hashlib
import urllib.request
from pathlib import Path

URL = ("http://www.minethatdata.com/"
       "Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv")
DEST = Path("data/hillstrom.csv")

DEST.parent.mkdir(exist_ok=True)
urllib.request.urlretrieve(URL, DEST)
digest = hashlib.sha256(DEST.read_bytes()).hexdigest()
print(f"{DEST}: {DEST.stat().st_size} bytes, sha256 {digest}")
