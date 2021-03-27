from bioservices.chebi import ChEBI


chebi = ChEBI()


def chebi_search(query: str):
    results = chebi.getLiteEntity(query, maximumResults=100)
    results.sort(key=lambda e: e.searchScore * -10000 + len(e.chebiAsciiName))
    return results[:20]
