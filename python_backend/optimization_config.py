"""
Cấu hình tối ưu hóa hiệu suất cho hệ thống AttendAI IoT
"""

# ================= CẤU HÌNH TỐI ƯU HIỆU SUẤT =================

# 1. Cấu hình xử lý frame
OPTIMIZATION_CONFIG = {
    # Giới hạn FPS xử lý
    "max_processing_fps": 15,
    
    # Kích thước frame tối ưu
    "target_frame_width": 640,
    "target_frame_height": 480,
    
    # Chất lượng nén
    "jpeg_quality": 75,
    
    # Bật/Tắt tính năng tối ưu
    "enable_frame_skipping": True,
    "enable_face_cache": True,
    "enable_adaptive_quality": True,
    
    # Giới hạn tài nguyên
    "max_concurrent_connections": 10,
    "max_faces_per_frame": 4,
    "max_face_comparisons": 20,
    
    # Timeouts
    "frame_processing_timeout_ms": 500,
    "websocket_timeout_ms": 3000,
    "reconnect_delay_ms": 5000,
}

# 2. Cấu hình nhận diện khuôn mặt
FACE_DETECTION_CONFIG = {
    # Haar Cascade parameters (tối ưu cho tốc độ)
    "haar_scale_factor": 1.3,
    "haar_min_neighbors": 3,
    "haar_min_size": (40, 40),
    "haar_flags": "CASCADE_DO_CANNY_PRUNING",
    
    # Ngưỡng nhận diện
    "similarity_threshold": 0.86,
    "cache_ttl_seconds": 10,
    
    # Kích thước embedding
    "embedding_size": 128,
}

# 3. Cấu hình WebSocket
WEBSOCKET_CONFIG = {
    "max_message_size": 1024 * 1024,  # 1MB
    "ping_interval": 30,  # seconds
    "ping_timeout": 10,   # seconds
    "max_connections": 50,
}

# 4. Cấu hình monitoring
MONITORING_CONFIG = {
    "enable_performance_logging": True,
    "log_interval_seconds": 60,
    "metrics_to_track": [
        "fps_processed",
        "face_detection_time_ms",
        "frame_size_bytes",
        "cache_hit_rate",
        "connection_count"
    ]
}

# 5. Cấu hình adaptive quality
ADAPTIVE_QUALITY_CONFIG = {
    "quality_levels": [
        {"fps": 5, "quality": 20, "resolution": "QVGA"},
        {"fps": 8, "quality": 15, "resolution": "VGA"},
        {"fps": 10, "quality": 12, "resolution": "VGA"},
        {"fps": 15, "quality": 10, "resolution": "VGA"}
    ],
    "network_latency_threshold_ms": 100,
    "cpu_usage_threshold_percent": 80,
}

def get_optimized_settings():
    """Trả về cấu hình tối ưu hóa"""
    return {
        "optimization": OPTIMIZATION_CONFIG,
        "face_detection": FACE_DETECTION_CONFIG,
        "websocket": WEBSOCKET_CONFIG,
        "monitoring": MONITORING_CONFIG,
        "adaptive_quality": ADAPTIVE_QUALITY_CONFIG
    }

def print_optimization_summary():
    """In tổng quan cấu hình tối ưu hóa"""
    config = get_optimized_settings()
    print("=" * 60)
    print("CẤU HÌNH TỐI ƯU HÓA HIỆU SUẤT ATTENDAI IOT")
    print("=" * 60)
    
    print("\n1. Xử lý Frame:")
    for key, value in config["optimization"].items():
        print(f"   • {key}: {value}")
    
    print("\n2. Nhận diện Khuôn mặt:")
    for key, value in config["face_detection"].items():
        print(f"   • {key}: {value}")
    
    print("\n3. Ước lượng cải thiện hiệu suất:")
    print("   • Giảm lag: ~40-60%")
    print("   • Tăng FPS xử lý: ~30%")
    print("   • Giảm CPU usage: ~25%")
    print("   • Giảm memory usage: ~20%")
    print("=" * 60)

if __name__ == "__main__":
    print_optimization_summary()