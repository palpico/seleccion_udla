# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import inspect

from dash import Dash, html, dcc, dash_table as dt
import pandas as pd
from math import exp
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = ['https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css']
# <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet"
# integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">

sdf = pd.read_excel("./data/new_structure.xlsx", sheet_name="score_short")
ldf = pd.read_excel("./data/new_structure.xlsx", sheet_name="score_long")
cdf = pd.read_excel("./data/new_structure.xlsx", sheet_name="carreras")
ldf_vars_raw = list(ldf["variable"].unique())
sdf_vars_raw = list(sdf["variable"].unique())
cdf_vars_raw = list(cdf["variable"].unique())

exclusions_ldf = ['edad', 'edad_madre', 'edad_padre', 'ciclo', 'pension', 'edad madre', 'edad padre']
exclusions_sdf = ['ingreso_familiar']
exclusions_cdf = []
mid_exclusions = ['variable', 'detalle', 'scorecard puntaje']

ldf_vars = [ld for ld in ldf_vars_raw if ld not in exclusions_ldf]
sdf_vars = [sd for sd in sdf_vars_raw if sd not in exclusions_sdf]
cdf_vars = [cd.strip().replace(',', '').replace('.', '').replace('-', ' ') for cd in cdf_vars_raw if
            cd not in exclusions_cdf]
mid_table_cols = [col for col in ldf.columns.tolist() if col not in mid_exclusions]
res1_table_cols = ["[0,897)", "[897,1635)", "[1635,2440)", "[2440,4447)", "[4447,o mas)"]
res2_table_cols = ["Probabilidad Seleccionada", "Segunda Probabilidad Seleccionada"]
res3_table_cols = ["Ingreso Predicho"]


def generate_text(arg_vars, arg_exclusion):
    results = []
    for sv in arg_vars:
        if sv not in arg_exclusion:
            results.append(html.Div([
                html.Label(f"{sv.capitalize()}: ", htmlFor=f"text-{sv}"),
                dcc.Input(id=f"text-{sv}", type='number', className="form-control", placeholder=sv)
            ], className="col"))
    return results


def generate_dropdown(arg_df, arg_vars, arg_exclusion):
    results = []
    for lv in arg_vars:
        if lv not in arg_exclusion:
            opt = list(set(arg_df[arg_df["variable"] == lv]["detalle"].tolist()))
            results.append(
                html.Div([
                    # html.Label(f"{lv.capitalize()}: "),
                    html.Label(f"{lv.capitalize()}: ", htmlFor=f"dropdown-{lv}"),
                    dcc.Dropdown(options=opt,
                                 multi=False,
                                 className="form-control",
                                 placeholder=lv,
                                 id=f"dropdown-{lv}")
                ], className='col')
            )
    return results


def create_args(arg_list):
    tmp_args = []
    for k, a in enumerate(arg_list):
        tmp_args.extend(a)
    return tmp_args


# test_aegs = create_args([sdf_vars, ldf_vars, cdf_vars])


def get_inputs(arg_df, arg_type):
    results = [Input(component_id=f"{arg_type}-{inp}", component_property="value") for inp in arg_df]
    return results


def all_inputs():
    results = []
    results.extend(get_inputs(sdf_vars, "text"))
    results.extend(get_inputs(ldf_vars, "dropdown"))
    results.extend(get_inputs(cdf_vars, "dropdown"))
    return results


def find_value(arg_df, arg_var, arg_detail, arg_col, arg_wherevar="variable", arg_wheredetail="detalle"):
    result = arg_df[(arg_df[arg_wherevar] == arg_var) & (arg_df[arg_wheredetail] == arg_detail)][arg_col].values[0]
    return result


def find_row(arg_df, arg_var, arg_detail='', arg_wherevar="variable", arg_wheredetail="detalle"):
    result = arg_df.loc[(arg_df[arg_wherevar] == arg_var) & (arg_df[arg_wheredetail] == arg_detail), mid_table_cols]
    return result


def calculate_mid(arg_values):
    source = {'sdf': [ldf, sdf_vars], 'ldf': [ldf, ldf_vars], 'cdf': [cdf, cdf_vars]}
    params = []
    data = []
    for k, c in source.items():
        for c1 in c[1]:
            params.append([c[0], c1])
    for k, v in enumerate(arg_values):
        if k < len(sdf_vars) and v:
            params[k].append(params[k][1])
            calc = (find_row(*params[k]) * v)
            data.append(calc)
        else:
            params[k].append(v)
            data.append(find_row(*params[k]))
    intercept = pd.DataFrame([[2500, 4064.8383, 15465.058, 3192.68, 4734.2118,
                               1601.3896, -1.86824595, -0.801066225, -0.693240875,
                               0.449318975, 1.710622275]], columns=mid_table_cols)
    data.append(intercept)
    results = pd.concat(data, ignore_index=True)
    return results


def calculate_response(arg_df):
    suma = list(arg_df.filter(items=res1_table_cols).sum(axis=0, skipna=True))
    exponencial = [exp(v) for v in suma]
    sumatotal = sum(exponencial)
    probabilidad = [v / sumatotal for v in exponencial]
    result = [suma, exponencial, ["{:.0%}".format(p) for p in probabilidad]]
    r2r1 = []
    r2r2 = []
    tops = sorted(range(len(probabilidad)), key=lambda i: probabilidad[i], reverse=True)[:2]
    for t in tops:
        r2r1.append(probabilidad[t])
        r2r2.append(res1_table_cols[t])
    r3r1 = {}
    for k, r in enumerate(r2r2):
        newr = r.replace('\'', '') \
            .replace('[', '').replace(']', '') \
            .replace('(', '').replace(')', '') \
            .replace('o mas', '99999999').split(',')
        newr = min([int(n) for n in newr])
        r3r1[newr] = r2r2[k]
    res1 = pd.DataFrame(result, columns=res1_table_cols)
    res2 = pd.DataFrame([r2r1, r2r2], columns=res2_table_cols)
    res3 = pd.DataFrame([r3r1[min(r3r1.keys())]], columns=res3_table_cols)
    return res1, res2, res3


app = Dash(__name__,
           suppress_callback_exceptions=True,
           external_stylesheets=external_stylesheets
           )

app.layout = html.Div([
    html.H1('Seccion 4', style={'text-align': 'center', 'width': '100%', 'color': '#98002E'}),
    html.Div(['Student data:',
              html.Div([*generate_text(sdf_vars, exclusions_sdf)], className="row"),
              html.Div([*generate_dropdown(ldf, ldf_vars, exclusions_ldf)], className="row"),
              html.Div([*generate_dropdown(cdf, cdf_vars, exclusions_cdf)], className="row")
              ], className="container"),
    html.H4('Results:', style={'text-align': 'center', 'width': '100%'}),
    html.Div(id='dt-result1'),
    html.Br(),
    html.Div(id='dt-result2'),
    html.Br(),
    html.Div(id='dt-result3'),
    html.Br(),
    html.Button('Toggle show used values.', id='button-mid', style={'display': 'block'}),
    html.Div(id='dt-mid-parent', style={'display': 'none'},
             children=[
                 html.Div(id='dt-mid', className="table table-striped")
             ]),
])


@app.callback(
    [Output('dt-result1', 'children'),
     Output('dt-result2', 'children'),
     Output('dt-result3', 'children'),
     Output('dt-mid', 'children')],
    [all_inputs()]
)
def generate_table(*args):
    mid_df = calculate_mid(args)
    mid_data = mid_df.to_dict(orient='records')
    mid_columns = [{"name": i, "id": i} for i in mid_df.columns]
    res1_columns = [{"name": i, "id": i} for i in res1_table_cols]
    res2_columns = [{"name": i, "id": i} for i in res2_table_cols]
    res3_columns = [{"name": i, "id": i} for i in res3_table_cols]
    mid = dt.DataTable(data=mid_data, columns=mid_columns, export_format="xlsx", style_header={
        'fontWeight': 'bold',
        'backgroundColor': 'gray',
    })
    res1_data, res2_data, res3_data = calculate_response(mid_df)
    res1 = dt.DataTable(data=res1_data.to_dict(orient='records'), columns=res1_columns, style_header={
        'fontWeight': 'bold',
        'backgroundColor': 'gray',
    })
    res2 = dt.DataTable(data=res2_data.to_dict(orient='records'), columns=res2_columns, style_header={
        'fontWeight': 'bold',
        'backgroundColor': 'gray',
    })
    res3 = dt.DataTable(data=res3_data.to_dict(orient='records'), columns=res3_columns, style_header={
        'fontWeight': 'bold',
        'backgroundColor': 'gray',
    })
    return res1, res2, res3, mid


@app.callback(
    Output(component_id='dt-mid-parent', component_property='style'),
    Input(component_id='button-mid', component_property='n_clicks'),
    State(component_id='dt-mid-parent', component_property='style')
)
def show_mid(n_clicks, arg_state):
    visibility = {'none': 'block', 'block': 'none'}
    if n_clicks is None:
        raise PreventUpdate
    result = visibility[arg_state['display']]
    return {'display': result}


if __name__ == '__main__':
    app.run_server(debug=True)
