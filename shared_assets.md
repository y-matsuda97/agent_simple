## File .devcontainer/devcontainer.json
```json
{
    "name": "app",
    "dockerComposeFile": [
        "../docker-compose.yml"
    ],
    "service": "app",
    "workspaceFolder": "/work",
    "shutdownAction": "stopCompose",
    "customizations": {
        "vscode": {
            "settings": {
                "terminal.integrated.shell.linux": "/bin/bash",
                "python.defaultInterpreterPath": "/usr/bin/python3.11",
                "editor.formatOnSave": true,
                "black-formatter.args": [
                    "--line-length",
                    "88"
                ],
                "flake8.args": [
                    "--max-line-length=88",
                    "--ignore=E203,W503,W504"
                ]
            },
            "extensions": [
                "ms-azuretools.vscode-docker",
                "ms-python.python",
                "ms-python.black-formatter",
                "ms-python.flake8",
                "ms-python.vscode-pylance",
                "ms-python.debugpy",
                "donjayamanne.githistory",
                "GitHub.vscode-pull-request-github",
                "shd101wyy.markdown-preview-enhanced",
                "phplasma.csv-to-table"
            ]
        }
    },
    "forwardPorts": [
        8000
    ]
}

```
## File .devcontainer/Dockerfile
```dockerfile
FROM nvidia/cuda:12.2.2-devel-ubuntu22.04
USER root

ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN apt-get update && apt-get install -y \
    locales \
    vim less \
    wget \
    gcc-11 \
    g++-11 \
    python3.11 \
    python3-pip \
    git \
    #libcudnn8=8.1.1.*-1+cuda12.2 \
    #libcudnn8-dev=8.1.1.*-1+cuda12.2 \
    && localedef -f UTF-8 -i ja_JP ja_JP.UTF-8 \
    && apt-mark hold libcudnn8 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 \
    && update-alternatives --set python /usr/bin/python3.11

RUN python -m pip install --upgrade pip setuptools \
    && python -m pip install jupyterlab

COPY .devcontainer/base-requirements.txt /tmp/base-requirements.txt
RUN pip install -r /tmp/base-requirements.txt

COPY .devcontainer/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

RUN  mkdir -p /work
WORKDIR /work

```
## File .vscode/launch.json
```json
{
    // Use IntelliSense to learn about possible attributes.
    // Hover to view descriptions of existing attributes.
    // For more information, visit: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: predict_ytest_ListMLE.py",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/predict_ytest_ListMLE.py",
            "console": "integratedTerminal"
        }
    ]
}

```
## File conf/config.yaml
```yaml
# Hydra Configuration for Keirin Prediction Model

defaults:
  - data: default
  - model: listmle
  - _self_

# Data splitting
data_split:
  test_size: 0.05
  val_size: 0.15

# Training parameters
training:
  seed: 42
  device: "cuda"
  ndcg_k: 3

# Debug mode
debug: true

```
## File .gitignore
```text
venv/
.devcontainer/
docker-compose.yml
__pycache__/
agent_simple/
data/
output/
outputs/

```
## File docker-compose.yml
```yaml
services:
  app:
    build:
      context: .
      dockerfile: .devcontainer/Dockerfile
    #env_file:
    #  - .devcontainer/.env
    volumes:
      - .:/work
    command: "tail -F anything"
    ports:
      - 5678:5678
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              capabilities: [ utility, compute, video ]

```
## File src/utils.py
```python
import os
import random

import numpy as np
import torch


def seed_torch(seed=42):
    """
    乱数シードを設定する関数。

    Args:
        seed (int): 設定する乱数シード値。デフォルトは42。
    """
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

```
