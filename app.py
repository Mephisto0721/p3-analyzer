import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="排列三分析", page_icon="🎯", layout="wide")
st.title("体彩排列三历史分析")

SAMPLE_CSV = """issue,date,d1,d2,d3
2024001,2024-01-01,7,2,9
2024002,2024-01-02,1,1,5
2024003,2024-01-03,0,3,8
2024004,2024-01-04,4,4,4
2024005,2024-01-05,2,7,9
2024006,2024-01-06,3,3,0
2024007,2024-01-07,5,6,7
2024008,2024-01-08,9,0,1
2024009,2024-01-09,8,8,2
2024010,2024-01-10,6,5,4
"""

def load_data(file=None):
    if file is not None:
        df = pd.read_csv(file)
    else:
        try:
            df = pd.read_csv("data/p3.csv")
        except Exception:
            df = pd.read_csv(StringIO(SAMPLE_CSV))

    df.columns = [c.strip().lower() for c in df.columns]

    required = ["issue", "date", "d1", "d2", "d3"]
    for col in required:
        if col not in df.columns:
            st.error(f"CSV 缺少列：{col}")
            st.stop()

    for col in ["d1", "d2", "d3"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    df = df.dropna(subset=["d1", "d2", "d3"]).copy()
    df["issue"] = df["issue"].astype(str)
    df["date"] = df["date"].astype(str)
    df = df.sort_values("issue").reset_index(drop=True)

    df["和值"] = df[["d1", "d2", "d3"]].sum(axis=1)
    df["跨度"] = df[["d1", "d2", "d3"]].max(axis=1) - df[["d1", "d2", "d3"]].min(axis=1)

    def shape(row):
        nums = [row["d1"], row["d2"], row["d3"]]
        if len(set(nums)) == 1:
            return "豹子"
        elif len(set(nums)) == 2:
            return "组三"
        else:
            return "组六"

    df["形态"] = df.apply(shape, axis=1)
    df["号码"] = df[["d1", "d2", "d3"]].astype(str).agg("".join, axis=1)
    return df

def calc_omission(series, values=range(10)):
    last_seen = {v: None for v in values}
    for i, val in enumerate(series):
        if pd.notna(val):
            last_seen[int(val)] = i
    total = len(series)
    return {v: (total if pos is None else total - 1 - pos) for v, pos in last_seen.items()}

st.sidebar.header("数据")
uploaded = st.sidebar.file_uploader("上传排列三 CSV", type=["csv"])
df = load_data(uploaded)

st.sidebar.write(f"共 {len(df)} 期，最新：{df['issue'].iloc[-1]}")

latest = df.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("最新期号", latest["issue"])
c2.metric("开奖号码", latest["号码"])
c3.metric("和值", int(latest["和值"]))
c4.metric("跨度", int(latest["跨度"]))
st.caption(f"开奖日期：{latest['date']}，形态：{latest['形态']}")

st.header("号码频率")
freq_data = []
for pos, col in [("百位", "d1"), ("十位", "d2"), ("个位", "d3")]:
    counts = df[col].value_counts().reindex(range(10), fill_value=0)
    for num, cnt in counts.items():
        freq_data.append({"位置": pos, "数字": num, "次数": int(cnt)})

freq_df = pd.DataFrame(freq_data)
pivot = freq_df.pivot(index="数字", columns="位置", values="次数").fillna(0)
st.bar_chart(pivot)

st.header("当前遗漏")
omission_data = []
for pos, col in [("百位", "d1"), ("十位", "d2"), ("个位", "d3")]:
    om = calc_omission(df[col])
    for num, val in om.items():
        omission_data.append({"位置": pos, "数字": num, "当前遗漏": val})

om_df = pd.DataFrame(omission_data)
om_pivot = om_df.pivot(index="数字", columns="位置", values="当前遗漏").fillna(0)
st.dataframe(om_pivot, use_container_width=True)

st.header("和值 / 跨度 / 形态分布")
col1, col2 = st.columns(2)

with col1:
    st.subheader("和值分布")
    sum_counts = df["和值"].value_counts().sort_index()
    st.bar_chart(sum_counts)

with col2:
    st.subheader("跨度分布")
    span_counts = df["跨度"].value_counts().sort_index()
    st.bar_chart(span_counts)

st.subheader("形态分布")
shape_counts = df["形态"].value_counts()
st.bar_chart(shape_counts)

st.header("历史开奖")
st.dataframe(
    df[["issue", "date", "号码", "和值", "跨度", "形态"]].tail(100),
    use_container_width=True
)
# ==========================================
# 智能选号与预测模块（复式：27 / 64 / 125 注）
# ==========================================
st.markdown("---")
st.header("🎯 智能选号辅助 (仅供娱乐)")
st.caption("注意：彩票开奖是独立随机事件，以下号码仅由历史数据统计生成，不代表预测结果，请理性对待。")

import random
from itertools import product

for _k, _v in (
    ("history_records", []),
    ("last_batch", []),
    ("last_batch_info", {}),
):
    if _k not in st.session_state:
        st.session_state[_k] = _v


def pick_position_numbers(count, series, recent_df, col, strategy):
    """给某个位置挑 count 个候选号（0-9）。

    热号 = 近 30 期出现次数多；冷号 = 当前遗漏长。
    """
    freq = recent_df[col].value_counts()
    hot_order = [int(x) for x in freq.index]
    hot_order += [i for i in range(10) if i not in hot_order]

    om = calc_omission(series)
    cold_order = sorted(om, key=lambda k: (-om[k], k))

    if strategy == "追热号（近期高频）":
        picked = hot_order[:count]
    elif strategy == "守冷号（遗漏最长）":
        picked = cold_order[:count]
    elif strategy == "冷热结合（推荐）":
        picked = hot_order[: (count + 1) // 2]
        for x in cold_order:
            if len(picked) >= count:
                break
            if x not in picked:
                picked.append(x)
    else:
        picked = random.sample(range(10), count)

    # 补足兜底（理论上不会缺）
    for i in hot_order:
        if len(picked) >= count:
            break
        if i not in picked:
            picked.append(i)

    return sorted(int(x) for x in picked[:count])


# 1. 定义选号策略
strategy = st.selectbox(
    "选择选号策略：",
    ["冷热结合（推荐）", "追热号（近期高频）", "守冷号（遗漏最长）", "随机生成（纯机选）"]
)

# 2. 用户自定义过滤条件（可选）
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    sum_range = st.slider("和值范围", 0, 27, (10, 18))
with col_f2:
    span_range = st.slider("跨度范围", 0, 9, (3, 7))
with col_f3:
    exclude_shape = st.multiselect("排除形态", ["豹子", "组三", "组六"], default=[])

# 3. 复式规模：每个位置选 n 个号，展开 n×n×n 注
st.markdown("**复式规模**：每个位置选 n 个号，展开后是 n×n×n 注")
b1, b2, b3 = st.columns(3)
target_n = None
with b1:
    if st.button("27 注（3×3×3）", use_container_width=True):
        target_n = 3
with b2:
    if st.button("64 注（4×4×4）", use_container_width=True):
        target_n = 4
with b3:
    if st.button("125 注（5×5×5）", use_container_width=True):
        target_n = 5

if target_n:
    recent_df = df.tail(30)
    picked_nums = {
        "d1": pick_position_numbers(target_n, df["d1"], recent_df, "d1", strategy),
        "d2": pick_position_numbers(target_n, df["d2"], recent_df, "d2", strategy),
        "d3": pick_position_numbers(target_n, df["d3"], recent_df, "d3", strategy),
    }

    all_combos = list(
        product(picked_nums["d1"], picked_nums["d2"], picked_nums["d3"])
    )
    generated = []
    for n1, n2, n3 in all_combos:
        s_val = n1 + n2 + n3
        sp_val = max(n1, n2, n3) - min(n1, n2, n3)

        if len({n1, n2, n3}) == 1:
            shape_val = "豹子"
        elif len({n1, n2, n3}) == 2:
            shape_val = "组三"
        else:
            shape_val = "组六"

        if not (sum_range[0] <= s_val <= sum_range[1]):
            continue
        if not (span_range[0] <= sp_val <= span_range[1]):
            continue
        if shape_val in exclude_shape:
            continue

        generated.append({
            "号码": f"{n1}{n2}{n3}",
            "和值": s_val,
            "跨度": sp_val,
            "形态": shape_val,
            "策略": strategy,
        })

    st.session_state.last_batch = generated
    st.session_state.last_batch_info = {
        "n": target_n,
        "nums": picked_nums,
        "total": len(all_combos),
    }
    if generated:
        st.session_state.history_records.extend(generated)

# 4. 展示本批结果
_batch = st.session_state.get("last_batch") or []
_info = st.session_state.get("last_batch_info") or {}

if _batch and _info:
    _n = _info["n"]
    _total = _info["total"]
    _kept = len(_batch)
    _nums = _info["nums"]

    st.markdown(
        f"**本次 {_n}×{_n}×{_n}**　百位 {_nums['d1']} ｜ 十位 {_nums['d2']} ｜ 个位 {_nums['d3']}"
    )
    if _kept == _total:
        st.success(f"展开 {_total} 注，过滤后全部保留。")
    elif _kept:
        st.warning(
            f"展开 {_total} 注，按和值/跨度/形态过滤掉 {_total - _kept} 注，剩 {_kept} 注。"
        )
    else:
        st.error("全部被过滤掉了，放宽和值/跨度范围再试。")

    if _kept:
        st.dataframe(
            pd.DataFrame(_batch), use_container_width=True, hide_index=True
        )

        _numbers = " ".join(row["号码"] for row in _batch)
        st.markdown("**👇 本批号码（点右上角复制，只有号码）**")
        st.code(_numbers, language=None)

# 5. 展示历史生成记录
if st.session_state.history_records:
    st.markdown("---")
    st.subheader("📋 历史生成记录")

    hist_df = pd.DataFrame(st.session_state.history_records)

    tab1, tab2 = st.tabs(["当前历史列表", "下载/清空"])

    with tab1:
        st.dataframe(hist_df, use_container_width=True, hide_index=True)

    with tab2:
        col_a, col_b = st.columns(2)
        with col_a:
            csv_data = hist_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                label="📥 下载历史记录为 CSV",
                data=csv_data,
                file_name="p3_generated_history.csv",
                mime="text/csv",
            )
        with col_b:
            if st.button("🗑️ 清空历史记录"):
                st.session_state.history_records = []
                st.session_state.last_batch = []
                st.session_state.last_batch_info = {}
                st.rerun()

st.caption("⚠️ 本工具仅供个人学习与娱乐，所有数据来源于公开网络，不构成任何购彩建议，不保证预测准确，请理性购彩。")
