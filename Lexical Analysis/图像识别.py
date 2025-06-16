import cv2
import pytesseract
import argparse
import os
import subprocess

# 在Windows上，可能需要设置Tesseract的路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
    """预处理图像以提高OCR识别率"""
    # 读取图像
    image = cv2.imread(image_path)
    if image is None:
        print(f"无法读取图像: {image_path}")
        return None
    
    # 转换为灰度图
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # 应用自适应阈值处理
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                  cv2.THRESH_BINARY, 11, 2)
    
    # 降噪
    denoised = cv2.medianBlur(binary, 3)
    
    return denoised

def recognize_text(image):
    """使用Tesseract OCR识别图像中的文本"""
    # 针对代码识别优化的配置
    custom_config = r'--oem 3 --psm 6 -l eng -c preserve_interword_spaces=1'
    
    # 执行OCR识别
    text = pytesseract.image_to_string(image, config=custom_config)
    return text

def save_to_file(text, output_path):
    """将识别结果保存到文件"""
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f"识别结果已保存到: {output_path}")

def run_lexer(recognized_code_path, lexer_path):
    """运行C++词法分析器处理识别出的代码"""
    try:
        # 执行词法分析器程序
        result = subprocess.run([lexer_path, recognized_code_path], 
                               capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"词法分析器执行错误: {e}")
        print(f"错误信息: {e.stderr}")
        return None
    except Exception as e:
        print(f"执行词法分析器时出错: {e}")
        return None

def main():
    # 设置固定的参数
    image_path = r"D:\test\img\2.png"
    output_dir = r"D:\test\out"
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置输出文件路径
    output_file = os.path.join(output_dir, "recognized_code.txt")
    
    # 处理图像
    print(f"正在处理图片: {image_path}...")
    processed_image = preprocess_image(image_path)
    if processed_image is None:
        return
    
    # 保存处理后的图像（调试用）
    debug_image_path = os.path.join(output_dir, "processed_" + os.path.basename(image_path))
    cv2.imwrite(debug_image_path, processed_image)
    print(f"预处理后的图像已保存到: {debug_image_path}")
    
    # OCR识别
    print("正在进行OCR识别...")
    recognized_text = recognize_text(processed_image)
    
    # 显示识别结果
    print("\n--- 识别结果 ---")
    print(recognized_text)
    print("----------------\n")
    
    # 保存到文件
    save_to_file(recognized_text, output_file)
    
    # 词法分析器部分保留，但默认不执行
    # 如果需要执行词法分析，请提供词法分析器路径作为参数
    # lexer_path = r"path_to_your_lexer.exe"
    # if lexer_path and os.path.exists(lexer_path):
    #     print("\n正在执行词法分析...")
    #     lexer_output = run_lexer(output_file, lexer_path)
    #     if lexer_output:
    #         print("\n--- 词法分析结果 ---")
    #         print(lexer_output)
    #         print("--------------------")

if __name__ == "__main__":
    main()
