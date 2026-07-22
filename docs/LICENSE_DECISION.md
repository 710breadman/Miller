# Project license decision

Status: owner decision required. This document is not legal advice.

Miller currently contains original implementation plus references to permissive
and GPL-licensed upstream projects. Until a project license is selected:

- do not copy upstream source into Miller;
- keep GPL tools external and user-installed;
- record source-code and model-weight licenses separately;
- retain exact revisions and notices for every distributed dependency;
- record the FFmpeg build and codec configuration used for packaged releases.

## Practical candidates

- **Apache-2.0:** permissive, includes an explicit patent grant and NOTICE duties.
- **MIT:** short and permissive, with simpler notice requirements.

The owner should choose after considering intended distribution, contributor
policy, and whether any future code will be adapted from upstream sources.
