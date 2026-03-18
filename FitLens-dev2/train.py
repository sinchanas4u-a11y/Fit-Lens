"""
Training script for Keypoint R-CNN model
"""
import os
import torch
from detectron2.engine import DefaultTrainer
from detectron2.evaluation import COCOEvaluator
from detectron2.data import build_detection_train_loader, build_detection_test_loader
from detectron2.data import DatasetMapper
import detectron2.data.transforms as T

from config import Config
from model_arch import ModelTrainer
from dataset import prepare_datasets, visualize_dataset_sample


class CustomTrainer(DefaultTrainer):
    """Custom trainer with evaluation"""
    
    @classmethod
    def build_evaluator(cls, cfg, dataset_name):
        """Build evaluator for validation"""
        return COCOEvaluator(dataset_name, cfg, False, output_dir=cfg.OUTPUT_DIR)
    
    @classmethod
    def build_train_loader(cls, cfg):
        """Build training data loader with augmentation"""
        mapper = DatasetMapper(
            cfg,
            is_train=True,
            augmentations=[
                T.RandomFlip(prob=0.5, horizontal=True, vertical=False),
                T.RandomBrightness(0.8, 1.2),
                T.RandomContrast(0.8, 1.2),
                T.RandomSaturation(0.8, 1.2),
            ]
        )
        return build_detection_train_loader(cfg, mapper=mapper)


def train_model(resume: bool = False):
    """
    Train Keypoint R-CNN model
    
    Args:
        resume: Whether to resume from checkpoint
    """
    print("=" * 60)
    print("Training Keypoint R-CNN for Body Measurement")
    print("=" * 60)
    
    # Create output directories
    Config.create_directories()
    
    # Prepare datasets
    prepare_datasets()
    
    # Initialize trainer
    trainer = ModelTrainer(output_dir=Config.CHECKPOINT_DIR)
    
    # Setup training configuration
    print("\nSetting up training configuration...")
    cfg = trainer.setup_training_config(
        dataset_name="coco_person_train",
        num_classes=1
    )
    
    print(f"\nTraining Configuration:")
    print(f"  Device: {cfg.MODEL.DEVICE}")
    print(f"  Batch Size: {cfg.SOLVER.IMS_PER_BATCH}")
    print(f"  Learning Rate: {cfg.SOLVER.BASE_LR}")
    print(f"  Max Iterations: {cfg.SOLVER.MAX_ITER}")
    print(f"  Checkpoint Period: {cfg.SOLVER.CHECKPOINT_PERIOD}")
    print(f"  Output Directory: {cfg.OUTPUT_DIR}")
    
    # Check if CUDA is available
    if torch.cuda.is_available():
        print(f"\n✓ CUDA available: {torch.cuda.get_device_name(0)}")
        print(f"  Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
    else:
        print("\n⚠ CUDA not available. Training on CPU (will be slow)")
    
    # Create trainer
    print("\nInitializing trainer...")
    custom_trainer = CustomTrainer(cfg)
    
    # Resume or start fresh
    custom_trainer.resume_or_load(resume=resume)
    
    # Start training
    print("\n" + "=" * 60)
    print("Starting training...")
    print("=" * 60 + "\n")
    
    try:
        custom_trainer.train()
        print("\n✓ Training completed successfully!")
        
        # Save final model
        final_model_path = os.path.join(Config.CHECKPOINT_DIR, "model_final.pth")
        print(f"\n✓ Final model saved to: {final_model_path}")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Training interrupted by user")
        print(f"Checkpoints saved in: {Config.CHECKPOINT_DIR}")
    
    except Exception as e:
        print(f"\n✗ Training failed with error: {e}")
        raise


def evaluate_model(checkpoint_path: str):
    """
    Evaluate trained model
    
    Args:
        checkpoint_path: Path to model checkpoint
    """
    print("=" * 60)
    print("Evaluating Keypoint R-CNN Model")
    print("=" * 60)
    
    # Prepare datasets
    prepare_datasets()
    
    # Initialize trainer
    trainer = ModelTrainer(output_dir=Config.CHECKPOINT_DIR)
    cfg = trainer.setup_training_config(
        dataset_name="coco_person_val",
        num_classes=1
    )
    
    # Load checkpoint
    cfg.MODEL.WEIGHTS = checkpoint_path
    
    print(f"\nEvaluating model: {checkpoint_path}")
    print(f"Dataset: coco_person_val")
    
    # Run evaluation
    results = ModelTrainer.evaluate_model(cfg, "coco_person_val")
    
    print("\n" + "=" * 60)
    print("Evaluation Results:")
    print("=" * 60)
    for key, value in results.items():
        print(f"  {key}: {value}")
    
    return results


def visualize_training_data(num_samples: int = 5):
    """
    Visualize training data samples
    
    Args:
        num_samples: Number of samples to visualize
    """
    print("Visualizing training data samples...")
    prepare_datasets()
    visualize_dataset_sample("coco_person_train", num_samples)


def main():
    """Main training entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Keypoint R-CNN for Body Measurement")
    parser.add_argument("--mode", type=str, default="train", 
                       choices=["train", "eval", "visualize"],
                       help="Mode: train, eval, or visualize")
    parser.add_argument("--resume", action="store_true",
                       help="Resume training from checkpoint")
    parser.add_argument("--checkpoint", type=str, default=None,
                       help="Path to checkpoint for evaluation")
    parser.add_argument("--samples", type=int, default=5,
                       help="Number of samples to visualize")
    
    args = parser.parse_args()
    
    if args.mode == "train":
        train_model(resume=args.resume)
    
    elif args.mode == "eval":
        if args.checkpoint is None:
            # Use latest checkpoint
            checkpoint_path = os.path.join(Config.CHECKPOINT_DIR, "model_final.pth")
        else:
            checkpoint_path = args.checkpoint
        
        if not os.path.exists(checkpoint_path):
            print(f"✗ Checkpoint not found: {checkpoint_path}")
            return
        
        evaluate_model(checkpoint_path)
    
    elif args.mode == "visualize":
        visualize_training_data(num_samples=args.samples)


if __name__ == "__main__":
    main()
