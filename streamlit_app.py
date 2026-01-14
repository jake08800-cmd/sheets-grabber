import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import io
from datetime import datetime, timedelta
import json
import pandas as pd

# ================ 美化设置 ================
st.set_page_config(
    page_title="项目数据抓取工具",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS 美化
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        height: 3em;
        width: 100%;
        border-radius: 10px;
        font-size: 20px;
        font-weight: bold;
    }
    .stDownloadButton>button {
        background-color: #00d4aa;
        color: white;
        font-weight: bold;
    }
    .project-tag {
        padding: 5px 10px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        display: inline-block;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ================ 主界面 ================
st.title("📊 项目数据每日抓取工具")
st.markdown("**专业 · 简洁 · 高效** — 你的专属数据助手")

# ================ 侧边栏项目展示 + 多选 ================
with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)
    st.header("🌟 当前支持项目")

    all_projects = [
        "jeetup项目", "lakhup项目", "kanzplay项目",
        "falcowin项目", "snakerwin项目"
    ]
    colors = ["#ff6b6b", "#4ecdc4", "#45b7d1", "#96ceb4", "#ffeaa7"]

    for p, c in zip(all_projects, colors):
        st.markdown(f"<span class='project-tag' style='background-color:{c}; color:black'>{p}</span>", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🛠 抓取设置")

    selected_projects = st.multiselect(
        "选择要抓取的项目",
        options=all_projects,
        default=all_projects,
        help="不选任何项目将无法抓取"
    )

    st.caption(f"今天是 {datetime.today().strftime('%Y-%m-%d')}")

# 上传密钥
uploaded_file = st.file_uploader("🔑 上传 service_account.json 密钥文件（只需一次）", type=["json"])

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        file_str = file_bytes.decode("utf-8")
        service_account_info = json.loads(file_str)
        creds = Credentials.from_service_account_info(
            service_account_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        client = gspread.authorize(creds)
        st.success("✅ 密钥认证成功！已连接 Google Sheets")
    except Exception as e:
        st.error(f"❌ 密钥认证失败：{str(e)}")
        st.stop()

    # 多选日历
    st.markdown("### 📅 选择要抓取的日期（支持多选）")
    date_options = [(datetime.today() - timedelta(days=i)).date() for i in range(30)]
    date_options.reverse()
    default_date = datetime.today().date()
    selected_dates = st.multiselect(
        "点选日期（按住 Command 可多选，默认今天）",
        options=date_options,
        default=[default_date],
        format_func=lambda d: d.strftime("%Y-%m-%d"),
        help="可选择多个日期批量抓取"
    )
    if not selected_dates:
        st.warning("请至少选择一个日期")
        st.stop()
    目标日期列表 = [d.strftime("%Y-%m-%d") for d in selected_dates]
    st.info(f"**即将抓取：** {', '.join(目标日期列表)}")

    # 项目配置（5个项目）
    所有表格配置 = [
        {"id": "1UeYJ9e2almMVjO_X0Ts6oE7CmCoNN5IPO82cMMugLBw", "name": "jeetup项目", "sheets": ["ADC", "UD"], "date_col": 1, "result_cols": [12]},
        {"id": "1F_cu4GpofGbT0DGqNzO6vTYOUKTreGTRQzIQgnhs6is", "name": "lakhup项目", "sheets": ["ADC"], "date_col": 1, "result_cols": [4]},
        {"id": "1LTnKqi_h_fcalboeB75IxVTGjJsh6HtO7_YOYH6oHic", "name": "kanzplay项目", "sheets": ["YSS", "FS", "UD"], "date_col": 1, "result_cols": [4]},
        {"id": "1tSrNji1nheomDN_jjHZpFVJwzY2-DGQ_N-jAqbS95yg", "name": "falcowin项目", "sheets": ["ADC", "YSS", "AdRachel", "FS", "Pizzads", "UD"], "date_col": 1, "result_cols": [3]},
        {"id": "1laHyK6yB_mmc1ZyC79VCD3WOrkRylDXtzuGJJ9HjLhQ", "name": "snakerwin项目", "sheets": ["ADC", "YOJOY", "YSS", "Pizzads", "AdRachel", "UD", "FS"], "date_col": 1, "result_cols": [4]}
    ]

    # 只保留用户选择的项目配置
    表格配置列表 = [cfg for cfg in 所有表格配置 if cfg["name"] in selected_projects]

    if not 表格配置列表:
        st.warning("请至少选择一个项目")
        st.stop()

    if st.button("🚀 开始抓取数据", type="primary"):
        with st.spinner("正在从 Google Sheets 抓取数据，请稍等..."):
            所有结果 = []
            for 配置 in 表格配置列表:
                try:
                    spreadsheet = client.open_by_key(配置["id"])
                    for sheet_name in 配置["sheets"]:
                        try:
                            sheet = spreadsheet.worksheet(sheet_name)
                            data = sheet.get_all_values()
                            if len(data) > 1:
                                for row in data[1:]:
                                    if len(row) >= 配置["date_col"] and row[配置["date_col"] - 1].strip() in 目标日期列表:
                                        值 = [row[i - 1].strip() if i <= len(row) else "" for i in 配置["result_cols"]]
                                        值.extend([配置["name"], sheet_name, row[配置["date_col"] - 1].strip()])
                                        所有结果.append(值)
                        except Exception:
                            continue
                except Exception as e:
                    st.error(f"无法打开 {配置['name']}：{e}")

            if 所有结果:
                max_cols = max(len(r) - 3 for r in 所有结果)
                表头 = ["日期", "来源项目", "来源Sheet"] + [f"数据列{i}" for i in range(1, max_cols + 1)]
                新结果 = []
                for r in 所有结果:
                    数据 = r[:-3]
                    新行 = [r[-1], r[-3], r[-2]] + 数据 + [""] * (max_cols - len(数据))
                    新结果.append(新行)

                st.success(f"🎉 抓取完成！共找到 **{len(所有结果)}** 条数据")

                st.dataframe(
                    新结果,
                    use_container_width=True,
                    hide_index=True,
                    column_config={0: st.column_config.DateColumn("日期")}
                )

                output = io.StringIO()
                output.write("\t".join(表头) + "\n")
                for row in 新结果:
                    output.write("\t".join(map(str, row)) + "\n")
                st.download_button(
                    "📥 下载抓取结果（TXT）",
                    data=output.getvalue(),
                    file_name=f"项目数据_{'_'.join(目标日期列表)}.txt",
                    mime="text/plain"
                )

                # ──────────────── 对比汇总表（日期 + 渠道） ────────────────
                st.markdown("---")
                st.subheader("📊 与汇总表对比结果（日期 + 渠道）")

                try:
                    # 汇总表ID（替换成你的）
                    汇总表ID = "1NW-j8d3HhAHxOZxX5EhQfhcnWyQBwpZ1Yqt-3A6tpd4"

                    # 项目 → 汇总 sheet 映射
                    项目_汇总_sheet映射 = {
                        "jeetup项目": "jeetup",
                        "lakhup项目": "lakhup",
                        "kanzplay项目": "kanz",
                        "falcowin项目": "falcowin",
                        "snakerwin项目": "Saherwin（AUE)"
                    }

                    汇总_date_col = 1
                    汇总_channel_col = 2
                    汇总_value_col = 3

                    汇总_spreadsheet = client.open_by_key(汇总表ID)
                    对比结果 = []

                    for _, 抓取行 in pd.DataFrame(新结果, columns=表头).iterrows():
                        日期 = 抓取行['日期']
                        项目 = 抓取行['来源项目']
                        渠道 = 抓取行['来源Sheet']

                        汇总_sheet_name = 项目_汇总_sheet映射.get(项目)
                        if not 汇总_sheet_name:
                            对比结果.append({
                                "日期": 日期,
                                "项目": 项目,
                                "渠道": 渠道,
                                "抓取值": float(抓取行.get('数据列1', 0)),
                                "汇总值": "未配置",
                                "差值": "N/A",
                                "状态": "未配置"
                            })
                            continue

                        try:
                            汇总_sheet = 汇总_spreadsheet.worksheet(汇总_sheet_name)
                            汇总_data = 汇总_sheet.get_all_values()

                            if len(汇总_data) <= 1:
                                对比结果.append({
                                    "日期": 日期,
                                    "项目": 项目,
                                    "渠道": 渠道,
                                    "抓取值": float(抓取行.get('数据列1', 0)),
                                    "汇总值": "空表",
                                    "差值": "N/A",
                                    "状态": "空表"
                                })
                                continue

                            汇总_df = pd.DataFrame(汇总_data[1:], columns=汇总_data[0])
                            汇总_df['日期'] = 汇总_df.iloc[:, 汇总_date_col-1].astype(str).str.strip()
                            汇总_df['渠道'] = 汇总_df.iloc[:, 汇总_channel_col-1].astype(str).str.strip()

                            匹配行 = 汇总_df[(汇总_df['日期'] == 日期) & (汇总_df['渠道'] == 渠道)]

                            if not 匹配行.empty:
                                汇总值 = float(匹配行.iloc[0, 汇总_value_col-1]) if pd.notna(匹配行.iloc[0, 汇总_value_col-1]) else 0
                                抓取值 = float(抓取行.get('数据列1', 0))

                                差值 = 抓取值 - 汇总值
                                对比结果.append({
                                    "日期": 日期,
                                    "项目": 项目,
                                    "渠道": 渠道,
                                    "抓取值": 抓取值,
                                    "汇总值": 汇总值,
                                    "差值": 差值,
                                    "状态": "一致" if abs(差值) < 0.01 else "差异"
                                })
                            else:
                                对比结果.append({
                                    "日期": 日期,
                                    "项目": 项目,
                                    "渠道": 渠道,
                                    "抓取值": float(抓取行.get('数据列1', 0)),
                                    "汇总值": "未找到",
                                    "差值": "N/A",
                                    "状态": "缺失"
                                })

                        except gspread.WorksheetNotFound:
                            对比结果.append({
                                "日期": 日期,
                                "项目": 项目,
                                "渠道": 渠道,
                                "抓取值": float(抓取行.get('数据列1', 0)),
                                "汇总值": "Sheet不存在",
                                "差值": "N/A",
                                "状态": "Sheet缺失"
                            })
                        except Exception as e:
                            st.error(f"对比 {项目} - {渠道} 时出错：{e}")

                    if 对比结果:
                        对比_df = pd.DataFrame(对比结果)
                        st.dataframe(对比_df.style.applymap(
                            lambda x: 'background-color: #ffebee' if x in ["差异", "缺失", "未配置", "空表", "Sheet缺失"] else '',
                            subset=['状态']
                        ))

                        col1, col2, col3 = st.columns(3)
                        col1.metric("异常行数", len(对比_df[对比_df['状态'] != "一致"]))
                        col2.metric("总差值", f"{对比_df['差值'].sum():.2f}")
                        col3.metric("一致率", f"{(len(对比_df[对比_df['状态'] == '一致']) / len(对比_df)) * 100:.1f}%")

                        output对比 = io.StringIO()
                        output对比.write("\t".join(对比_df.columns) + "\n")
                        for _, row in 对比_df.iterrows():
                            output对比.write("\t".join(map(str, row)) + "\n")
                        st.download_button(
                            "📥 下载对比结果（TXT）",
                            data=output对比.getvalue(),
                            file_name=f"渠道对比_{'_'.join(目标日期列表)}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.info("没有可对比的数据")

            except Exception as e:
                st.error(f"读取汇总表失败：{e}")

else:
    st.info("👆 请先上传 service_account.json 密钥文件")
    st.markdown("### 使用步骤：\n1. 上传密钥文件\n2. 在左侧选择项目和日期\n3. 点击开始抓取")

st.markdown("---")
st.caption("你的专属数据抓取工具 • 永久免费 • 随时随地可用")
