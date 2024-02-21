# Steering herds away from dangers: an approach to shepherding by decentralized caging
Stef Van Havermaet et al. 2022

## Install

Language: Python3.9 \
Packages: requirements.txt

```
# Ubuntu commands
sudo apt-get -y update
sudo apt-get -y install software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa

sudo apt-get -y install python3.9 python3.9-dev

sudo pip install -r requirements.txt
```

## Run

Follow the guided instructions to replicate the results presented in the paper.

### Collective movement (Quantitative herd measurements without robotic agents):

e.g.
```
python -m experiments.collective_movement --n_seeds="10" --t_max="3000"
```

varying `zoo_s` and `zoa_s` each over `[10, 20, ..., 100]`,\
for the following different models:

* `model_s="METRIC"`
* `model_s="TOPOLOGICAL"` with `knn_s=50`
* `model_s="VISUAL"`
* `model_s="LONGRANGE"` with `knn_s=7` and `klr_s=0.1`


with default parameters apart from:
* `n_seeds=10`
* `t_max=3000`

analysing the metrics:

* Relative area (A_r) by `collective_metrics.metric_herd_density()`
* Number of fragmented groups (N_G) by `collective_metrics.metric_herd_connectivity(38)`
* Theoretical minimum number of agents to cage N_{A,min} by `caging_metrics.metric_caging_probability(38)` 

with z_i = 19.

### Caging (Ratio of robots successfully caging):

e.g.
```
python -m experiments.caging_movement --n_seeds="10" --t_max="3000"
```
varying `n_agents` in `[10, 20, 30]`, and \
varying `zoo_s` and `zoa_s` each over `[10, 20, ..., 100]`,\
for the following different models:

* `model_s="METRIC"`
* `model_s="TOPOLOGICAL"` with `knn_s=50`
* `model_s="VISUAL"`
* `model_s="LONGRANGE"` with `knn_s=7` and `klr_s=0.1`

with default parameters apart from:
* `n_seeds=10`
* `t_max=4500`
* `n_school=10`

analysing the metrics:
`caging_metrics.metric_caging_probability`

### Shepherding (Fraction of endangered herd):

e.g.
```
python -m experiments.steering_movement --n_seeds="10" --t_max="3000"
```

for the following different scenarios:
* `scenario="patches"`
* `scenario="enclosure"`

with default parameters apart from:
* `n_seeds=10`
* `t_max=6000`
* `model_s="METRIC"`

analysing the metrics:
* "patches" with `steering_metrics.metric_number_of_prey_in_range(19)`
* "enclosure" with `steering_metrics.metric_number_of_prey_out_enclosure()`

## Data/Results

See the `data` folder, it is structured by the paper subsections and collective models or shepherding scenarios. 
The files contain analysed results and are named after abbreviations of the corresponding measurements (see analysis python files). 

