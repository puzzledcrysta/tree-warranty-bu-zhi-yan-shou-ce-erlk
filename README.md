# 补植验收册

园林养护验收员可用本地工作台处理街段验收单，复查单株验收明细并与独立清单逐笔核对。

死亡与补植按时序复盘，只有通过重置后的完整养护期及有效巡检才可结算，重复观察不重复计价。

## 启动

```sh
docker compose up --build
```

打开 http://127.0.0.1:18314 并运行随附样例。可以在「导入来源与外部账」上传自己的 CSV，也可以编辑表单中的样例。数据保存于 Compose 卷 `ledger`。使用 `APP_PORT` 可覆盖宿主端口。

## 工作步骤

1. 检查「巡检底单」与「物候字段」，定位导入坏行与字段归一结果。
2. 在「异常巡检」区分冲突、业务拒绝、重传与旧版本。
3. 打开「保活核款」并点击任意记录的「查看依据」。
4. 在「养护台账」检查金额或用量差异。通过「验收批次」复算原文件，通过「签收底稿」提交意见并下载证据。

接口定义见 `/openapi.json`。字段、允许区间及算例见 [数据字典](docs/DATA-DICTIONARY.md)，模块和回归测试见 [测试登记](docs/DEPTH.md)。

## 验证

```sh
docker compose config --quiet
docker compose exec -T app pytest -q
```

`sample_data/shift.csv` 是班次数据，`sample_data/external.csv` 是独立账样例。`cases.csv` 固定业务反例，`legacy.csv` 和 `truncated.csv` 用于验证历史格式与断行。
