# TEVO-BW 改装为贴片机

这是一个将 TEVO Black Widow 3D 打印机改装为桌面 SMT 元件贴装机的工程项目。项目包含 FreeCAD 参数化模型、TBW-Feeder v3.0 送料器设计、装配说明、初步电气图和物料清单（BOM）。

> **项目状态：** 原型设计。CAD 检查和图纸不能证明实物设备安全或可用。运行前，请在实际机架上检查尺寸与配合、接线和保护、运动限位以及送料器性能。

## 主要文档

- [完整图文资料汇编（PDF，共 82 页）](../../../pnp/out/TEVO_BW_PnP_Dossier.pdf)
- [整机制造与装配指南](../../../pnp/BUILD_AND_ASSEMBLY.md)
- [当前 CAD 模型报告](../../../pnp/out/report.md)
- [电源架构与详细接线设计](../../../pnp/electronics/POWER_CONTROL_DESIGN.md)
- [TBW v3.0 送料器指南](../../../pnp/feeder/README.md)
- [整机物料清单](../../../pnp/out/bom.csv)

## 项目内容

- FreeCAD 参数化整机模型及生成脚本。
- 机架、龙门、贴装头、工作台和传动机构的机械设计。
- 八工位送料器，包含料带步进机构和盖带剥离组件。
- 初步 24 V 供电架构、控制电脑、相机和控制器设计。
- 装配图、渲染图、报告和初步 BOM。

## 生成 CAD 模型

安装 FreeCAD 1.1，然后在 PowerShell 中运行：

```powershell
cd pnp
.\pnp.ps1 build
.\pnp.ps1 check
.\pnp.ps1 all
```

模型检查仅覆盖 CAD 中定义的位置，不能验证真实打印机机架、电气安全或生产性能。目前建议使用 x86-64 电脑运行 OpenPnP；在 ARM64 应用和双相机功能完成验证前，Raspberry Pi 仅作为辅助/实验方案。

完整技术文档和 PDF 汇编目前为英文。本页面为项目简介和文档导航的中文翻译。

## 许可证与第三方文件

本仓库尚未指定统一许可证。部分目录含有许可证单独规定或许可信息不明确的第三方 CAD 模型和图片。重新发布或用于商业用途前，请核查这些文件的来源与许可。
