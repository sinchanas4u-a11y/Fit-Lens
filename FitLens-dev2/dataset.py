"""
Dataset loading and preprocessing for training Keypoint R-CNN
"""
import os
import json
import cv2
import numpy as np
from typing import List, Dict, Tuple
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.structures import BoxMode
import albumentations as A
from config import Config


class COCOKeypointDataset:
    """COCO dataset loader for keypoint detection"""
    
    def __init__(self, json_file: str, image_root: str):
        """
        Initialize COCO dataset
        
        Args:
            json_file: Path to COCO annotations JSON
            image_root: Root directory containing images
        """
        self.json_file = json_file
        self.image_root = image_root
        
        with open(json_file, 'r') as f:
            self.coco_data = json.load(f)
        
        self.images = {img['id']: img for img in self.coco_data['images']}
        self.annotations = self._group_annotations()
    
    def _group_annotations(self) -> Dict[int, List[Dict]]:
        """Group annotations by image_id"""
        grouped = {}
        for ann in self.coco_data['annotations']:
            img_id = ann['image_id']
            if img_id not in grouped:
                grouped[img_id] = []
            grouped[img_id].append(ann)
        return grouped
    
    def get_detectron2_dicts(self) -> List[Dict]:
        """
        Convert COCO format to Detectron2 format
        
        Returns:
            List of dataset dictionaries
        """
        dataset_dicts = []
        
        for img_id, img_info in self.images.items():
            record = {}
            
            # Image info
            filename = os.path.join(self.image_root, img_info['file_name'])
            record["file_name"] = filename
            record["image_id"] = img_id
            record["height"] = img_info['height']
            record["width"] = img_info['width']
            
            # Annotations
            if img_id in self.annotations:
                objs = []
                for ann in self.annotations[img_id]:
                    # Only include person class with keypoints
                    if ann['category_id'] == 1 and 'keypoints' in ann:
                        obj = {
                            "bbox": ann['bbox'],
                            "bbox_mode": BoxMode.XYWH_ABS,
                            "category_id": 0,  # Person class
                            "keypoints": ann['keypoints'],
                        }
                        objs.append(obj)
                
                record["annotations"] = objs
                
                # Only include images with at least one person
                if len(objs) > 0:
                    dataset_dicts.append(record)
        
        return dataset_dicts


class DataAugmentation:
    """Data augmentation pipeline for training"""
    
    @staticmethod
    def get_training_augmentation() -> A.Compose:
        """
        Get augmentation pipeline for training
        
        Returns:
            Albumentations composition
        """
        return A.Compose([
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.3),
            A.HueSaturationValue(p=0.3),
            A.GaussNoise(p=0.2),
            A.Blur(blur_limit=3, p=0.2),
            A.RandomScale(scale_limit=0.2, p=0.5),
        ], keypoint_params=A.KeypointParams(format='xy', remove_invisible=False))
    
    @staticmethod
    def get_validation_augmentation() -> A.Compose:
        """Get augmentation pipeline for validation (minimal)"""
        return A.Compose([], keypoint_params=A.KeypointParams(format='xy'))


def register_coco_dataset(name: str, json_file: str, image_root: str):
    """
    Register COCO dataset with Detectron2
    
    Args:
        name: Dataset name
        json_file: Path to annotations JSON
        image_root: Root directory for images
    """
    def dataset_function():
        dataset = COCOKeypointDataset(json_file, image_root)
        return dataset.get_detectron2_dicts()
    
    DatasetCatalog.register(name, dataset_function)
    MetadataCatalog.get(name).set(
        thing_classes=["person"],
        keypoint_names=Config.KEYPOINT_NAMES,
        keypoint_flip_map=[
            ("left_eye", "right_eye"),
            ("left_ear", "right_ear"),
            ("left_shoulder", "right_shoulder"),
            ("left_elbow", "right_elbow"),
            ("left_wrist", "right_wrist"),
            ("left_hip", "right_hip"),
            ("left_knee", "right_knee"),
            ("left_ankle", "right_ankle"),
        ]
    )


class SyntheticDataGenerator:
    """Generate synthetic pose data for testing/training"""
    
    @staticmethod
    def generate_synthetic_pose(image_size: Tuple[int, int] = (720, 1280)) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate a synthetic pose image with keypoints
        
        Args:
            image_size: (height, width) of output image
            
        Returns:
            (image, keypoints) tuple
        """
        height, width = image_size
        
        # Create blank image
        image = np.ones((height, width, 3), dtype=np.uint8) * 200
        
        # Generate random but realistic keypoints
        # Center person in frame
        center_x = width // 2
        center_y = height // 2
        
        # Scale factor for body proportions
        scale = min(width, height) // 4
        
        # Generate keypoints (17 keypoints in COCO format)
        keypoints = np.zeros((17, 3))
        
        # Head
        keypoints[0] = [center_x, center_y - scale * 1.5, 1.0]  # nose
        keypoints[1] = [center_x - 10, center_y - scale * 1.6, 1.0]  # left_eye
        keypoints[2] = [center_x + 10, center_y - scale * 1.6, 1.0]  # right_eye
        keypoints[3] = [center_x - 20, center_y - scale * 1.6, 1.0]  # left_ear
        keypoints[4] = [center_x + 20, center_y - scale * 1.6, 1.0]  # right_ear
        
        # Upper body
        keypoints[5] = [center_x - scale * 0.4, center_y - scale * 1.0, 1.0]  # left_shoulder
        keypoints[6] = [center_x + scale * 0.4, center_y - scale * 1.0, 1.0]  # right_shoulder
        keypoints[7] = [center_x - scale * 0.7, center_y - scale * 0.3, 1.0]  # left_elbow
        keypoints[8] = [center_x + scale * 0.7, center_y - scale * 0.3, 1.0]  # right_elbow
        keypoints[9] = [center_x - scale * 0.9, center_y + scale * 0.3, 1.0]  # left_wrist
        keypoints[10] = [center_x + scale * 0.9, center_y + scale * 0.3, 1.0]  # right_wrist
        
        # Lower body
        keypoints[11] = [center_x - scale * 0.3, center_y + scale * 0.2, 1.0]  # left_hip
        keypoints[12] = [center_x + scale * 0.3, center_y + scale * 0.2, 1.0]  # right_hip
        keypoints[13] = [center_x - scale * 0.3, center_y + scale * 1.0, 1.0]  # left_knee
        keypoints[14] = [center_x + scale * 0.3, center_y + scale * 1.0, 1.0]  # right_knee
        keypoints[15] = [center_x - scale * 0.3, center_y + scale * 1.8, 1.0]  # left_ankle
        keypoints[16] = [center_x + scale * 0.3, center_y + scale * 1.8, 1.0]  # right_ankle
        
        # Draw stick figure on image
        from pose_utils import SkeletonDrawer
        image = SkeletonDrawer.draw_skeleton(image, keypoints, (0, 0, 255))
        
        return image, keypoints


def prepare_datasets():
    """Prepare and register all datasets"""
    print("Registering datasets...")
    
    # Check if COCO dataset exists
    if os.path.exists(Config.TRAIN_JSON):
        register_coco_dataset(
            "coco_person_train",
            Config.TRAIN_JSON,
            Config.TRAIN_IMAGES
        )
        print("✓ Registered COCO training dataset")
    else:
        print("⚠ COCO training dataset not found. Using synthetic data for demo.")
    
    if os.path.exists(Config.VAL_JSON):
        register_coco_dataset(
            "coco_person_val",
            Config.VAL_JSON,
            Config.VAL_IMAGES
        )
        print("✓ Registered COCO validation dataset")
    else:
        print("⚠ COCO validation dataset not found.")


def visualize_dataset_sample(dataset_name: str, num_samples: int = 5):
    """
    Visualize samples from dataset
    
    Args:
        dataset_name: Name of registered dataset
        num_samples: Number of samples to visualize
    """
    from detectron2.utils.visualizer import Visualizer
    from detectron2.data import DatasetCatalog, MetadataCatalog
    import random
    
    dataset_dicts = DatasetCatalog.get(dataset_name)
    metadata = MetadataCatalog.get(dataset_name)
    
    for d in random.sample(dataset_dicts, min(num_samples, len(dataset_dicts))):
        img = cv2.imread(d["file_name"])
        visualizer = Visualizer(img[:, :, ::-1], metadata=metadata, scale=0.5)
        vis = visualizer.draw_dataset_dict(d)
        
        cv2.imshow("Dataset Sample", vis.get_image()[:, :, ::-1])
        cv2.waitKey(0)
    
    cv2.destroyAllWindows()


if __name__ == "__main__":
    """Test dataset loading"""
    print("Testing dataset loading...")
    
    # Test synthetic data generation
    print("\nGenerating synthetic pose...")
    image, keypoints = SyntheticDataGenerator.generate_synthetic_pose()
    
    print(f"Generated image shape: {image.shape}")
    print(f"Keypoints shape: {keypoints.shape}")
    
    cv2.imshow("Synthetic Pose", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    print("\n✓ Dataset module test complete")
