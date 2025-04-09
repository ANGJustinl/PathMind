"""
图表生成工具
"""
import logging
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

from matplotlib import font_manager as fm

matplotlib.use('Agg')  # 使用非交互式后端
# 设置中文字体
def find_font(font_name):
    for font in fm.findSystemFonts(fontpaths=None, fontext='ttf'):
        if font_name in Path(font).name:
            return font
    return None

font_path = find_font("楷体_GB2312")  # 自动查找字体
if font_path is None:
    raise FileNotFoundError("未找到 '楷体_GB2312' 字体，请检查系统是否安装该字体")
my_font = fm.FontProperties(fname=font_path)
plt.rcParams["font.family"] = my_font.get_name()

# 设置日志
logger = logging.getLogger(__name__)

def create_learning_style_chart(visual=70, auditory=50, kinesthetic=80, reading=40):
    """创建学习风格雷达图"""
    try:
        # 创建雷达图
        categories = ['视觉学习', '听觉学习', '动觉学习', '阅读学习']
        values = [visual, auditory, kinesthetic, reading]
        
        # 创建角度并闭合图形
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]  # 闭合图形
        values += values[:1]  # 闭合数据
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        
        # 填充雷达图
        ax.fill(angles, values, color='skyblue', alpha=0.7)
        ax.plot(angles, values, 'o-', color='blue', linewidth=2)
        
        # 设置标签
        ax.set_thetagrids(np.degrees(angles[:-1]), categories)
        ax.set_ylim(0, 100)
        ax.set_title('学习风格分析', fontsize=15, pad=20)
        ax.grid(True)
        
        for angle, value in zip(angles[:-1], values[:-1]):
            ax.text(angle, value + 10, f"{value}%", 
                    horizontalalignment='center', 
                    verticalalignment='center')
        
        return fig
    except Exception as e:
        logger.error(f"创建学习风格图表失败: {str(e)}")
        # 创建一个错误图表
        fig, ax = plt.subplots(figsize=(6, 6))
        ax.text(0.5, 0.5, f"图表生成失败: {str(e)}", ha='center', va='center', wrap=True)
        ax.axis('off')
        return fig
