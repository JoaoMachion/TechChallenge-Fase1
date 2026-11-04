"""Gera arquivos .ipynb (formato v4) a partir de listas de células."""
import json
import textwrap


def md(text):
    return {"cell_type": "markdown", "metadata": {},
            "source": textwrap.dedent(text).strip("\n").splitlines(keepends=True)}


def code(text):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [],
            "source": textwrap.dedent(text).strip("\n").splitlines(keepends=True)}


def write(path, cells):
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    for i, c in enumerate(nb["cells"]):
        c["id"] = f"cell-{i:03d}"
    json.dump(nb, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


SETUP = """
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd().parent / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from olist_utils import *

set_style()
pd.set_option("display.max_columns", 30)
pd.set_option("display.float_format", lambda v: f"{v:,.2f}")
"""
