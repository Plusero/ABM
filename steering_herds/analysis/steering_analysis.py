import glob
import re

import click
import numpy as np
import pandas as pd

from analysis import caging_metrics, steering_metrics, collective_metrics
from utils import sorting


@click.command()
@click.option('--params_filename', type=str, default="params.csv")
@click.option('--scenario', type=str, default="predator")
@click.option('--eta', type=float, default=0.5)
@click.option('--seed_start', type=int, default=0)
@click.option('--seed_end', type=int, default=2)
@click.option('--in_folder', type=str, default="")
@click.option('--out_folder', type=str, default="")
def analyse(params_filename="",
            scenario="predator",
            eta=0.5,
            seed_start=0,
            seed_end=1,
            in_folder="",
            out_folder=""):
    mu = 19.
    v_h_max = 2.
    e_star = 2 * v_h_max + eta
    r_star = mu + e_star

    e_steer = v_h_max
    R_star = r_star + mu / 2

    _metrics = []

    if scenario == "predator":
        _metrics.extend([
            # _metric('DP', 'steering', steering_metrics.metric_distance_predator(), True, 0),
            _metric('DPNP', 'steering', steering_metrics.metric_distance_predator_nearest_prey(), True, 0),
            _metric('NPIP', 'steering', steering_metrics.metric_number_of_prey_in_proximity(mu), True, 0),
            _metric('DPIP', 'steering', steering_metrics.metric_duration_of_prey_in_proximity(mu), False, 0),
        ])

    if scenario == "patches":
        _metrics.extend([
            _metric('NPIR=19', 'steering', steering_metrics.metric_number_of_prey_in_range(mu), True, 0),
            _metric('NPIR=28.5', 'steering', steering_metrics.metric_number_of_prey_in_range(mu+mu/2), True, 0),
        ])

    if scenario == "enclosure":
        _metrics.extend([
            _metric('RDE', 'steering', steering_metrics.metric_relative_distance_enclosure(), True, 0),
            _metric('RDEFP', 'steering', steering_metrics.metric_relative_distance_enclosure_furthest_prey(), True, 0),
            _metric('NPOE=0', 'steering', steering_metrics.metric_number_of_prey_out_enclosure(), True, 0),
            _metric('NPOE=9.5', 'steering', steering_metrics.metric_number_of_prey_out_enclosure(mu/2), True, 0),
            _metric('DPOE', 'steering', steering_metrics.metric_duration_of_prey_out_enclosure(), False, 0),
        ])

    # additional caging metrics
    _metrics.extend([
        _metric('DUE', 'caging', caging_metrics.metric_distance_upper_error(R_star), True, 0),
        _metric('DLE', 'caging', caging_metrics.metric_distance_lower_error(R_star), True, 0),
        _metric('CP', 'caging', caging_metrics.metric_caging_probability(2 * mu), True, 0),
        _metric('CER', 'caging', caging_metrics.metric_convex_enclosure_rate(), True, 0)
    ])

    # additional collective metrics
    _metrics.extend([
        _metric('HC', 'couzin', collective_metrics.metric_herd_connectivity(2 * mu), True, 0),
        _metric('HO', 'couzin', collective_metrics.metric_herd_order(), True, 0)
    ])

    params_df = pd.read_csv(params_filename)
    variable_names = list(params_df.columns)

    for metric in _metrics:
        measure_data(in_folder=in_folder,
                     out_folder=out_folder,
                     metric=metric,
                     variable_names=variable_names,
                     seed_start=seed_start,
                     seed_end=seed_end)


def _metric(of, model, func, time_variant, t_0):
    return {'of': of, 'model': model, 'func': func, 'time_variant': time_variant, 't_0': t_0}


def measure_data(in_folder,
                 out_folder,
                 metric,
                 variable_names,
                 seed_start,
                 seed_end):
    files = {"A": [], "S": [], "Z": []}
    for file_type in files.keys():
        filenames = glob.glob(f'{in_folder}*TYPE={file_type}*')
        filenames.sort(key=sorting.natural_keys)
        files[file_type] = filenames
    data = {'Measurement': [], 'seed': []}
    if metric['time_variant']:
        data['time'] = []
    for var_name in variable_names:
        data[var_name] = []

    if len(files["A"]) < 1:
        print("NO FILES")
        return
    if len(files["A"]) != len(files["S"]) != len(files["Z"]):
        print("MISSING FILES")
        return
    n_files = len(files["A"])

    for i in range(n_files):
        seed = int(re.search('SEED=([0-9]*).npy', files["A"][i]).group(1))
        if seed in range(seed_start, seed_end):
            try:
                data_array_agent = np.load(files["A"][i])
                data_array_school = np.load(files["S"][i])
                if metric['model'] == 'steering':
                    data_array_zone = np.load(files["Z"][i])
            except IndexError:
                print("IndexError")
            except ValueError:
                print("ValueError")

            metric_func = metric['func']

            t_max = data_array_agent.shape[0]

            if metric['time_variant']:
                t_0 = metric['t_0']
                time_points = list(range(t_0, t_max))
                for t in time_points:
                    if metric['model'] == 'steering':
                        data_point = metric_func(t, data_array_agent, data_array_school, data_array_zone)
                    else:
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
            else:
                if metric['model'] == 'steering':
                    data_point = metric_func(data_array_agent, data_array_school, data_array_zone)
                else:
                    data_point = metric_func(data_array_agent, data_array_school)
                data['Measurement'].append(data_point)
                data['seed'].append(i)
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
            if metric['model'] == 'steering':
                data_array_zone = None

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
