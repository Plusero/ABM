import glob
import re

import click
import numpy as np
import pandas as pd

from analysis import caging_metrics as metrics, collective_metrics
from utils import sorting


@click.command()
@click.option('--params_filename', type=str, default="params.csv")
@click.option('--seed_start', type=int, default=0)
@click.option('--seed_end', type=int, default=10)
@click.option('--in_folder', type=str, default="")
@click.option('--out_folder', type=str, default="")
def analyse(params_filename="",
            seed_start=0,
            seed_end=1,
            in_folder="",
            out_folder="", ):
    _metrics = [
        _metric('CP', metrics.metric_caging_probability(38.), True, 0),
        _metric('DUE', metrics.metric_distance_upper_error(19.), True, 0),
        _metric('DLE', metrics.metric_distance_lower_error(19.), True, 0),
        # _metric('CER', metrics.metric_convex_enclosure_rate(), True, 0),
        # _metric('MNAD', metrics.metric_max_nearest_agent_distance(), True, 0),
        _metric('MCA', metrics.metric_min_caging_agents(38.), False, 0),
        _metric('HD', collective_metrics.metric_herd_density(), True, 0),
        _metric('HC', collective_metrics.metric_herd_connectivity(38.), True, 0),
    ]

    params_df = pd.read_csv(params_filename)
    variable_names = list(params_df.columns)

    for metric in _metrics:
        measure_data(in_folder=in_folder,
                     out_folder=out_folder,
                     metric=metric,
                     variable_names=variable_names,
                     seed_start=seed_start,
                     seed_end=seed_end,)


def _metric(of, func, time_variant, t_0):
    return {'of': of, 'func': func, 'time_variant': time_variant, 't_0': t_0}


def measure_data(in_folder,
                 out_folder,
                 metric,
                 variable_names,
                 seed_start,
                 seed_end):
    files = {"A": [], "S": []}
    for file_type in files.keys():
        filenames = glob.glob(f'{in_folder}*TYPE={file_type}*')
        filenames.sort(key=sorting.natural_keys)
        files[file_type] = filenames

    data = {'Measurement': [], 'seed': [], 'time': []}
    for var_name in variable_names:
        data[var_name] = []

    if len(files["A"]) < 1:
        print("NO FILES")
        return
    if len(files["A"]) != len(files["S"]):
        print("MISSING FILES")
        return
    n_files = len(files["A"])

    for i in range(n_files):
        seed = int(re.search('SEED=([0-9]*).npy', files["A"][i]).group(1))
        if seed in range(seed_start, seed_end):
            try:
                data_array_agent = np.load(files["A"][i])
                data_array_school = np.load(files["S"][i])
            except IndexError:
                print("IndexError")
            except ValueError:
                print("ValueError")

            metric_func = metric['func']

            t_max = data_array_agent.shape[0]

            if metric['time_variant']:
                t_0 = metric['t_0']
            else:
                t_0 = t_max - 1
            time_points = list(range(t_0, t_max))
            for t in time_points:
                data_point = metric_func(t, data_array_agent, data_array_school)
                data['Measurement'].append(data_point)
                data['time'].append(t)
                data['seed'].append(seed)
                for var_name in variable_names:
                    val_postfix = files["A"][i].split(f'{var_name}=')[1]
                    var_value = val_postfix.split('_')[0]
                    if var_value.isnumeric():
                        try:
                            value = int(var_value)
                        except ValueError:
                            value = float(var_value)
                    else:
                        value = var_value
                    data[var_name].append(value)
            data_array_agent, data_array_school = None, None

    # Store data
    df = pd.DataFrame(data=data)

    out_fix = files["A"][0].split('TYPE=A_')
    prefixes = out_fix[0]
    prefix = prefixes.split("/")[-1]
    suffix = out_fix[1].split('SEED')[0]
    for var_name in variable_names:
        suffix = re.sub(f'^{var_name}=[^_]*_', '', suffix)
        suffix = re.sub(f'_{var_name}=[^_]*_', '_', suffix)
    output_filepath = out_folder + prefix + suffix + metric["of"] + f'_{seed_start}-{seed_end}.pkl'
    df.to_pickle(output_filepath)


analyse()
