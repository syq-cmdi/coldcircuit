# ColdCircuit 可视化前端

ColdCircuit v0.3 新增 Streamlit + Plotly 前端，用于展示三维冷板结构、1500W TDP 参考设计、制造约束和按结构分组的设计规则。

## 启动方式

```bash
pip install -e ".[frontend]"
streamlit run frontend/streamlit_app.py
```

## 前端功能

- 1500W TDP 混合结构参考方案；
- 示例 JSON 加载；
- 自定义 JSON 上传；
- 指标卡片：TDP、最高温、压降、冷却液温升、流态；
- 3D 分层结构示意；
- 入口/出口与热源空间位置显示；
- 制造约束表；
- 按结构分组的设计规则卡片；
- 1500W TDP 设计指导。

## 结构分组

当前按以下结构族组织：

1. 蛇形流道 serpentine；
2. 并联微通道 parallel_microchannel；
3. 歧管微通道 manifold_microchannel；
4. 针翅 pin_fin；
5. 冲击射流 impingement；
6. 嵌入式冷板 embedded；
7. 混合结构 hybrid。

## 1500W TDP 设计建议

1500W 级冷板不建议默认采用单一路径蛇形流道。优先考虑：

- 歧管微通道；
- 嵌入式近热源流道；
- 局部铜扩展/铜嵌件；
- 局部针翅或冲击射流；
- 多入口/多出口流量均衡；
- 短并联流路降低压降。

该前端目前是工程概念级显示，后续可升级为真正的 CAD mesh/STEP 预览器。
