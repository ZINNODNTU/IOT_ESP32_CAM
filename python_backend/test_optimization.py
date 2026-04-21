"""
Script test tối ưu hóa - kiểm tra các thay đổi đã được áp dụng
"""

import ast
import re

def check_optimizations():
    """Kiểm tra các tối ưu hóa đã được áp dụng trong websockets_stream.py"""
    
    print("=" * 60)
    print("KIỂM TRA TỐI ƯU HÓA ĐÃ ÁP DỤNG")
    print("=" * 60)
    
    try:
        with open('websockets_stream.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        optimizations_found = []
        
        # Kiểm tra các tối ưu hóa đã thực hiện
        checks = [
            ("MAX_WORKERS = 4", "Tăng worker từ 2 lên 4"),
            ("SKIP_FRAME_RATIO = 3", "Tăng skip frame ratio từ 2 lên 3"),
            ("FACE_CACHE_SIZE = 100", "Tăng cache size từ 50 lên 100"),
            ("max_comparisons = min\\(20", "Giới hạn so sánh khuôn mặt (20)"),
            ("if frame.shape\\[0\\] > 480 or frame.shape\\[1\\] > 640:", "Resize frame xuống 640x480"),
            ("ENABLE_FRAME_SKIPPING = True", "Bật frame skipping"),
            ("USE_OPTIMIZED_DETECTOR = True", "Sử dụng detector tối ưu"),
        ]
        
        for pattern, description in checks:
            if re.search(pattern, content):
                optimizations_found.append(f"✓ {description}")
            else:
                optimizations_found.append(f"✗ {description} (CHƯA ÁP DỤNG)")
        
        # Kiểm tra syntax
        try:
            ast.parse(content)
            optimizations_found.append("✓ Syntax hợp lệ (không có lỗi)")
        except SyntaxError as e:
            optimizations_found.append(f"✗ Lỗi syntax: {e}")
        
        # Hiển thị kết quả
        print("\nKẾT QUẢ KIỂM TRA:")
        for item in optimizations_found:
            print(f"  {item}")
        
        # Tính tỷ lệ thành công
        total = len(optimizations_found)
        successful = sum(1 for item in optimizations_found if item.startswith("✓"))
        success_rate = (successful / total) * 100
        
        print(f"\nTỶ LỆ THÀNH CÔNG: {success_rate:.1f}% ({successful}/{total})")
        
        if success_rate >= 80:
            print("\n✅ TỐI ƯU HÓA THÀNH CÔNG!")
            print("Hệ thống đã được tối ưu hóa với hầu hết các cải thiện.")
        else:
            print("\n⚠️ CẦN KIỂM TRA LẠI")
            print("Một số tối ưu hóa chưa được áp dụng đầy đủ.")
            
    except Exception as e:
        print(f"Lỗi khi kiểm tra: {e}")
    
    print("\n" + "=" * 60)
    print("KIỂM TRA HOÀN TẤT")
    print("=" * 60)

def check_arduino_optimizations():
    """Kiểm tra tối ưu hóa trong file Arduino"""
    print("\nKIỂM TRA TỐI ƯU HÓA ARDUINO:")
    
    try:
        with open('../arduino/esp32cam_ws_stream/esp32cam_ws_stream.ino', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ("TARGET_FPS 8", "Giảm FPS từ 10 xuống 8"),
            ("MAX_FRAME_SIZE 20000", "Giảm kích thước frame từ 30KB xuống 20KB"),
            ("SEND_TIMEOUT_MS 3000", "Giảm timeout từ 5s xuống 3s"),
            ("DYNAMIC_QUALITY", "Thêm chất lượng động"),
        ]
        
        for pattern, description in checks:
            if re.search(pattern, content):
                print(f"  ✓ {description}")
            else:
                print(f"  ✗ {description}")
                
    except FileNotFoundError:
        print("  ✗ Không tìm thấy file Arduino")
    except Exception as e:
        print(f"  ✗ Lỗi: {e}")

if __name__ == "__main__":
    check_optimizations()
    check_arduino_optimizations()