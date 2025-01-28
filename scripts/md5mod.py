import hashlib
def createmd5(filetocheck): 
  filename = "data/" + filetocheck
  checksumfile = filetocheck[:-4] + "md5"
  md5_hash = hashlib.md5()
  with open(filename,"rb") as f:
    for byte_block in iter(lambda: f.read(4096),b""):
        md5_hash.update(byte_block)
  checksum = md5_hash.hexdigest()
  with open(checksumfile, 'w') as fp:
      fp.write(checksum)
