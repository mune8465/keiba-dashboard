import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# 1. ページ設定
st.set_page_config(page_title="競馬分析ダッシュボード", layout="wide")

# ==========================================
# ★ここを表示したい日付に書き換えてください
DATE_VAL = "20260110" 
# ==========================================

# 場所マスター
PLACE_MASTER = {
    1: "札幌", 2: "函館", 3: "福島", 4: "新潟", 5: "東京",
    6: "中山", 7: "中京", 8: "京都", 9: "阪神", 10: "小倉"
}

# --- 色設定の関数 ---

# 判定(SS, S, A...)の色
def color_rank(val):
    # SS系統
    if val == 'SS':  return 'background-color: #ff69b4; color: white; font-weight: bold'
    if val == 'SS-': return 'background-color: #ff69b4; color: white'
    
    # S系統
    if val == 'S':   return 'background-color: #ff4500; color: white; font-weight: bold'
    if val == 'S-':  return 'background-color: #ff4500; color: white'
    
    # A系統
    if val == 'A':   return 'background-color: #ffa500; color: black; font-weight: bold'
    if val == 'A-':  return 'background-color: #ffa500; color: black'
    
    # B系統
    if val == 'B':   return 'background-color: #98fb98; color: black; font-weight: bold'
    if val == 'B-':  return 'background-color: #98fb98; color: black'
    
    # C系統 (追加)
    if val == 'C':   return 'background-color: #f0f8ff; color: black; font-weight: bold' # 薄い緑
    if val == 'C-':  return 'background-color: #f0f8ff; color: black'
    
    # D系統
    if val == 'D':   return 'background-color: #CCCCCC; color: black; font-weight: bold'
    if val == 'D-':  return 'background-color: #CCCCCC; color: black'
    
    # E系統
    if val == 'E':   return 'background-color: #AAAAAA; color: white; font-weight: bold'
    
    return ''

# 順位の色（1位: 黄, 2位: 水色, 3位: 黄緑, その他: 薄グレー）
def color_order(val):
    if val == 1: return 'background-color: #FFFF00; color: black; font-weight: bold' # 黄
    if val == 2: return 'background-color: #e0ffff; color: black; font-weight: bold' # 水色
    if val == 3: return 'background-color: #f8f8ff; color: black; font-weight: bold' # 黄緑
    if val == 4: return 'background-color: #f5f5dc; color: black; font-weight: bold' # 黄緑
    if val == 5: return 'background-color: #faf0e6; color: black; font-weight: bold' # 黄緑
    if val != "" and val != "-": return 'background-color: #F0F0F0; color: black' # 薄グレー
    return ''

# MS指数の色分け
def color_ms_index(val):
    try:
        v = float(val) if val != "-" else 0
    except: return ''
    if v >= 30.0: return 'background-color: #FF0000; color: white'
    if v >= 25.0: return 'background-color: #FF4500; color: white'
    if v >= 20.0: return 'background-color: #FF8C00; color: black'
    if v >= 15.0: return 'background-color: #FFD700; color: black'
    if v >= 10.0: return 'background-color: #FFFACD; color: black'
    return ''

# MSPF指数の色分け
def color_mspf_expect(val):
    try:
        v = float(val) if val != "-" else 0
    except: return ''
    if v >= 100.0: return 'background-color: #FF69B4; color: white' # ピンク系
    if v >= 98.0:  return 'background-color: #f4a460; color: black'
    if v >= 95.0:  return 'background-color: #f5deb3; color: black'
    return ''

# MST指数の色分け
def color_mst_index(val):
    try:
        v = float(val) if val != "-" else 0
    except: return ''
    if v >= 15.0: return 'background-color: #FFE4B5; color: black' # 薄オレンジ
    if v >= 10.0: return 'background-color: #FFFACD; color: black' # 薄黄色
    return ''

# ポイント定義
POINT_MAP = {'SS': 15, 'S': 12, 'A': 9, 'B': 7, 'C': 5, 'D': 3, 'E': 1}

# --- 判定ロジック ---

# 合計点からランク文字を出す
def get_al_rank(total_pt):
    if total_pt >= 28: return 'SS'
    if total_pt >= 27: return 'SS-'
    if total_pt >= 24: return 'S'
    if total_pt >= 21: return 'S-'
    if total_pt >= 18: return 'A'
    if total_pt >= 16: return 'A-'
    if total_pt >= 14: return 'B'
    if total_pt >= 12: return 'B-'
    if total_pt >= 10: return 'C'
    if total_pt >= 8:  return 'C-'
    if total_pt >= 6:  return 'D'
    if total_pt >= 4:  return 'D-'
    if total_pt >= 2:  return 'E'
    return ""

# MSとMSPFを合算して判定を出す（共通処理）
def get_combined_rank(ms_val, mspf_val, is_special=False):
    def get_pt(val):
        s_val = str(val).strip() if pd.notnull(val) else ""
        return POINT_MAP.get(s_val, 5) # 文字があればその点、なければC(5点)

    total = get_pt(ms_val) + get_pt(mspf_val)
    rank = get_al_rank(total)
    
    # CD, GR列のみ、C判定（10点）なら空欄にする
    if is_special and rank == 'C':
        return ""
    return rank


# --- データ読込 ---
@st.cache_data
def load_and_merge_data(date):
    base_dir = "data/output/"
    try:
        df_mspf = pd.read_csv(os.path.join(base_dir, f"MSPF_expect_results_{date}.csv"))
        df_ms = pd.read_csv(os.path.join(base_dir, f"MS_index_results_{date}.csv"))
        df_mst = pd.read_csv(os.path.join(base_dir, f"MST_index_results_{date}.csv"))
        
        # MSの判定列を特定 (総合判定:8, コース:12, レベル:15, 不利:18, 条件:21, 重賞:23, 血統:25)
        ms_cols = {
            df_ms.columns[8]: '総合判定_MS',
            df_ms.columns[12]: 'CS_MS', df_ms.columns[15]: 'LV_MS',
            df_ms.columns[18]: 'DA_MS', df_ms.columns[21]: 'CD_MS',
            df_ms.columns[23]: 'GR_MS', df_ms.columns[25]: 'BL_MS',
            'MS_index': 'MS_index_MS'
        }
        df_ms_sub = df_ms[['場所', 'レース', '馬番'] + list(ms_cols.keys())].rename(columns=ms_cols)

        df = df_mspf.merge(df_ms_sub, on=['場所', 'レース', '馬番'], how='left')
        df = df.merge(df_mst[['場所', 'レース', '馬番', 'MS_index']], on=['場所', 'レース', '馬番'], how='left')
        df = df.rename(columns={'MS_index': 'MST_index'})
        return df
    except Exception as e:
        st.error(f"データロードエラー: {e}")
        return None


# --- メイン処理 ---
try:
    dt = datetime.strptime(DATE_VAL, '%Y%m%d')
    DATE_STR = dt.strftime('%Y年%m月%d日')
except:
    DATE_STR = DATE_VAL

# タイトルと日付の表示
st.title("🏇 競馬指数ダッシュボード")
st.markdown(f"### 📅 {DATE_STR}")
st.divider()

# データロード
df_raw = load_and_merge_data(DATE_VAL)


if df_raw is not None:
    df_raw['場所名'] = df_raw['場所'].map(PLACE_MASTER).fillna(df_raw['場所'])
    all_places = sorted(df_raw['場所名'].unique())
    
    selected_place = st.pills("場所：", options=all_places, selection_mode="single", default=all_places[0])
    
    if selected_place:
        race_codes = sorted(df_raw[df_raw['場所名'] == selected_place]['レース'].unique(), key=lambda x: int(x.split('_')[1]))
        race_display_names = [f"{c.split('_')[1]}R" for c in race_codes]
        race_map = dict(zip(race_display_names, race_codes))
        selected_race_name = st.pills("R：", options=race_display_names, selection_mode="single", default=race_display_names[0])
        
        if selected_race_name:
            current_race_code = race_map[selected_race_name]
            st.subheader(f"🚩 {selected_place} {selected_race_name}")
            df_race = df_raw[(df_raw['場所名'] == selected_place) & (df_raw['レース'] == current_race_code)].copy()

            # 1. 順位計算
            for col, new_col in [('MS_index_MS', 'MS順'), ('MSPF_expect', 'MSPF順'), ('MST_index', 'MST順')]:
                if col in df_race.columns:
                    df_race[new_col] = df_race[col].rank(ascending=False, method='min').fillna(99).astype(int)

            # 2. 全列合算判定 (MS + MSPF)
            df_race['AL'] = df_race.apply(lambda r: get_combined_rank(r.get('総合判定_MS'), r.get('総合判定')), axis=1)
            df_race['CS'] = df_race.apply(lambda r: get_combined_rank(r.get('CS_MS'), r.get('コース(判定)')), axis=1)
            df_race['LV'] = df_race.apply(lambda r: get_combined_rank(r.get('LV_MS'), r.get('レベル(判定)')), axis=1)
            df_race['DA'] = df_race.apply(lambda r: get_combined_rank(r.get('DA_MS'), r.get('不利(複合判定)')), axis=1)
            df_race['CD'] = df_race.apply(lambda r: get_combined_rank(r.get('CD_MS'), r.get('条件(複合判定)'), True), axis=1)
            df_race['GR'] = df_race.apply(lambda r: get_combined_rank(r.get('GR_MS'), r.get('重賞(判定)'), True), axis=1)
            df_race['BL'] = df_race.apply(lambda r: get_combined_rank(r.get('BL_MS'), r.get('血統(判定)')), axis=1)

            # 3. 表示整形
            display_cols_map = {
                '馬番': '馬番', '馬名': '馬名', 'MS_index_MS': 'MS', 'MS順': ' ', 
                'MSPF_expect': 'MSPF', 'MSPF順': '  ', 'MST_index': 'MST', 'MST順': '   ',
                'AL': '総合', 'CS': 'CS', 'LV': 'LV', 'DA': 'DA', 'CD': 'CD', 'GR': 'GR', 'BL': 'BL'
            }
            # --- 修正：df_raceに存在する列だけを抽出するようにガードを入れる ---
            available_cols = [c for c in display_cols_map.keys() if c in df_race.columns]
            df_display = df_race[available_cols].rename(columns=display_cols_map)

            # 数値・判定クレンジング
            # --- 修正：None(評価不能)はハイフン、0.0以上の数値は表示 ---
            for c in ['MS', 'MSPF', 'MST']:
                # 一度数値型に変換（Noneや空文字はNaNになる）
                df_display[c] = pd.to_numeric(df_display[c], errors='coerce')
    
                # 判定：NaN(元None)や 1.0(対象外) はハイフン、それ以外（0.0含む）は表示
                df_display[c] = df_display[c].apply(
                    lambda x: f"{x:.1f}" if pd.notnull(x) and x != 1.0 else "-"
                )
            
            # スタイリング
            judge_cols = ['総合', 'CS', 'LV', 'DA', 'CD', 'GR', 'BL']
            rank_cols = [' ', '  ', '   ']
            styled_df = df_display.style\
                .map(color_rank, subset=judge_cols)\
                .map(color_order, subset=rank_cols)\
                .map(color_ms_index, subset=['MS'])\
                .map(color_mspf_expect, subset=['MSPF'])\
                .map(color_mst_index, subset=['MST'])\
                .set_properties(subset=['総合'], **{'border-left': '3px solid #555', 'font-weight': 'bold'})

            st.dataframe(styled_df, height=750, use_container_width=True, hide_index=True)
else:
    st.error("データが見つかりません。")