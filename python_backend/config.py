"""
Cấu hình production cho hệ thống AttendAI IoT
"""

import os
from typing import Dict, Any

# ================= CẤU HÌNH PRODUCTION =================

class ProductionConfig:
    """Cấu hình cho môi trường production"""
    
    # Cấu hình WebSocket
    WEBSOCKET_CONFIG: Dict[str, Any] = {
        "port": 3000,
        "address": "0.0.0.0",
        "max_buffer_size": 100 * 1024 * 1024,  # 100MB
        "max_connections": 50,
        "ping_interval": 30,  # seconds
        "ping_timeout": 10,   # seconds
    }
    
    # Cấu hình nhận diện khuôn mặt
    FACE_RECOGNITION_CONFIG: Dict[str, Any] = {
        "similarity_threshold": 0.86,
        "max_faces_per_frame": 4,
        "max_face_comparisons": 20,
        "cache_ttl_seconds": 10,
        "skip_frame_ratio": 3,  # Xử lý 1 frame, bỏ 2 frame
    }
    
    # Cấu hình hiệu suất
    PERFORMANCE_CONFIG: Dict[str, Any] = {
        "max_workers": 4,
        "target_frame_width": 640,
        "target_frame_height": 480,
        "frame_processing_timeout_ms": 500,
        "enable_frame_skipping": True,
        "enable_face_cache": True,
    }
    
    # Cấu hình file paths
    PATHS_CONFIG: Dict[str, str] = {
        "known_faces_dir": "known_faces",
        "attendance_log": "attendance_log.csv",
        "face_registrations": "face_registrations.csv",
        "templates_dir": "templates",
    }
    
    # Cấu hình admin
    ADMIN_CONFIG: Dict[str, str] = {
        "username": "admin",
        "password": "abc@123",  # NÊN THAY ĐỔI TRONG PRODUCTION!
    }
    
    # Cấu hình logging
    LOGGING_CONFIG: Dict[str, Any] = {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "file": "app.log",
        "max_size_mb": 10,
        "backup_count": 5,
    }
    
    @classmethod
    def get_config(cls) -> Dict[str, Dict[str, Any]]:
        """Trả về toàn bộ cấu hình"""
        return {
            "websocket": cls.WEBSOCKET_CONFIG,
            "face_recognition": cls.FACE_RECOGNITION_CONFIG,
            "performance": cls.PERFORMANCE_CONFIG,
            "paths": cls.PATHS_CONFIG,
            "admin": cls.ADMIN_CONFIG,
            "logging": cls.LOGGING_CONFIG,
        }
    
    @classmethod
    def print_summary(cls):
        """In tổng quan cấu hình"""
        print("=" * 60)
        print("CẤU HÌNH PRODUCTION - ATTENDAI IOT")
        print("=" * 60)
        
        config = cls.get_config()
        
        print("\n1. WebSocket Configuration:")
        for key, value in config["websocket"].items():
            print(f"   • {key}: {value}")
        
        print("\n2. Face Recognition Configuration:")
        for key, value in config["face_recognition"].items():
            print(f"   • {key}: {value}")
        
        print("\n3. Performance Configuration:")
        for key, value in config["performance"].items():
            print(f"   • {key}: {value}")
        
        print("\n4. Security Notes:")
        print("   • ĐỔI MẬT KHẨU ADMIN trong production!")
        print("   • Sử dụng HTTPS/WSS trong production")
        print("   • Bật firewall và giới hạn IP truy cập")
        print("   • Regular backup CSV files")
        
        print("\n5. Deployment Checklist:")
        print("   [ ] Đổi mật khẩu admin")
        print("   [ ] Cấu hình domain/SSL certificate")
        print("   [ ] Setup monitoring (CPU, memory, network)")
        print("   [ ] Configure firewall rules")
        print("   [ ] Test với nhiều camera đồng thời")
        print("   [ ] Setup auto-restart (systemd/supervisor)")
        
        print("\n" + "=" * 60)


class DevelopmentConfig(ProductionConfig):
    """Cấu hình cho môi trường development (kế thừa từ ProductionConfig)"""
    
    # Override một số cấu hình cho development
    PERFORMANCE_CONFIG = {
        **ProductionConfig.PERFORMANCE_CONFIG,
        "max_workers": 2,  # Giảm worker cho development
        "skip_frame_ratio": 2,  # Xử lý nhiều frame hơn
    }
    
    LOGGING_CONFIG = {
        **ProductionConfig.LOGGING_CONFIG,
        "level": "DEBUG",  # Log chi tiết hơn
    }


def get_config(env: str = "production") -> Dict[str, Dict[str, Any]]:
    """Lấy cấu hình dựa trên môi trường"""
    if env.lower() == "development":
        return DevelopmentConfig.get_config()
    else:
        return ProductionConfig.get_config()


if __name__ == "__main__":
    ProductionConfig.print_summary()