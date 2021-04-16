'''Aggregation of webservices required by the extension.'''

from io import StringIO
from bioservices.chebi import ChEBI
from bioservices.uniprot import UniProt
from urllib.error import URLError

from typing import Text
import csv


class NetworkError(Exception):
    pass


class WebServices:
    def __init__(self):
        self.chebi = None
        self.uniprot = None

    def init_chebi(self):
        if self.chebi is None:
            try:
                self.chebi = ChEBI()
            except Exception:
                raise NetworkError

    def init_uniprot(self):
        if self.uniprot is None:
            try:
                self.uniprot = UniProt()
            except Exception:
                raise NetworkError

    def annot_search_chebi(self, query: str):
        self.init_chebi()
        # TODO do we want to change searchCategory and maybe THREE STARS?
        if query.strip() == '':
            return list()

        try:
            results = self.chebi.getLiteEntity(query, maximumResults=100)
        except URLError:
            raise NetworkError

        # no result
        if isinstance(results, str):
            return list()
        # sort by length as well. TODO should I do this?
        results.sort(key=lambda e: e.searchScore * -10000 + len(e.chebiAsciiName))
        results = results[:20]
        return [{
            'id': res.chebiId,
            'name': res.chebiAsciiName,
            'prefix': 'chebi'
        } for res in results]

    def annot_search_uniprot(self, query: str):
        self.init_uniprot()

        if query.strip() == '':
            return list()

        try:
            result_str = self.uniprot.search(query, limit=20, columns='id,entry name,protein names,genes')
        except URLError:
            raise NetworkError

        assert isinstance(result_str, str)
        result_f = StringIO(result_str)
        reader = csv.reader(result_f, delimiter='\t')
        objects = list()
        # Skip header
        next(reader)
        for row in reader:
            id_, entry_name, protein_names, genes = row
            objects.append({
                'id': id_,
                'name': entry_name,
                'protein_names': protein_names,
                'genes': genes,
                'prefix': 'uniprot',
            })
        return objects
