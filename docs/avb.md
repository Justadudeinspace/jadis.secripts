# AVB evidence and trust

```sh
js avb insp vbmeta.img --json
js avb vfy vbmeta.img --key expected-public.pem --json
js avb vfy vbmeta.img --partition boot=boot.img --partition system=system.img --json
```

Native schema-1 models validate footer/vbmeta bounds, authentication/auxiliary subranges, algorithm
sizes, public-key encoding bounds and property/hash/hashtree/cmdline/chain descriptor structures.
Public key identity is a fingerprint, not a root-of-trust decision. Property/cmdline values are not
dumped. Unsafe partition references and unbounded descriptor dimensions are refused before providers.
Native hash descriptors use declared salt/algorithm and explicitly supplied image evidence. Persistent
(unembedded) digests remain unverified. Authentication-hash matching is separate from RSA verification.

RSA/signature and hashtree verification use an **explicit installed avbtool**. No homemade RSA or new
runtime crypto dependency is introduced. Missing capability returns CRYPTO_PROVIDER_UNAVAILABLE,
not metadata PASS. Expected keys must be PEM public keys; private-key inputs are refused.

Providers run with fixed argv/time/output bounds against isolated copies and explicit companion images.
There is no automatic chain following, signing, unlocking, verification-disable flag or bypass feature.
Pinned upstream avbtool can be prepared explicitly for development/CI with
`python tools/prepare_avb_provider.py --output NEW_DIRECTORY`; ordinary runtime commands never download it.

Independent states include SIGNATURE_MATHEMATICALLY_VALID, EMBEDDED_KEY_IDENTIFIED, EXPECTED_KEY_MATCH,
HASH_DESCRIPTOR_VALID, HASHTREE_VALID, VBMETA_DIGEST_CALCULATED and ROLLBACK_METADATA_PRESENT. Failure,
missing inputs and unavailable providers remain distinct. Signature evidence can succeed while a
later descriptor check blocks/fails; that does not turn the full image into verified output.

Chain descriptors are modeled but expected-chain verification remains UNVERIFIED. Chained digest
traversal is not invoked until a bounded trusted-chain workflow exists. FEC verification is unverified.
FIT signatures also remain unverified. No source/corpus signing keys are trusted or imported.

DEVICE_ROLLBACK_POLICY_UNVERIFIED and ROOT_OF_TRUST_UNVERIFIED remain mandatory: an offline image cannot
prove the device's stored rollback state, fused root key, ownership or bootloader enforcement. A supplied
expected public key expresses operator context and can prove a match; it does not prove hardware trust.
