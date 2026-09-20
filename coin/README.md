# 古钱币版别识别（ORB 版别比对 Demo）

```bash
pip install opencv-python numpy
python coin_match.py --demo                    # 自检（合成图演示管线）
python coin_match.py ref.png tgt.png           # 真实图片比对
python coin_match.py ref.png tgt.png --roi 150,100,90,80  # ROI 局部比对
```

## 技术点

- **圆形轮廓提取**：Hough 圆检测 + 掩码只保留钱身
- **ORB 对齐**：`estimateAffinePartial2D` + RANSAC 抗离群，模糊/反光提示对齐失败
- **ROI 局部比对**：以 ROI 内 ORB 匹配点数量为主判定
- **SSIM 仅辅助**：ORB（结构）与 SSIM（亮度）解耦，避免锈色/包浆误判

> 真实版别判定阈值需用真钱币样本标定。合成图仅供流程演示。
