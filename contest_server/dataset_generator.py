import json
import random
from datetime import datetime, timedelta
from pathlib import Path
import uuid

class UnlabeledDatasetGenerator:
    def __init__(self):
        self.base_url = "https://storage.googleapis.com/dataset/images"
        self.start_date = datetime(2024, 1, 1)
        
        # Камеры для разных типов задач
        self.cameras = {
            "classification": ["Canon EOS 5D", "Nikon D850", "Sony A7 III", "Fujifilm X-T4"],
            "object_detection": ["Traffic Camera X-200", "Security Cam Pro", "Street Monitor 4K", "Urban Scanner HD"],
            "segmentation": ["Sentinel-2", "Landsat-8", "WorldView-3", "GeoEye-1"],
            "keypoint": ["Kinect v2", "Azure Kinect DK", "Intel RealSense D455", "Orbbec Astra Pro"]
        }
        
        # Локации для объектов
        self.locations = [
            {"latitude": 55.7558, "longitude": 37.6173},  # Москва
            {"latitude": 59.9343, "longitude": 30.3351},  # Санкт-Петербург
            {"latitude": 56.8389, "longitude": 60.6057},  # Екатеринбург
            {"latitude": 55.0084, "longitude": 82.9357},  # Новосибирск
        ]
        
        # Условия съемки
        self.weather_conditions = ["sunny", "cloudy", "overcast", "rainy", "clear"]
        self.times_of_day = ["morning", "afternoon", "evening", "night"]
        self.environments = ["urban", "suburban", "rural", "industrial"]
        
    def generate_classification_data(self, index: int) -> dict:
        """Генерация данных для задачи классификации"""
        image_size = random.choice([(224, 224), (299, 299), (384, 384), (512, 512)])
        return {
            "image_id": f"cls_{uuid.uuid4().hex[:8]}",
            "image_url": f"{self.base_url}/classification_{index:03d}.jpg",
            "metadata": {
                "timestamp": (self.start_date + timedelta(hours=index*2)).isoformat(),
                "camera": random.choice(self.cameras["classification"]),
                "resolution": [1920, 1080],
                "format": "JPEG",
                "size_bytes": random.randint(1000000, 5000000)
            },
            "preprocessing": {
                "resize": list(image_size),
                "normalize": True,
                "color_space": "RGB",
                "augmentation": {
                    "horizontal_flip": random.choice([True, False]),
                    "rotation_range": random.randint(0, 30),
                    "brightness_range": [0.8, 1.2]
                }
            }
        }

    def generate_object_detection_data(self, index: int) -> dict:
        """Генерация данных для задачи обнаружения объектов"""
        location = random.choice(self.locations)
        return {
            "image_id": f"det_{uuid.uuid4().hex[:8]}",
            "image_url": f"{self.base_url}/detection_{index:03d}.jpg",
            "metadata": {
                "timestamp": (self.start_date + timedelta(hours=index*2)).isoformat(),
                "location": location,
                "weather": random.choice(self.weather_conditions),
                "time_of_day": random.choice(self.times_of_day),
                "camera": random.choice(self.cameras["object_detection"])
            },
            "image_properties": {
                "width": random.choice([1920, 2560, 3840]),
                "height": random.choice([1080, 1440, 2160]),
                "channels": 3,
                "format": "JPEG"
            },
            "scene_context": {
                "environment": random.choice(self.environments),
                "lighting": random.choice(["daylight", "artificial", "mixed", "low_light"]),
                "weather_conditions": random.choice(self.weather_conditions),
                "traffic_density": random.choice(["low", "medium", "high"])
            },
            "bbox_format": {
                "coordinate_system": "top_left",
                "units": "pixels"
            }
        }

    def generate_segmentation_data(self, index: int) -> dict:
        """Генерация данных для задачи сегментации"""
        location = random.choice(self.locations)
        resolution = random.choice([10, 20, 30])
        size = random.choice([(2048, 2048), (4096, 4096), (8192, 8192)])
        return {
            "image_id": f"seg_{uuid.uuid4().hex[:8]}",
            "image_url": f"{self.base_url}/segmentation_{index:03d}.jpg",
            "metadata": {
                "timestamp": (self.start_date + timedelta(hours=index*2)).isoformat(),
                "satellite": random.choice(self.cameras["segmentation"]),
                "bands": ["RGB", "NIR", "SWIR"],
                "cloud_coverage": round(random.uniform(0, 0.3), 2),
                "resolution_meters": resolution,
                "acquisition_date": (self.start_date + timedelta(days=index)).strftime("%Y-%m-%d")
            },
            "image_properties": {
                "width": size[0],
                "height": size[1],
                "channels": random.choice([3, 4, 8]),
                "format": "GeoTIFF"
            },
            "geographic_info": {
                "projection": "EPSG:4326",
                "bounds": {
                    "north": location["latitude"] + 0.01,
                    "south": location["latitude"] - 0.01,
                    "east": location["longitude"] + 0.01,
                    "west": location["longitude"] - 0.01
                },
                "pixel_size": [resolution, resolution]
            },
            "mask_format": {
                "encoding": "rle",
                "size": list(size),
                "classes_expected": random.randint(5, 10)
            }
        }

    def generate_keypoint_data(self, index: int) -> dict:
        """Генерация данных для задачи определения ключевых точек"""
        return {
            "image_id": f"kpt_{uuid.uuid4().hex[:8]}",
            "image_url": f"{self.base_url}/keypoint_{index:03d}.jpg",
            "metadata": {
                "timestamp": (self.start_date + timedelta(hours=index*2)).isoformat(),
                "camera": random.choice(self.cameras["keypoint"]),
                "capture_type": "RGB-D",
                "subject_distance_meters": round(random.uniform(1.5, 4.0), 1),
                "session_id": f"session_{index//5:02d}"
            },
            "image_properties": {
                "width": random.choice([1280, 1920, 2560]),
                "height": random.choice([720, 1080, 1440]),
                "channels": 3,
                "format": "JPEG"
            },
            "depth_data": {
                "available": True,
                "format": "uint16",
                "units": "millimeters",
                "min_depth": random.randint(400, 600),
                "max_depth": random.randint(4000, 5000),
                "frame_aligned": True
            },
            "keypoint_format": {
                "coordinate_system": "image_coordinates",
                "origin": "top_left",
                "units": "pixels",
                "skeleton_format": "COCO"
            },
            "capture_conditions": {
                "lighting": random.choice(["indoor", "outdoor", "studio"]),
                "background": random.choice(["neutral", "complex", "green_screen"]),
                "occlusion": random.choice(["minimal", "moderate", "significant"]),
                "motion_blur": random.choice(["none", "slight", "moderate"])
            }
        }

    def generate_dataset(self, num_files: int = 50, output_dir: str = "dataset") -> None:
        """Генерация датасета"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Удаляем старые файлы raw_*.json
        for old_file in output_path.glob("raw_*.json"):
            old_file.unlink()
        
        generators = [
            self.generate_classification_data,
            self.generate_object_detection_data,
            self.generate_segmentation_data,
            self.generate_keypoint_data
        ]
        
        for i in range(num_files):
            # Выбираем генератор случайным образом
            generator = random.choice(generators)
            data = generator(i)
            
            # Сохраняем файл
            file_path = output_path / f"raw_{i+1:03d}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Generated {num_files} unlabeled dataset files in {output_dir}/")

if __name__ == "__main__":
    generator = UnlabeledDatasetGenerator()
    generator.generate_dataset() 