# FAQ

**Do I need invisible watermarking?**  
No. It’s optional deterrence. Your signed manifest + hashes carry most evidentiary weight.

**What if a platform strips metadata?**  
Your signed `manifest.json` still proves authorship and timing. Metadata is convenience, not the foundation.

**Why not MD5?**  
Use SHA-256. MD5 is weak and collision-prone.

**Can I use my existing GPG key?**  
Yes—import or point Sealimg at it. Ed25519 is the default for new keys.

**Can I seal offline?**  
Yes. All features are local by default.

**What if I lose my key?**  
Keep an offline backup + revocation file. Losing the private key prevents future signatures but does not invalidate past signed manifests.
