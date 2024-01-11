# Traffic light optimization with low penetration rate vehicle trajectory data

[![DOI](https://zenodo.org/badge/730009195.svg)](https://zenodo.org/doi/10.5281/zenodo.10493793)

## Introduction

In this project, we implement the queueing model and probabilistic time-space
(PTS) diagram in OSaaS paper.
Based on calibrated arrival curves, PTS diagram of a corridor can be generated.
With the PTS diagram, we can optimize the traffic signal control to improve the
traffic efficiency.

We also provide the code to reproduce the figures in the paper.


### Project structure

The project is structured as follows:

```plain
.
├── data                      # Data folder for demo and reproducing figures
├── LICENSE                   # License file
├── demo.py                   # Demo from calibrated curves to PTS diagram
├── models                    # Data structure and utility functions for calibrated curves
├── mtldp                     # Data structure for traffic network
├── output                    # Output folder for generated pts diagram
├── plot                      # Functions for plotting 
├── pts                       # Dynamics of the queueing model
├── README.md                 # Readme file
└── requirements.txt          # Dependencies
```

## Getting Started

### Prerequisites

#### Python

This project is tested on Python 3.8.13 under Ubuntu 22.04, macOS 12.6, and Windows 11.

#### Virtual Environment

Virtual environment is highly recommended. It can help you
avoid most dependency issue and reproducible problems.

You can use [Anaconda](https://docs.anaconda.com/anaconda/install/index.html)
or [Miniconda](https://docs.conda.io/en/latest/miniconda.html), or you can use python
standard library [venv](https://docs.python.org/3.8/library/venv.html).

Anaconda/Miniconda will be used in the following documentation.

### Usage

### Get the source code

Get the source code via `git clone` command.
```shell
$ git clone git@github.com:michigan-traffic-lab/osaas-public.git
$ cd osaas-public
```

#### Create virtual environment

```shell
$ conda create -n osaas python=3.8.13 -y
$ conda activate osaas
(osaas) $
```

#### Install the dependencies

```shell
(osaas) $ pip install -r requirements.txt
```

#### Run

```shell
(osaas) $ python demo.py
```

This command will generate the PTS diagram for the corridor 'Adams Rd'.
It will first generate the PTS diagram based on its old offset. And then it will
generate the PTS diagram based on the optimized offset. Generated PTS diagrams
will be saved in `output/demo` folder.

```shell
(osaas) $ python paper_figures.py
```
This command will generate all the non-illustration figures in the paper.
Generated figures will be saved in `output/figures` folder.


## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the [PolyForm Noncommercial License 1.0.0]. Please refer to LICENSE for more details.

H. L. and the team have filed a US provisional patent application 18/308,996.

## Developers

Xingmin Wang (xingminw@umich.edu)

Zihao Wang (zihaooo@umich.edu)

Zachary Jerome (zjerome@umich.edu)


## Contact

For general questions about the paper, please contact Henry Liu (henryliu@umich.edu).