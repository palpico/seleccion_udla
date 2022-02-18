# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc
import pandas as pd
from dash.dependencies import Input, Output

sdf = pd.read_excel("./data/new_structure.xlsx", sheet_name="score_short")
ldf = pd.read_excel("./data/new_structure.xlsx", sheet_name="score_long")
cdf = pd.read_excel("./data/new_structure.xlsx", sheet_name="carreras")
ldf_vars_raw = list(set(ldf["variable"].tolist()))
sdf_vars_raw = list(set(sdf["variable"].tolist()))
cdf_vars_raw = list(set(cdf["carreras"].tolist()))

exclusions_ldf = ['edad', 'edad madre', 'edad padre', 'pension_long', 'ciclo']
exclusions_sdf = ['ingreso_familiar']
exclusions_cdf = []
ldf_vars = [ld for ld in ldf_vars_raw if ld not in exclusions_ldf]
sdf_vars = [sd for sd in sdf_vars_raw if sd not in exclusions_sdf]
# cdf_vars = [c for c in cdf_vars_raw if c not in exclusions_cdf]
cdf_vars = [cd.strip().replace(',', '').replace('.', '').replace('-', ' ') for cd in cdf_vars_raw if
            cd not in exclusions_cdf]


def generate_text(arg_df):
    textls = []
    for sv in arg_df:
        textls.append(dcc.Input(id=f"text-{sv}", type="number", placeholder=sv))
    return textls


def generate_dropdown(arg_df):
    ddls = []
    print(ddls)
    for lv in arg_df:
        opt = list(set(ldf[ldf["variable"] == lv]["detalle"].tolist()))
        print(lv, ' -- ', opt)
        ddls.append(dcc.Dropdown(
            options=opt,
            multi=False,
            placeholder=lv,
            id=f"dropdown-{lv}"))
    print(ddls)
    return ddls


def generate_dropdown_cdf():
    return dcc.Dropdown(
        cdf_vars,
        multi=False,
        placeholder='carreras',
        id=f"dropdown-carreras"
    )


app = Dash(__name__, suppress_callback_exceptions=True)

app.layout = html.Div([
    *generate_text(sdf_vars),
    *generate_dropdown(ldf_vars),
    generate_dropdown_cdf(),
    dcc.Textarea(id="output")
])

args = ldf_vars
args.extend(sdf_vars)
args = [f"arg_{a}" for a in sdf_vars]
args.append("carreras")


def get_inputs_ldf(arg_df):
    inputsl = []
    for inp in arg_df:
        inputsl.append(Input(component_id=f"dropdown-{inp}", component_property="value"))
    return inputsl


def get_inputs_sdf(arg_df):
    inputss = []
    for inp in arg_df:
        inputss.append(Input(component_id=f"text-{inp}", component_property="value"))
    return inputss
    # return [component_id=Input(f"text-{sv}", component_property="value") for sv in sdf_vars]


def get_inputs_cdf():
    return Input(component_id=f"dropdown-carreras", component_property="value")


@app.callback(
    Output("output", "children"),
    get_inputs_ldf(ldf_vars),
    get_inputs_sdf(sdf_vars),
    get_inputs_cdf(),
)
def generate_table(**kwargs):
    return f"{[arg for arg in kwargs]}"


if __name__ == '__main__':
    app.run_server(debug=True)
