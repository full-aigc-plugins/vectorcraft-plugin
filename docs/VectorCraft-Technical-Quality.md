# VectorCraft technical quality candidate

The readonly candidate checker verifies current runtime/project/file hashes and decodes PNG with Pillow and PDF/SVG with PyMuPDF. Missing decoders remain NOT_RUN; corrupt exports or stale identities block acceptance even when creative assessment says PASS. Artifact integrity does not claim native reopening: engineering remains NOT_RUN, and acceptance stays pending.

Five unit tests and18 actual fixed38/source35 exports were checked, including two corrupt-PNG cases with matching manifest hashes. Task6.1 is complete. ReviewStore/CLI integration6.2 and complete native engineering/creative acceptance6.3 remain open. [Bound evidence](evidence/vectorcraft-technical-quality-candidate-20261008.json).
