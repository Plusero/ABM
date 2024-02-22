import sys  # nopep8
print(sys.path)  # nopep8
sys.path.append('..')  # nopep8

import click  # nopep8
import numpy as np  # nopep8

from experiments.collective_2d import run_simulation  # nopep8
from experiments.visualization import collective_visuals  # nopep8


@click.command()
@click.option('--n_seeds', type=int, default=1)
@click.option('--init_seed', type=int, default=0)
@click.option('--n_school', type=int, default=10)
@click.option('--model_s', type=str, default="METRIC")
@click.option('--knn_s', type=int, default=13)
@click.option('--klr_s', type=float, default=0.05)
@click.option('--kor_s', type=float, default=100.)
@click.option('--koo_s', type=float, default=50.)
@click.option('--koa_s', type=float, default=1.)
@click.option('--rho_s', type=float, default=0.01)
@click.option('--sigma_s', type=float, default=0.05)
@click.option('--v_s_max', type=float, default=2.)
@click.option('--w_s_max', type=float, default=np.pi / 3)
@click.option('--zor_s', type=float, default=1.0)
@click.option('--zoo_s', type=float, default=None)
@click.option('--zoa_s', type=float, default=None)
@click.option('--zoo_m_s', type=float, default=1.5)
@click.option('--zoa_m_s', type=float, default=1.0)
@click.option('--t_max', type=int, default=500)
@click.option('--save_folder', type=str, default="")
@click.option('--visualization', type=bool, default=False)
def run(n_seeds=1,
        init_seed=0,
        n_school=10,
        model_s="METRIC",
        knn_s=7,
        klr_s=0.1,
        kor_s=100.,
        koo_s=50.,
        koa_s=1.,
        rho_s=0.01,
        sigma_s=0.05,
        v_s_max=2.,
        w_s_max=np.pi / 3,
        zor_s=1.0,
        zoo_s=None,
        zoa_s=None,
        zoo_m_s=1.5,
        zoa_m_s=1.0,
        t_max=3 * 10 ** 3,
        save_folder="",
        visualization=False):
    size_s = np.sqrt(n_school / rho_s)
    if zoo_s is None:
        zoo_s = zoo_m_s * size_s
    if zoa_s is None:
        zoa_s = zoa_m_s * size_s

    filename = 'POSES_COLLECTIVE_TYPE={TYPE}_' + \
               f'NS={n_school}_' + \
               f'MODELS={model_s}_' + \
               f'KNNS={knn_s}_' + \
               f'KLRS={klr_s}_' + \
               f'KORS={kor_s}_' + \
               f'KOOS={koo_s}_' + \
               f'KOAS={koa_s}_' + \
               f'ZORS={zor_s}_' + \
               f'ZOOS={zoo_s}_' + \
               f'ZOAS={zoa_s}' + \
               '_SEED={SEED}'

    for seed in range(init_seed, init_seed + n_seeds):
        school_poses = run_simulation(n_school=n_school,
                                      model_s=model_s,
                                      knn_s=knn_s,
                                      klr_s=klr_s,
                                      zor_s=zor_s,
                                      zoo_s=zoo_s,
                                      zoa_s=zoa_s,
                                      kor_s=kor_s,
                                      koo_s=koo_s,
                                      koa_s=koa_s,
                                      sigma_s=sigma_s,
                                      rho_s=rho_s,
                                      v_s_max=v_s_max,
                                      w_s_max=w_s_max,
                                      t_max=t_max, )
        np.save(save_folder + filename.format(TYPE="S",
                SEED=seed) + ".npy", school_poses)

        if visualization:
            collective_visuals.run(seed, school_poses)


run()
