from typing import Text
from bioservices.chebi import ChEBI


chebi = ChEBI()


def chebi_search(query: str):
    # TODO do we want to change searchCategory and maybe THREE STARS?
    results = chebi.getLiteEntity(query, maximumResults=100)
    # no result
    if isinstance(results, str):
        return list()
    # sort by length as well. TODO should I do this?
    results.sort(key=lambda e: e.searchScore * -10000 + len(e.chebiAsciiName))
    return results[:20]
