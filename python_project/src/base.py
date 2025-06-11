from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import hydra
import numpy as np
import pandas as pd
import torch
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf

import utils


# --- Configuration ---
@dataclass
class FeatureConfig:
    categorical_features: List[str] = field(default_factory=list)
    numerical_features: List[str] = field(default_factory=list)
    # Add other feature-related configurations as needed


@dataclass
class DataConfig:
    data_path: str = "path/to/your/data.csv"
    output_dir: str = "output/"
    features: FeatureConfig = field(default_factory=FeatureConfig)
    # Add other data-related configurations as needed


@dataclass
class ModelConfig:
    input_dim: Any = None  # To be set dynamically
    hidden_dim: int = 64
    lr: float = 0.001
    epochs: int = 10
    batch_size: int = 32
    # Add other model-specific configurations as needed


@dataclass
class TrainingConfig:
    seed: int = 42
    device: str = "cpu"  # "cuda" if GPU is available
    model: ModelConfig = field(default_factory=ModelConfig)
    # Add other training-related configurations as needed


@dataclass
class ProjectConfig:
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    debug: bool = False


cs = ConfigStore.instance()
cs.store(name="base_config", node=ProjectConfig)
# You can also register sub-configs for more modularity
# cs.store(group="data", name="base_data", node=DataConfig)
# cs.store(group="model", name="base_model", node=ModelConfig)


# --- Data Processing Functions ---
def load_and_preprocess_data(cfg: ProjectConfig) -> Tuple[pd.DataFrame, List[str]]:
    """
    Load raw data and perform initial preprocessing.
    Args:
        cfg: Hydra configuration object.
    Returns:
        A tuple containing the preprocessed DataFrame and a list of feature column names.
    """
    print("Loading and preprocessing data...")

    # Placeholder:
    processed_df = pd.DataFrame()  # Replace with your actual processed data
    feature_columns = []  # Replace with your actual feature columns
    print(f"Data loaded. Shape: {processed_df.shape}, Features: {len(feature_columns)}")
    return processed_df, feature_columns


def create_grouped_data(
    processed_df: pd.DataFrame, feature_columns: List[str], cfg: ProjectConfig
) -> List[Dict[str, Any]]:
    """
    Group data by a specific key (e.g., race_id) and prepare it for model input.
    Args:
        processed_df: The preprocessed DataFrame.
        feature_columns: List of feature column names.
        cfg: Hydra configuration object.
    Returns:
        A list of dictionaries, where each dictionary represents a group (e.g., a race).
    """
    print("Creating grouped data...")
    grouped_data_list = []
    # --- Add your grouping logic here ---
    # Example: Group by 'ID' (race_id)
    # for group_id, group_df in processed_df.groupby("ID"):
    #     features_tensor = torch.FloatTensor(group_df[feature_columns].values)
    #     relevance_tensor = torch.FloatTensor(group_df["relevance"].values)
    #     grouped_data_list.append({
    #         "race_id": group_id,
    #         "features": features_tensor,
    #         "relevance": relevance_tensor,
    #         "num_items": len(group_df)
    #     })
    print(f"Grouped data created. Number of groups: {len(grouped_data_list)}")
    return grouped_data_list


def scale_features(
    train_data: List[Dict[str, Any]],
    val_data: List[Dict[str, Any]],
    test_data: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    pass
    return train_data, val_data, test_data


# --- Main ---
@hydra.main(config_path=None, config_name="base_config", version_base=None)
def main(cfg: ProjectConfig) -> None:
    """
    Main function to run the data processing and model training/evaluation pipeline.
    Args:
        cfg: Hydra configuration object.
    """
    print("Starting project...")
    print(f"Configuration:\n{OmegaConf.to_yaml(cfg)}")

    # Set seed for reproducibility
    utils.seed_torch(cfg.training.seed)

    # 1. Load and preprocess data
    processed_df, feature_columns = load_and_preprocess_data(cfg)
    if processed_df.empty or not feature_columns:
        print("No data or features after preprocessing. Exiting.")
        return

    print("\nProject finished.")


if __name__ == "__main__":
    main()
