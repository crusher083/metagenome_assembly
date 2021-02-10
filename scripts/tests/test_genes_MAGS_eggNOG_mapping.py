import os
import glob
import pytest
import pandas.util.testing as pdt

from os.path import join
from click.testing import CliRunner

from scripts.genes_MAGS_eggNOG_mapping import _perform_mapping
from scripts.tests.utils import dict2str, load_df

runner = CliRunner()

INPATH = join(os.getcwd(), "data/input")
EXPPATH = join(os.getcwd(), "data/expected")
OUTPATH = join(os.getcwd(), "data/generated/genes_mags_eggnog")


@pytest.fixture(scope="session", autouse=True)
def clean_generated_files():
    print("\nRemoving old generated files...")
    if not os.path.exists(OUTPATH):
        os.makedirs(OUTPATH)
    for f in glob.glob(join(OUTPATH, '*')):
        os.remove(f)
    assert glob.glob(join(OUTPATH, '*')) == []


def test_help():
    response = runner.invoke(_perform_mapping, ["--help"])
    assert response.exit_code == 0
    assert "Script for mapping genes to contigs" in response.output


def test_basic():
    params = {'-r': join(INPATH, 'cluster_genes/nr.reduced.clstr'),
              '-g': join(INPATH, 'cluster_genes/sample_genes.fa'),
              '-c': join(INPATH, 'assemble/merged.min500.contigs.fa'),
              '-b': join(INPATH, 'metabat2/'),
              '-t': join(INPATH, 'gtdbtk/'),
              '-m': join(INPATH, 'checkm/'),
              '-e': join(INPATH, 'eggnog-mapper/eggNOG_reduced.tsv'),
              '-o': join(OUTPATH, 'mapped_genes.tsv'),
              '-f': join(OUTPATH, 'clusters.tsv')}
    response = runner.invoke(_perform_mapping, f"{dict2str(params)}")
    assert response.exit_code == 0
    # Compare clusters
    clstr_out = load_df(os.path.join(OUTPATH, "clusters.tsv"), squeeze=True)
    clstr_exp = load_df(os.path.join(EXPPATH, "clstr.tsv"), squeeze=True)
    pdt.assert_series_equal(clstr_out, clstr_exp)
    # Compare mapped genes
    genes_out = load_df(os.path.join(OUTPATH, "mapped_genes.tsv"))
    genes_exp = load_df(os.path.join(EXPPATH, "mapped_genes.tsv"))
    pdt.assert_frame_equal(genes_out, genes_exp)


def test_missing_checkm():
    params = {'-r': join(INPATH, 'cluster_genes/nr.reduced.clstr'),
              '-g': join(INPATH, 'cluster_genes/sample_genes.fa'),
              '-c': join(INPATH, 'assemble/merged.min500.contigs.fa'),
              '-b': join(INPATH, 'metabat2/'),
              '-t': join(INPATH, 'gtdbtk/'),
              '-m': join(INPATH, 'empty/'),  # difference wrt basic
              '-e': join(INPATH, 'eggnog-mapper/eggNOG_reduced.tsv'),
              '-o': join(OUTPATH, 'mapped_genes_missing_checkm.tsv'),
              '-f': join(OUTPATH, 'clusters_missing_checkm.tsv')}
    response = runner.invoke(_perform_mapping, f"{dict2str(params)}")
    assert response.exit_code == 0
    # Compare clusters
    clstr_out = load_df(os.path.join(OUTPATH, "clusters_missing_checkm.tsv"),
                        squeeze=True)
    clstr_exp = load_df(os.path.join(EXPPATH, "clustr_missing_checkm.tsv"),
                        squeeze=True)
    pdt.assert_series_equal(clstr_out, clstr_exp)
    # Compare mapped genes
    genes_out = load_df(os.path.join(OUTPATH,
                                     "mapped_genes_missing_checkm.tsv"))
    genes_exp = load_df(os.path.join(EXPPATH,
                                     "mapped_genes_missing_checkm.tsv"))
    pdt.assert_frame_equal(genes_out, genes_exp)


def test_missing_checkm_and_gtdb():
    params = {'-r': join(INPATH, 'cluster_genes/nr.reduced.clstr'),
              '-g': join(INPATH, 'cluster_genes/sample_genes.fa'),
              '-c': join(INPATH, 'assemble/merged.min500.contigs.fa'),
              '-b': join(INPATH, 'metabat2/'),
              '-t': join(INPATH, 'empty/'),  # difference wrt basic
              '-m': join(INPATH, 'empty/'),  # difference wrt basic
              '-e': join(INPATH, 'eggnog-mapper/eggNOG_reduced.tsv'),
              '-o': join(OUTPATH, 'mapped_genes_missing_checkm_gtdb.tsv'),
              '-f': join(OUTPATH, 'clusters_missing_checkm_gtdb.tsv')}
    response = runner.invoke(_perform_mapping, f"{dict2str(params)}")
    assert response.exit_code == 0
    # Compare clusters
    clstr_out = load_df(os.path.join(OUTPATH,
                        "clusters_missing_checkm_gtdb.tsv"), squeeze=True)
    clstr_exp = load_df(os.path.join(EXPPATH,
                        "clustr_missing_checkm_gtdb.tsv"), squeeze=True)
    pdt.assert_series_equal(clstr_out, clstr_exp)
    # Compare mapped genes
    genes_out = load_df(os.path.join(OUTPATH,
                                     "mapped_genes_missing_checkm_gtdb.tsv"))
    genes_exp = load_df(os.path.join(EXPPATH,
                                     "mapped_genes_missing_checkm_gtdb.tsv"))
    pdt.assert_frame_equal(genes_out, genes_exp)