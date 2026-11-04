"""
Executor mínimo de notebooks (.ipynb v4) sem dependência de Jupyter.
Executa as células de código em sequência num namespace compartilhado e grava
as saídas (texto, tabelas HTML e figuras PNG) dentro do próprio notebook.

Uso:  python tools/run_notebook.py notebooks/01_x.ipynb [...]
(Em um ambiente com Jupyter, o equivalente é:
 jupyter nbconvert --to notebook --execute --inplace notebooks/*.ipynb)
"""
import ast
import base64
import contextlib
import io
import json
import os
import sys
import traceback

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def _fig_outputs():
    outs = []
    for num in plt.get_fignums():
        fig = plt.figure(num)
        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight", dpi=100, facecolor="white")
        outs.append({
            "output_type": "display_data",
            "data": {"image/png": base64.b64encode(buf.getvalue()).decode(),
                     "text/plain": [f"<Figure {fig.get_size_inches()[0]*100:.0f}x"
                                    f"{fig.get_size_inches()[1]*100:.0f}>"]},
            "metadata": {},
        })
    plt.close("all")
    return outs


def _rich(value, count):
    data = {"text/plain": repr(value).splitlines(keepends=True)}
    if hasattr(value, "_repr_html_"):
        try:
            html = value._repr_html_()
            if html:
                data["text/html"] = html.splitlines(keepends=True)
        except Exception:
            pass
    return {"output_type": "execute_result", "execution_count": count,
            "data": data, "metadata": {}}


def run(path):
    nb = json.load(open(path, encoding="utf-8"))
    nb_dir = os.path.dirname(os.path.abspath(path))
    cwd = os.getcwd()
    os.chdir(nb_dir)
    ns = {"__name__": "__main__"}
    count = 0
    ok = True
    try:
        for cell in nb["cells"]:
            if cell["cell_type"] != "code":
                continue
            count += 1
            src = "".join(cell["source"])
            outputs = []
            stdout = io.StringIO()
            # display() simples para uso dentro das células
            def display(v, _out=outputs, _so=stdout):
                if _so.getvalue():
                    _out.append({"output_type": "stream", "name": "stdout",
                                 "text": _so.getvalue().splitlines(keepends=True)})
                    _so.seek(0)
                    _so.truncate(0)
                _out.extend(_fig_outputs())
                r = _rich(v, None)
                r["output_type"] = "display_data"
                _out.append(r)
            ns["display"] = display

            def show(*a, _out=outputs, _so=stdout, **k):
                if _so.getvalue():
                    _out.append({"output_type": "stream", "name": "stdout",
                                 "text": _so.getvalue().splitlines(keepends=True)})
                    _so.seek(0)
                    _so.truncate(0)
                _out.extend(_fig_outputs())
            plt.show = show
            try:
                tree = ast.parse(src)
                last = None
                if tree.body and isinstance(tree.body[-1], ast.Expr):
                    last = ast.Expression(tree.body.pop().value)
                with contextlib.redirect_stdout(stdout):
                    exec(compile(tree, f"<cell {count}>", "exec"), ns)
                    result = eval(compile(last, f"<cell {count}>", "eval"), ns) if last else None
                if stdout.getvalue():
                    outputs.append({"output_type": "stream", "name": "stdout",
                                    "text": stdout.getvalue().splitlines(keepends=True)})
                outputs.extend(_fig_outputs())
                if result is not None and not repr(result).startswith(("<matplotlib", "[<matplotlib", "Text(")):
                    outputs.append(_rich(result, count))
            except Exception as e:
                ok = False
                tb = traceback.format_exc()
                outputs.append({"output_type": "error", "ename": type(e).__name__,
                                "evalue": str(e), "traceback": tb.splitlines()})
                print(f"ERRO em {path}, célula {count}:\n{tb}", file=sys.stderr)
            # remove 'execution_count' None dos display_data
            for o in outputs:
                if o["output_type"] == "display_data":
                    o.pop("execution_count", None)
            cell["outputs"] = outputs
            cell["execution_count"] = count
            if not ok:
                break
    finally:
        os.chdir(cwd)
    json.dump(nb, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return ok


if __name__ == "__main__":
    results = {p: run(p) for p in sys.argv[1:]}
    for p, ok in results.items():
        print(("OK   " if ok else "FALHOU ") + p)
    sys.exit(0 if all(results.values()) else 1)
