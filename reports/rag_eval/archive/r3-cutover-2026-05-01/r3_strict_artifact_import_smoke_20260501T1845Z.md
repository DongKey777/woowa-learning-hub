# R3 Strict Artifact Import Smoke - 2026-05-01T18:45Z

Scope: local strict artifact packaging/import contract smoke. This proves the contract that a remote RunPod artifact must satisfy before local serving. It is not itself a remote RunPod build.

Commands:

- Package: `python -m scripts.remote.package_rag_artifact --index-root state/cs_rag --run-id r3-local-87e8588-2026-05-01T1845 --r-phase r3 --strict-r3 ...`
- Verify: `python -m scripts.remote.artifact_contract artifacts/rag-full-build/r3-local-87e8588-2026-05-01T1845 --strict-r3 --verify-import`

Observed:

| Item | Value |
| --- | ---: |
| archive bytes | 156104732 |
| uncompressed bytes | 367953920 |
| compression ratio | 0.4243 |
| archive sha256 | `c4f09836c2398ce4ae128c3c2abb8a4ed8da602310d04ab3548c0025068f44f5` |
| package wallclock | 1.17s |
| strict_r3 verify | true |
| verify_import | true |
| imported index_version | 3 |
| imported row_count | 27170 |
| imported encoder | `BAAI/bge-m3` |

Interpretation:

- The import contract now fails closed on missing strict R3 metadata, archive checksum mismatch, decompression failure, or extracted index manifest mismatch.
- The local artifact import check passed for the current R3 Lance index: row_count=27170, encoder=`BAAI/bge-m3`, and chunk hash sidecar present.
- Actual remote RunPod artifact production remains a separate operational run, but it now has a concrete local verification gate.
